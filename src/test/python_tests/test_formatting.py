# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for formatting over LSP.
"""
from hamcrest import assert_that, is_

from .lsp_test_client import constants, session, utils

FORMATTER = utils.get_formatter_defaults()
TIMEOUT = 10  # 10 seconds


def test_formatting():
    """Test formating a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.python_file(contents, UNFORMATTED_TEST_FILE_PATH.parent) as pf:
        uri = utils.as_uri(str(pf))

        with session.LspSession() as ls_session:
            ls_session.initialize()
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    # `options` is not used by black
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
        }
    ]

    assert_that(actual, is_(expected))


def test_formatting_cell():
    """Test formating a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.formatted"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []

    # generate a fake cell uri
    uri = (
        utils.as_uri(UNFORMATTED_TEST_FILE_PATH.parent / "sample.ipynb").replace(
            "file:", "vscode-notebook-cell:"
        )
        + "#C00001"
    )

    with session.LspSession() as ls_session:
        ls_session.initialize()
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": uri},
                # `options` is not used by black
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
        }
    ]

    assert_that(actual, is_(expected))
