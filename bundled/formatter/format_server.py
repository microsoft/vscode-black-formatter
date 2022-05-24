# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Implementation of formatting support over LSP.
"""
import ast
import copy
import json
import os
import pathlib
import sys
import traceback
from typing import List, Sequence, Union

# Ensure that we can import LSP libraries, and other bundled formatter libraries
sys.path.append(str(pathlib.Path(__file__).parent.parent / "libs"))

import utils
from packaging.version import parse
from pygls import lsp, protocol, server, uris, workspace
from pygls.lsp import types

FORMATTER = {
    "name": "Black",
    "module": "black",
    "args": [],
}
WORKSPACE_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "runner.py"

MAX_WORKERS = 5
LSP_SERVER = server.LanguageServer(max_workers=MAX_WORKERS)


def is_python(code: str) -> bool:
    """Ensures that the code provided is python."""
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def _get_args_by_file_extension(document: workspace.Document) -> List[str]:
    """Returns arguments used by black based on file extensions."""
    if document.uri.startswith("vscode-notebook-cell"):
        return []

    p = document.path.lower()
    if p.endswith(".py"):
        return []
    elif p.endswith(".pyi"):
        return ["--pyi"]
    elif p.endswith(".ipynb"):
        return ["--ipynb"]
    return []


def _filter_args(args: List[str]) -> List[str]:
    """
    Removes arguments that prevent black from formatting or can cause
    errors when parsing output.
    """
    return [
        a
        for a in args
        if a
        not in [
            "--diff",
            "--check",
            "--color",
            "--no-color",
            "-h",
            "--help",
            "--version",
        ]
    ]


def _get_line_endings(lines: List[str]) -> str:
    """Returns line endings used in the text."""
    try:
        if lines[0][-2:] == "\r\n":
            return "\r\n"
        return "\n"
    except Exception:
        return None


def _match_line_endings(document: workspace.Document, text: str) -> str:
    """Ensures that the edited text line endings matches the document line endings."""
    expected = _get_line_endings(document.source.splitlines(keepends=True))
    actual = _get_line_endings(text.splitlines(keepends=True))
    if actual == expected or actual is None or expected is None:
        return text
    return text.replace(actual, expected)


def _get_filename_for_black(document: workspace.Document) -> Union[str, None]:
    """Gets or generates a file name to use with black when formatting."""
    if document.uri.startswith("vscode-notebook-cell") and document.path.endswith(
        ".ipynb"
    ):
        # Treat the cell like a python file
        return document.path[:-6] + ".py"
    return document.path


def _log_version_info(path: Sequence[str]) -> None:
    try:
        settings = copy.deepcopy(WORKSPACE_SETTINGS)
        workspace = settings["workspaceFS"]
        module = FORMATTER["module"]
        if len(path) > 0:
            result = utils.run_path([*path, "--version"], False, workspace)
        else:
            result = utils.run_module(module, [module, "--version"], False, workspace)
        LSP_SERVER.show_message_log(
            f"Version info for Formatter running for {workspace}:\r\n{result.stdout}"
        )

        MIN_VERSION = "22.3.0"
        # This is to just get the version number:
        # > black --version
        # black, 22.3.0 (compiled: yes) <--- this is all we want
        first_line = result.stdout.splitlines(keepends=False)[0]
        actual_version = first_line.split(" ")[1]
        version = parse(actual_version)
        min_version = parse(MIN_VERSION)
        if version < min_version:
            LSP_SERVER.show_message_log(
                f"Version of formatter running for {workspace} is less than min supported version:\r\n"
                f"SUPPORTED {module}>={MIN_VERSION}\r\nFOUND {module}=={actual_version}\r\n"
            )
        else:
            LSP_SERVER.show_message_log(
                f"SUPPORTED {module}>={MIN_VERSION}\r\nFOUND {module}=={actual_version}\r\n"
            )
    except:
        pass


def _format(
    params: types.DocumentFormattingParams,
) -> Union[List[types.TextEdit], None]:
    """Runs formatter, processes the output, and returns text edits."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)

    if utils.is_stdlib_file(document.path) or not is_python(document.source):
        # Don't format standard library python files. Or, invalid python code
        # or non-python code in case of notebooks
        return None

    settings = copy.deepcopy(WORKSPACE_SETTINGS)

    module = FORMATTER["module"]
    cwd = settings["workspaceFS"]

    if len(settings["path"]) > 0:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif len(settings["interpreter"]) > 0 and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use that interpreter.
        argv = settings["interpreter"] + [str(RUNNER), module]
        use_path = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [FORMATTER["module"]]
        use_path = False

    argv += _filter_args(FORMATTER["args"] + settings["args"])
    argv += _get_args_by_file_extension(document)
    argv += ["--stdin-filename", _get_filename_for_black(document), "-"]

    LSP_SERVER.show_message_log(" ".join(argv))
    LSP_SERVER.show_message_log(f"CWD Formatter: {cwd}")

    # Force line endings to be `\n`, this makes the diff
    # easier to work with
    source = document.source.replace("\r\n", "\n")

    try:
        if use_path:
            result = utils.run_path(argv=argv, use_stdin=True, cwd=cwd, source=source)
        else:
            result = utils.run_module(
                module=module, argv=argv, use_stdin=True, cwd=cwd, source=source
            )
    except Exception:
        error_text = traceback.format_exc()
        LSP_SERVER.show_message_log(error_text, msg_type=types.MessageType.Error)
        LSP_SERVER.show_message(
            f"Formatting error, please see Output > Black Formatter for more info:\r\n{error_text}",
            msg_type=types.MessageType.Error,
        )
        return None

    if result.stderr:
        LSP_SERVER.show_message_log(result.stderr, msg_type=types.MessageType.Error)
        if result.stderr.find("Error:") >= 0 or result.stderr.find("error:") >= 0:
            LSP_SERVER.show_message(
                f"Formatting error, please see Output > Black Formatter for more info:\r\n{result.stderr}",
                msg_type=types.MessageType.Error,
            )
            return None

    new_source = _match_line_endings(document, result.stdout)

    # Skip last line ending in a notebook cell
    if document.uri.startswith("vscode-notebook-cell"):
        if new_source.endswith("\r\n"):
            new_source = new_source[:-2]
        elif new_source.endswith("\n"):
            new_source = new_source[:-1]

    if new_source == document.source or not result.stdout:
        return None

    return [
        types.TextEdit(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=len(document.lines), character=0),
            ),
            new_text=new_source,
        )
    ]


