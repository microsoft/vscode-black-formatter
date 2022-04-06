# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Implementation of formatting support over LSP.
"""
import ast
import pathlib
import sys
import traceback
from typing import List, Union

# Ensure that will can import LSP libraries, and other bundled formatter libraries
sys.path.append(str(pathlib.Path(__file__).parent.parent / "libs"))

import utils
from pygls import lsp, protocol, server, workspace
from pygls.lsp import types

all_configurations = {
    "name": "Black",
    "module": "black",
    "patterns": {
        "default": {
            "args": [],
        }
    },
}

SETTINGS = {}
FORMATTER = {}

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


def _format(
    params: types.DocumentFormattingParams,
) -> Union[List[types.TextEdit], None]:
    """Runs formatter, processes the output, and returns text edits."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)

    if utils.is_stdlib_file(document.path):
        # Don't format standard library python files.
        return None

    module = FORMATTER["module"]
    use_path = len(SETTINGS["path"]) > 0

    argv = SETTINGS["path"] if use_path else [module]
    argv += _filter_args(FORMATTER["args"] + SETTINGS["args"])
    argv += _get_args_by_file_extension(document)
    argv += ["--stdin-filename", _get_filename_for_black(document), "-"]

    LSP_SERVER.show_message_log(" ".join(argv))

    # Force line endings to be `\n`, this makes the diff
    # easier to work with
    source = document.source.replace("\r\n", "\n")

    try:
        if use_path:
            result = utils.run_path(argv, True, source)
        else:
            result = utils.run_module(module, argv, True, source)
    except Exception:
        LSP_SERVER.show_message_log(
            traceback.format_exc(), msg_type=types.MessageType.Error
        )
        return None

    if result.stderr:
        LSP_SERVER.show_message_log(result.stderr, msg_type=types.MessageType.Error)

    new_source = _match_line_endings(document, result.stdout)

    # Skip last line ending in a notebook cell
    if document.uri.startswith("vscode-notebook-cell"):
        if new_source.endswith("\r\n"):
            new_source = new_source[:-2]
        elif new_source.endswith("\n"):
            new_source = new_source[:-1]

    if new_source == document.source:
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
    paths = "\r\n".join(sys.path)
    LSP_SERVER.show_message_log(f"sys.path used to run Formatter:\r\n{paths}")
    # First get workspace settings to know if we are using formatter
    # module or binary.
    global SETTINGS
    SETTINGS = params.initialization_options["settings"]

    global FORMATTER
    FORMATTER = utils.get_formatter_options_by_version(
        all_configurations,
        SETTINGS["path"] if len(SETTINGS["path"]) > 0 else None,
    )

    if isinstance(LSP_SERVER.lsp, protocol.LanguageServerProtocol):
        if SETTINGS["trace"] == "debug":
            LSP_SERVER.lsp.trace = lsp.Trace.Verbose
        elif SETTINGS["trace"] == "off":
            LSP_SERVER.lsp.trace = lsp.Trace.Off
        else:
            LSP_SERVER.lsp.trace = lsp.Trace.Messages


@LSP_SERVER.feature(lsp.FORMATTING)
def formatting(_server: server.LanguageServer, params: types.DocumentFormattingParams):
    """LSP handler for textDocument/formatting request."""
    return _format(params)


if __name__ == "__main__":
    LSP_SERVER.start_io()
