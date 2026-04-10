# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Tests for Jupyter notebook document lifecycle over LSP.

Black is a formatter, so these tests verify that notebook cells can be
opened, changed, saved, and closed via the notebook document protocol,
and that formatting produces correct results on notebook cells.
"""

from hamcrest import assert_that, is_

from .lsp_test_client import constants, session, utils

TIMEOUT = 10  # seconds

FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.formatted"
UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "sample.unformatted"


def _notebook_uri():
    """Build a notebook URI pointing to a .ipynb file in the test data directory."""
    return utils.as_uri(str(constants.TEST_DATA / "sample2" / "sample.ipynb"))


def _cell_uri(cell_id="C00001"):
    """Build a notebook cell URI."""
    return _notebook_uri().replace("file:", "vscode-notebook-cell:") + f"#{cell_id}"


def test_notebook_did_open():
    """Opening a notebook and formatting a cell produces correct edits."""
    contents = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    nb_uri = _notebook_uri()
    cell_uri = _cell_uri("C00001")

    with session.LspSession() as ls_session:
        ls_session.initialize()

        ls_session.notify_notebook_did_open(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "notebookType": "jupyter-notebook",
                    "version": 0,
                    "cells": [
                        {"kind": 2, "document": cell_uri},
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": cell_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    },
                ],
            }
        )

        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": cell_uri},
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    expected_text = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual_text = utils.apply_text_edits(contents, utils.destructure_text_edits(actual))
    assert_that(actual_text, is_(expected_text))


def test_notebook_did_change_text_content():
    """Formatting reflects updated cell content after a text change."""
    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    nb_uri = _notebook_uri()
    cell_uri = _cell_uri("C00001")

    with session.LspSession() as ls_session:
        ls_session.initialize()

        # Open with formatted content (already clean).
        ls_session.notify_notebook_did_open(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "notebookType": "jupyter-notebook",
                    "version": 0,
                    "cells": [
                        {"kind": 2, "document": cell_uri},
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": cell_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": formatted,
                    },
                ],
            }
        )

        # Change cell text to unformatted content.
        ls_session.notify_notebook_did_change(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "version": 1,
                },
                "change": {
                    "cells": {
                        "textContent": [
                            {
                                "document": {
                                    "uri": cell_uri,
                                    "version": 2,
                                },
                                "changes": [
                                    {
                                        "range": {
                                            "start": {"line": 0, "character": 0},
                                            "end": {
                                                "line": len(formatted.splitlines()),
                                                "character": 0,
                                            },
                                        },
                                        "text": unformatted,
                                    }
                                ],
                            }
                        ],
                    },
                },
            }
        )

        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": cell_uri},
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    actual_text = utils.apply_text_edits(
        unformatted, utils.destructure_text_edits(actual)
    )
    assert_that(actual_text, is_(formatted))


def test_notebook_did_change_add_cell():
    """Formatting works on a newly added cell."""
    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    nb_uri = _notebook_uri()
    cell1_uri = _cell_uri("C00001")
    cell2_uri = _cell_uri("C00002")

    with session.LspSession() as ls_session:
        ls_session.initialize()

        # Open notebook with one formatted cell.
        ls_session.notify_notebook_did_open(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "notebookType": "jupyter-notebook",
                    "version": 0,
                    "cells": [
                        {"kind": 2, "document": cell1_uri},
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": cell1_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": formatted,
                    },
                ],
            }
        )

        # Add a new cell with unformatted content.
        ls_session.notify_notebook_did_change(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "version": 1,
                },
                "change": {
                    "cells": {
                        "structure": {
                            "array": {
                                "start": 1,
                                "deleteCount": 0,
                                "cells": [
                                    {"kind": 2, "document": cell2_uri},
                                ],
                            },
                            "didOpen": [
                                {
                                    "uri": cell2_uri,
                                    "languageId": "python",
                                    "version": 1,
                                    "text": unformatted,
                                },
                            ],
                        },
                    },
                },
            }
        )

        # Format the newly added cell.
        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": cell2_uri},
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    actual_text = utils.apply_text_edits(
        unformatted, utils.destructure_text_edits(actual)
    )
    assert_that(actual_text, is_(formatted))


def test_notebook_did_save():
    """Saving a notebook does not interfere with cell formatting."""
    contents = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    nb_uri = _notebook_uri()
    cell_uri = _cell_uri("C00001")

    with session.LspSession() as ls_session:
        ls_session.initialize()

        ls_session.notify_notebook_did_open(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "notebookType": "jupyter-notebook",
                    "version": 0,
                    "cells": [
                        {"kind": 2, "document": cell_uri},
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": cell_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    },
                ],
            }
        )

        ls_session.notify_notebook_did_save(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                },
            }
        )

        # Formatting should still work after save.
        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": cell_uri},
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )

    expected_text = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual_text = utils.apply_text_edits(contents, utils.destructure_text_edits(actual))
    assert_that(actual_text, is_(expected_text))


def test_notebook_did_close():
    """Closing a notebook completes without errors."""
    contents = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    nb_uri = _notebook_uri()
    cell_uri = _cell_uri("C00001")

    with session.LspSession() as ls_session:
        ls_session.initialize()

        ls_session.notify_notebook_did_open(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                    "notebookType": "jupyter-notebook",
                    "version": 0,
                    "cells": [
                        {"kind": 2, "document": cell_uri},
                    ],
                },
                "cellTextDocuments": [
                    {
                        "uri": cell_uri,
                        "languageId": "python",
                        "version": 1,
                        "text": contents,
                    },
                ],
            }
        )

        # Verify formatting works before close.
        actual = ls_session.text_document_formatting(
            {
                "textDocument": {"uri": cell_uri},
                "options": {"tabSize": 4, "insertSpaces": True},
            }
        )
        assert actual, "Expected formatting edits before close"

        # Close the notebook.
        ls_session.notify_notebook_did_close(
            {
                "notebookDocument": {
                    "uri": nb_uri,
                },
                "cellTextDocuments": [
                    {"uri": cell_uri},
                ],
            }
        )
