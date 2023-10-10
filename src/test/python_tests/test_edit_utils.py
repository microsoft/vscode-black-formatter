# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for TextEdit utils.
"""

import os
import pathlib
import sys

from hamcrest import assert_that, is_

# From: src\test\python_tests\test_edit_utils.py
# To: bundled\tool\lsp_edit_utils.py
UTILS_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "bundled" / "tool"
sys.path.append(os.fspath(UTILS_PATH))

from lsp_edit_utils import get_text_edits

from .lsp_test_client import constants, utils


def test_large_edits():
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.unformatted"

    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")

    edits = get_text_edits(unformatted, formatted, 4000)

    actual = utils.apply_text_edits(unformatted, edits)
    assert_that(actual, is_(formatted))


def test_with_levenshtein():
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.unformatted"

    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")

    with utils.install_packages(["Levenshtein"]):
        edits = get_text_edits(unformatted, formatted, 4000)

    actual = utils.apply_text_edits(unformatted, edits)
    assert_that(actual, is_(formatted))
