# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Implementation of formatting support over LSP.
"""
import ast
import json
import os
import pathlib
import sys
import traceback
from typing import List, Union

# Ensure that we can import LSP libraries, and other bundled formatter libraries
sys.path.append(str(pathlib.Path(__file__).parent.parent / "libs"))

import utils
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


def _update_workspace_settings(settings):
    for setting in settings:
        key = uris.to_fs_path(setting["workspace"])
        WORKSPACE_SETTINGS[key] = {
            **setting,
            "workspaceFS": key,
        }


def _get_settings_by_document(document: workspace.Document):
    if len(WORKSPACE_SETTINGS) == 1 or document.path is None:
        return list(WORKSPACE_SETTINGS.values())[0]

    document_workspace = pathlib.Path(document.path)
    workspaces = [s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()]

    while document_workspace != document_workspace.parent:
        if str(document_workspace) in workspaces:
            break
        document_workspace = document_workspace.parent

    return WORKSPACE_SETTINGS[str(document_workspace)]


def _get_error_message_from_stderr(stderr: str) -> str:
    """
    Compose error message from stderr, while trying to display most relevant data first.

    Reason: message window in vscode is minimized and doesn't always show full message.
    This will hopefully reduce amount of times when user have to interact with that window.
    """
    message: "list[tuple[int, str]]" = []

    current_priority = 0
    first_line_priority = 1

    for line in map(str.strip, stderr.splitlines()):
        if line.lower().startswith('error:'):
            error, *parse_error = line.lower().split("cannot parse:")
            if parse_error:
                # the most relevant thing here is the line that couldn't be parsed, so show it first
                filename = error.replace("error:", "").replace("cannot format", "").strip()
                message.append(
                    (first_line_priority, f"Error: {parse_error[0]} cannot be parsed in {filename}")
                    )
            else:
                message.append((first_line_priority, line))
        else:
            message.append((current_priority, line))
            current_priority -= 1
    
    return "  ".join(line for _, line in sorted(message, reverse=True))


def _format(
    params: types.DocumentFormattingParams,
) -> Union[List[types.TextEdit], None]:
    """Runs formatter, processes the output, and returns text edits."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)

    settings = _get_settings_by_document(document)

    if utils.is_stdlib_file(document.path):
        message = f"Not going to reformat stdlib or site-packages ({document.path}), aborting..."
        LSP_SERVER.show_message_log(message)
        if settings["show-formatting-messages"]:
            LSP_SERVER.show_message(message, msg_type=types.MessageType.Info)
        return None

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
    except Exception as e:
        # this is quite unexpected and we should never end up here
        error_text = f"Encountered exception while executing black:\r\n{traceback.format_exc()}"
        LSP_SERVER.show_message_log(error_text, msg_type=types.MessageType.Error)
        LSP_SERVER.show_message(
            f"Fatal error: {e!r}, please see Output > Black Formatter for more info",
            msg_type=types.MessageType.Error,
        )
        return None

    if result.stderr:
        LSP_SERVER.show_message_log(result.stderr, msg_type=types.MessageType.Error)
        if "error:" in result.stderr.lower() and settings["show-formatting-messages"]:
            LSP_SERVER.show_message(_get_error_message_from_stderr(result.stderr), msg_type=types.MessageType.Error)
        # not going to exit just yet, check if black gave us any stdout first
        

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
    LSP_SERVER.show_message_log(f"CWD Format Server: {os.getcwd()}")

    paths = "\r\n    ".join(sys.path)
    LSP_SERVER.show_message_log(f"sys.path used to run Formatter:\r\n    {paths}\r\n")

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    LSP_SERVER.show_message_log(
        f"Settings used to run Formatter:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )

    if isinstance(LSP_SERVER.lsp, protocol.LanguageServerProtocol):
        trace = lsp.Trace.Off
        for setting in settings:
            if setting["trace"] == "debug":
                trace = lsp.Trace.Verbose
                break
            if setting["trace"] == "off":
                continue
            trace = lsp.Trace.Messages
        LSP_SERVER.lsp.trace = trace


@LSP_SERVER.feature(lsp.FORMATTING)
def formatting(_server: server.LanguageServer, params: types.DocumentFormattingParams):
    """LSP handler for textDocument/formatting request."""
    try:
        return _format(params)
    except Exception as e:
        # gracefully handle error and notify the user
        LSP_SERVER.show_message_log(traceback.format_exc(), msg_type=types.MessageType.Error)
        LSP_SERVER.show_message(
            f"Fatal error: {e!r}, please see Output > Black Formatter for more info",
            msg_type=types.MessageType.Error,
        )
        return None


if __name__ == "__main__":
    LSP_SERVER.start_io()
