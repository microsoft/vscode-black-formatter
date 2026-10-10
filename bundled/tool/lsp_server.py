# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Implementation of tool support over LSP."""

from __future__ import annotations

import ast
import copy
import os
import pathlib
import re
import subprocess
import sys
import traceback
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse, urlunparse


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        else:
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
BUNDLE_DIR = pathlib.Path(__file__).parent.parent
# Always use bundled server files.
update_sys_path(os.fspath(BUNDLE_DIR / "tool"), "useBundled")
update_sys_path(
    os.fspath(BUNDLE_DIR / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)

# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error
import lsp_edit_utils as edit_utils
import lsp_io
import lsp_notebook as notebook
import lsp_utils as utils
from lsprotocol import types as lsp
from pygls import uris
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument
from vscode_common_python_lsp import (
    RunResult,
    ToolServer,
    ToolServerConfig,
    is_current_interpreter,
    match_line_endings,
    strip_trailing_newline,
    update_environ_path,
)

update_environ_path()

RUNNER = pathlib.Path(__file__).parent / "lsp_runner.py"

MAX_WORKERS = 5

LSP_SERVER = LanguageServer(
    name="black-server",
    version="v0.1.0",
    max_workers=MAX_WORKERS,
    notebook_document_sync=notebook.NOTEBOOK_SYNC_OPTIONS,
)


TOOL_MODULE = "black"
TOOL_DISPLAY = "Black Formatter"

# Default arguments always passed to black.
TOOL_ARGS = []

# Minimum version of black supported.
MIN_VERSION = "22.3.0"

BLACK_CONFIG = ToolServerConfig(
    tool_module=TOOL_MODULE,
    tool_display=TOOL_DISPLAY,
    tool_args=TOOL_ARGS,
    min_version=MIN_VERSION,
    runner_script=str(RUNNER),
)

tool_server = ToolServer(BLACK_CONFIG, server=LSP_SERVER)

WORKSPACE_SETTINGS = tool_server.workspace_settings
GLOBAL_SETTINGS = tool_server.global_settings

# Minimum version of black that supports the `--line-ranges` CLI option.
LINE_RANGES_MIN_VERSION = (23, 11, 0)

# Timeout in seconds for formatting operations to prevent indefinite blocking.
FORMATTING_TIMEOUT = 120

# Versions of black found by workspace
VERSION_LOOKUP: Dict[str, Tuple[int, int, int]] = {}


def _get_document_path(document: TextDocument) -> str:
    """Returns the filesystem path for a document.

    Examples:
        file:///path/to/file.py -> /path/to/file.py
        vscode-notebook-cell:... -> /path/to/file.py
    """

    if not document.uri.startswith("file:"):
        parsed = urlparse(document.uri)
        file_uri = urlunparse(("file", parsed.netloc, parsed.path, "", "", ""))
        if result := uris.to_fs_path(file_uri):
            return result
    return document.path


# **********************************************************
# Tool specific code goes below this.
# **********************************************************

# **********************************************************
# Formatting features start here
# **********************************************************


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(params: lsp.DocumentFormattingParams) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/formatting request."""

    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
    return _formatting_helper(document)


@LSP_SERVER.feature(
    lsp.TEXT_DOCUMENT_RANGE_FORMATTING,
    lsp.DocumentRangeFormattingOptions(ranges_support=True),
)
def range_formatting(
    params: lsp.DocumentRangeFormattingParams,
) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/rangeFormatting request."""
    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
    settings = tool_server.get_settings_by_document(document)
    version = VERSION_LOOKUP.get(settings["workspaceFS"])

    if version is not None and version >= LINE_RANGES_MIN_VERSION:
        return _formatting_helper(
            document,
            args=[
                "--line-ranges",
                f"{params.range.start.line + 1}-{params.range.end.line + 1}",
            ],
        )

    if version is not None:
        tool_server.log_warning(
            "Black version earlier than 23.11.0 does not support range formatting. Formatting entire document."
        )
    return _formatting_helper(document)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_RANGES_FORMATTING)
