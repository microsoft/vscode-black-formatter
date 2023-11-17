# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for formatting over LSP.
"""
import pathlib

import pytest
from hamcrest import assert_that, is_

from .lsp_test_client import constants, session, utils

FORMATTER = utils.get_server_info_defaults()


@pytest.mark.parametrize("sample", ["sample1", "sample3"])
def test_formatting(sample: str):
    """Test formatting a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / sample / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / sample / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")

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

    expected_text = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual_text = utils.apply_text_edits(contents, utils.destructure_text_edits(actual))
    assert_that(actual_text, is_(expected_text))


def test_formatting_cell():
    """Test formating a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.formatted"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")

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

    expected_text = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual_text = utils.apply_text_edits(contents, utils.destructure_text_edits(actual))
    assert_that(actual_text, is_(expected_text))


def test_skipping_site_packages_files():
    """Test skipping formatting when the file is in site-packages"""

    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.unformatted"
    with session.LspSession() as ls_session:
        # Use any stdlib path here
        uri = utils.as_uri(pathlib.__file__)
        ls_session.initialize()
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8"),
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

    expected = None
    assert_that(actual, is_(expected))


@pytest.mark.parametrize(
    "sample, ranges", [("sample4", "single-range"), ("sample5", "multi-range")]
)
def test_range_formatting(sample: str, ranges: str):
    """Test formatting a python file."""
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / sample / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / sample / "sample.unformatted"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    lines = contents.splitlines()

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

            if ranges == "single-range":
                actual = ls_session.text_document_range_formatting(
                    {
                        "textDocument": {"uri": uri},
                        # `options` is not used by black
                        "options": {"tabSize": 4, "insertSpaces": True},
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": len(lines[0])},
                        },
                    }
                )
            else:
                actual = ls_session.text_document_ranges_formatting(
                    {
                        "textDocument": {"uri": uri},
                        # `options` is not used by black
                        "options": {"tabSize": 4, "insertSpaces": True},
                        "ranges": [
                            {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": 0, "character": len(lines[0])},
                            },
                            {
                                "start": {"line": 2, "character": 0},
                                "end": {"line": 2, "character": len(lines[2])},
                            },
                        ],
                    }
                )

    expected_text = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual_text = utils.apply_text_edits(contents, utils.destructure_text_edits(actual))
    assert_that(actual_text, is_(expected_text))
