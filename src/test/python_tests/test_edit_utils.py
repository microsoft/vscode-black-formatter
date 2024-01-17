# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for TextEdit utils.
"""

import os
import pathlib
import sys
from typing import List

import pytest
from hamcrest import assert_that, is_
from lsprotocol import types as lsp

# From: src\test\python_tests\test_edit_utils.py
# To: bundled\tool\lsp_edit_utils.py
UTILS_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "bundled" / "tool"
sys.path.append(os.fspath(UTILS_PATH))

from lsp_edit_utils import get_text_edits

from .lsp_test_client import constants, utils


@pytest.mark.parametrize(
    "encoding,expected",
    [
        (
            lsp.PositionEncodingKind.Utf8,
            [
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(0, 4), lsp.Position(0, 5)),
                    new_text='"',
                ),
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(0, 8), lsp.Position(0, 9)),
                    new_text='"',
                ),
            ],
        ),
        (
            lsp.PositionEncodingKind.Utf16,
            [
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(0, 4), lsp.Position(0, 5)),
                    new_text='"',
                ),
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(0, 7), lsp.Position(0, 8)),
                    new_text='"',
                ),
            ],
        ),
        (
            lsp.PositionEncodingKind.Utf32,
            [
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(0, 4), lsp.Position(0, 5)),
                    new_text='"',
                ),
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(0, 6), lsp.Position(0, 7)),
                    new_text='"',
                ),
            ],
        ),
    ],
)
def test_with_emojis(encoding: lsp.PositionEncodingKind, expected: List[lsp.TextEdit]):
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample6" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample6" / "sample.unformatted"

    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual = get_text_edits(unformatted, formatted, encoding, 4000)

    assert_that(actual, is_(expected))


@pytest.mark.parametrize(
    "encoding,expected",
    [
        (
            lsp.PositionEncodingKind.Utf8,
            [
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(1, 136), lsp.Position(1, 136)),
                    new_text="\n   ",
                ),
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(1, 268), lsp.Position(1, 268)),
                    new_text=",",
                ),
            ],
        ),
        (
            lsp.PositionEncodingKind.Utf16,
            [
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(1, 93), lsp.Position(1, 93)),
                    new_text="\n   ",
                ),
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(1, 182), lsp.Position(1, 182)),
                    new_text=",",
                ),
            ],
        ),
        (
            lsp.PositionEncodingKind.Utf32,
            [
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(1, 50), lsp.Position(1, 50)),
                    new_text="\n   ",
                ),
                lsp.TextEdit(
                    range=lsp.Range(lsp.Position(1, 96), lsp.Position(1, 96)),
                    new_text=",",
                ),
            ],
        ),
    ],
)
def test_with_emojis2(encoding: lsp.PositionEncodingKind, expected: List[lsp.TextEdit]):
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample7" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample7" / "sample.unformatted"

    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    actual = get_text_edits(unformatted, formatted, encoding, 4000)

    assert_that(actual, is_(expected))


def test_large_edits():
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.unformatted"

    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")

    edits = get_text_edits(unformatted, formatted, lsp.PositionEncodingKind.Utf32, 4000)

    actual = utils.apply_text_edits(unformatted, edits)
    assert_that(actual, is_(formatted))


def has_levenshtein():
    try:
        import Levenshtein  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not has_levenshtein(), reason="Levenshtein is not installed")
def test_with_levenshtein():
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.py"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "sample.unformatted"

    formatted = FORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")
    unformatted = UNFORMATTED_TEST_FILE_PATH.read_text(encoding="utf-8")

    with utils.install_packages(["Levenshtein"]):
        edits = get_text_edits(
            unformatted, formatted, lsp.PositionEncodingKind.Utf32, 4000
        )

    actual = utils.apply_text_edits(unformatted, edits)
    assert_that(actual, is_(formatted))