@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: types.InitializeParams):
    """LSP handler for initialize request."""
    global WORKSPACE_SETTINGS
    WORKSPACE_SETTINGS = params.initialization_options["settings"]
    workspace = uris.to_fs_path(WORKSPACE_SETTINGS["workspace"])
    WORKSPACE_SETTINGS["workspaceFS"] = workspace

    LSP_SERVER.show_message_log(f"CWD used for [{workspace}]: {os.getcwd()}\r\n")
    paths = "\r\n    ".join(sys.path)
    LSP_SERVER.show_message_log(
        f"sys.path used to run Formatter for [{workspace}]:\r\n    {paths}\r\n"
    )
    LSP_SERVER.show_message_log(
        f"Settings used to run Formatter for [{workspace}]:\r\n{json.dumps(WORKSPACE_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )

    if isinstance(LSP_SERVER.lsp, protocol.LanguageServerProtocol):
        if WORKSPACE_SETTINGS["trace"] == "debug":
            trace = lsp.Trace.Verbose
        elif WORKSPACE_SETTINGS["trace"] == "off":
            trace = lsp.Trace.Off
        else:
            trace = lsp.Trace.Messages
        LSP_SERVER.lsp.trace = trace

    _log_version_info(WORKSPACE_SETTINGS["path"])


@LSP_SERVER.feature(lsp.FORMATTING)
def formatting(_server: server.LanguageServer, params: types.DocumentFormattingParams):
    """LSP handler for textDocument/formatting request."""
    return _format(params)


if __name__ == "__main__":
    LSP_SERVER.start_io()