def ranges_formatting(
    params: lsp.DocumentRangesFormattingParams,
) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/rangesFormatting request."""
    document = LSP_SERVER.workspace.get_text_document(params.text_document.uri)
    settings = tool_server.get_settings_by_document(document)
    version = VERSION_LOOKUP.get(settings["workspaceFS"])

    if version is not None and version >= LINE_RANGES_MIN_VERSION:
        args = []
        for r in params.ranges:
            args += ["--line-ranges", f"{r.start.line + 1}-{r.end.line + 1}"]
        return _formatting_helper(document, args=args)

    if version is not None:
        tool_server.log_warning(
            "Black version earlier than 23.11.0 does not support range formatting. Formatting entire document."
        )
    return _formatting_helper(document)


def is_python(code: str, file_path: str) -> bool:
    """Ensures that the code provided is python."""
    try:
        ast.parse(code, file_path)
    except SyntaxError:
        tool_server.log_error(f"Syntax error in code: {traceback.format_exc()}")
        return False
    return True


def _formatting_helper(
    document: TextDocument, args: Sequence[str] = None
) -> list[lsp.TextEdit] | None:
    args = [] if args is None else args
    extra_args = list(args) + _get_args_by_file_extension(document)
    extra_args += ["--stdin-filename", _get_filename_for_black(document)]
    try:
        result = _run_tool_on_document(document, use_stdin=True, extra_args=extra_args)
    except (subprocess.TimeoutExpired, TimeoutError):
        tool_server.log_warning(
            f"Formatting timed out after {FORMATTING_TIMEOUT}s for {document.uri}"
        )
        return None
    if result and result.stdout:
        if LSP_SERVER.protocol.trace == lsp.TraceValue.Verbose:
            tool_server.log_to_output(
                f"{document.uri} :\r\n"
                + ("*" * 100)
                + "\r\n"
                + f"{result.stdout}\r\n"
                + ("*" * 100)
                + "\r\n"
            )

        new_source = match_line_endings(document.source, result.stdout)

        if document.uri.startswith("vscode-notebook-cell"):
            new_source = strip_trailing_newline(new_source)

        if new_source != document.source:
            edits = edit_utils.get_text_edits(
                document.source, new_source, lsp.PositionEncodingKind.Utf16
            )
            if edits:
                return edits
    return None


def _get_filename_for_black(document: TextDocument) -> str:
    """Gets or generates a file name to use with black when formatting."""
    doc_path = _get_document_path(document)
    if document.uri.startswith("vscode-notebook-cell") and doc_path.endswith(".ipynb"):
        return str(pathlib.Path(doc_path).with_suffix(".py"))
    return doc_path


def _get_args_by_file_extension(document: TextDocument) -> List[str]:
    """Returns arguments used by black based on file extensions."""
    if document.uri.startswith("vscode-notebook-cell"):
        return []

    p = _get_document_path(document).lower()
    if p.endswith(".py"):
        return []
    if p.endswith(".pyi"):
        return ["--pyi"]
    if p.endswith(".ipynb"):
        return ["--ipynb"]
    return []


# **********************************************************
# Formatting features ends here
# **********************************************************


# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    tool_server.apply_settings(params)
    settings = (params.initialization_options or {}).get("settings")
    tool_server.log_startup_info(settings)
    _update_workspace_settings_with_version_info(tool_server.workspace_settings)


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    tool_server.handle_exit()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    tool_server.handle_shutdown()


VERSION_RE = re.compile(r"\d+\.\d+(?:\.\d+)?\S*")


def _parse_tool_version(stdout: str) -> str:
    """Extract the tool version from the first line of `black --version` output.

    Returns the longest token on the first line that looks like a SemVer-ish
    version (digits, dots, optional pre-release / build suffix).  Raises
    ValueError when no candidate is found or the output is empty.
    """
    lines = stdout.splitlines(keepends=False)
    if not lines:
        raise ValueError("empty --version output")
    parts = [v for v in lines[0].split(" ") if VERSION_RE.fullmatch(v)]
    if not parts:
        raise ValueError(f"no version candidate in --version output: {lines[0]!r}")
    # If the first line contains multiple version-shaped tokens (e.g. black
    # with an embedded 'X.Y.Z' and '24.3.0'), pick the longest so a
    # pre-release suffix like '24.3.0rc1' wins over a stray short match.
    return max(parts, key=len)


def _update_workspace_settings_with_version_info(
    workspace_settings: dict[str, Any],
) -> None:
    for settings in workspace_settings.values():
        try:
            from packaging.version import parse as parse_version

            result = _run_tool(["--version"], copy.deepcopy(settings))
            code_workspace = settings["workspaceFS"]
            tool_server.log_to_output(
                f"Version info for formatter running for {code_workspace}:\r\n{result.stdout}"
            )

            if "The typed_ast package is required but not installed" in result.stdout:
                tool_server.log_to_output(
                    'Install black in your environment and set "black-formatter.importStrategy": "fromEnvironment"'
                )

            # This is text we get from running `black --version`
            # black, 22.3.0 (compiled: yes) <--- This is the version we want.
            try:
                actual_version = _parse_tool_version(result.stdout)
            except ValueError as ve:
                log_error(
                    f"Could not parse version of formatter running for "
                    f"{code_workspace}: {ve}\r\n"
                )
                continue

            version = parse_version(actual_version)
            min_version = parse_version(MIN_VERSION)
            VERSION_LOOKUP[code_workspace] = (
                version.major,
                version.minor,
                version.micro,
            )

            if version < min_version:
                tool_server.log_error(
                    f"Version of formatter running for {code_workspace} is NOT supported:\r\n"
                    f"SUPPORTED {TOOL_MODULE}>={min_version}\r\n"
                    f"FOUND {TOOL_MODULE}=={actual_version}\r\n"
                )
            else:
                tool_server.log_to_output(
                    f"SUPPORTED {TOOL_MODULE}>={min_version}\r\n"
                    f"FOUND {TOOL_MODULE}=={actual_version}\r\n"
                )

        except:  # pylint: disable=bare-except
            tool_server.log_to_output(
                f"Error while detecting black version:\r\n{traceback.format_exc()}"
            )


# *****************************************************
# Internal execution APIs.
# *****************************************************
def _run_tool_on_document(
    document: TextDocument,
    use_stdin: bool = False,
    extra_args: Sequence[str] = (),
) -> RunResult | None:
    """Runs tool on the given document.

    if use_stdin is true then contents of the document is passed to the
    tool via stdin.
    """
    doc_path = _get_document_path(document)
    if utils.is_stdlib_file(doc_path):
        tool_server.log_warning(f"Skipping standard library file: {doc_path}")
        return None

    if not is_python(document.source, doc_path):
        tool_server.log_warning(
            f"Skipping non python code or code with syntax errors: {doc_path}"
        )
        return None

    settings = copy.deepcopy(tool_server.get_settings_by_document(document))
    code_workspace = settings["workspaceFS"]
    cwd = tool_server.get_cwd(settings, document, document_path=doc_path)

    if settings["path"]:
        mode = "path"
        argv = list(settings["path"])
    elif settings["interpreter"] and not is_current_interpreter(
        settings["interpreter"][0]
    ):
        mode = "rpc"
        argv = [TOOL_MODULE]
    else:
        mode = "module"
        argv = [TOOL_MODULE]

    argv += TOOL_ARGS + settings["args"] + list(extra_args)

    if use_stdin:
        argv += ["-"]

    source = document.source
    if mode == "path" and use_stdin:
        source = source.replace("\r\n", "\n")

    return tool_server.execute_tool(
        argv=argv,
        mode=mode,
        settings=settings,
        use_stdin=use_stdin,
        cwd=cwd,
        workspace=code_workspace,
        source=source,
        env=(
            {"LS_IMPORT_STRATEGY": settings["importStrategy"]}
            if mode == "rpc"
            else None
        ),
        timeout=FORMATTING_TIMEOUT,
    )


def _run_tool(extra_args: Sequence[str], settings: Dict[str, Any]) -> RunResult:
    """Runs tool."""
    code_workspace = settings["workspaceFS"]
    cwd = tool_server.get_cwd(settings, None)

    if settings["path"]:
        mode = "path"
        argv = list(settings["path"])
    elif settings["interpreter"] and not is_current_interpreter(
        settings["interpreter"][0]
    ):
        mode = "rpc"
        argv = [TOOL_MODULE]
    else:
        mode = "module"
        argv = [TOOL_MODULE]

    argv += list(extra_args)

    try:
        result = tool_server.execute_tool(
            argv=argv,
            mode=mode,
            settings=settings,
            use_stdin=True,
            cwd=cwd,
            workspace=code_workspace,
            env=(
                {"LS_IMPORT_STRATEGY": settings["importStrategy"]}
                if mode == "rpc"
                else None
            ),
            timeout=FORMATTING_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, TimeoutError):
        if mode == "rpc":
            tool_server.log_warning(
                f"JSON-RPC execution timed out after {FORMATTING_TIMEOUT}s"
            )
        else:
            tool_server.log_warning(
                f"Tool execution timed out after {FORMATTING_TIMEOUT}s"
            )
        return RunResult("", f"Timed out after {FORMATTING_TIMEOUT}s")

    if LSP_SERVER.protocol.trace == lsp.TraceValue.Verbose:
        tool_server.log_to_output(f"\r\n{result.stdout}\r\n")

    return result


# *****************************************************
# Internal settings management APIs.
# Thin wrappers delegating to ToolServer for backward compatibility.
# *****************************************************
def _get_global_defaults():
    return tool_server.get_global_defaults()


# *****************************************************
# Internal execution APIs (wrapper).
# *****************************************************
def get_cwd(settings: Dict[str, Any], document: Optional[TextDocument]) -> str:
    """Returns the working directory for running the tool."""
    if document:
        return tool_server.get_cwd(
            settings, document, document_path=_get_document_path(document)
        )
    return tool_server.get_cwd(settings, document)


# *****************************************************
# Logging and notification.
# Thin wrappers delegating to ToolServer for backward compatibility.
# *****************************************************
def log_to_output(
    message: str, msg_type: lsp.MessageType = lsp.MessageType.Log
) -> None:
    """Logs messages to Output > Black Formatter channel only."""
    tool_server.log_to_output(message, msg_type)


def log_error(message: str) -> None:
    """Logs messages with notification on error."""
    tool_server.log_error(message)


def log_warning(message: str) -> None:
    """Logs messages with notification on warning."""
    tool_server.log_warning(message)


def log_always(message: str) -> None:
    """Logs messages with notification."""
    tool_server.log_always(message)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    args = lsp_io.parse_args()
    if args.pipe:
        with lsp_io.use_pipe(args.pipe) as (rpipe, wpipe):
            LSP_SERVER.start_io(rpipe, wpipe)
    else:
        # default is always the stdio option.
        LSP_SERVER.start_io()
