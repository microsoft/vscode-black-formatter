# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for lsp_server._parse_tool_version."""

from __future__ import annotations

import pathlib
import sys

import pytest

# Ensure bundled/tool is on sys.path so we can import lsp_server directly.
_TOOL_DIR = str(pathlib.Path(__file__).parent.parent)
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)

from lsp_server import _parse_tool_version  # noqa: E402


class TestParseToolVersion:
    def test_parses_standard_black_version_output(self):
        # black prints 'black, 24.3.0 (compiled: yes)'; only the version
        # token should be returned.
        out = "black, 24.3.0 (compiled: yes)\n"
        assert _parse_tool_version(out) == "24.3.0"

    def test_parses_prerelease_version(self):
        out = "black, 24.3.0rc1 (compiled: yes)\n"
        assert _parse_tool_version(out) == "24.3.0rc1"

    def test_picks_longest_candidate_when_multiple_match(self):
        # Two version-shaped tokens; the real one is longer.
        out = "Python 3.12.0 black, 24.3.0rc1\n"
        assert _parse_tool_version(out) == "24.3.0rc1"

    def test_tolerates_crlf_line_endings(self):
        out = "black, 24.3.0 (compiled: yes)\r\n"
        assert _parse_tool_version(out) == "24.3.0"

    def test_raises_on_empty_output(self):
        with pytest.raises(ValueError, match="empty --version output"):
            _parse_tool_version("")

    def test_raises_on_whitespace_only_output(self):
        # Whitespace-only first line: not empty, but contains no version.
        with pytest.raises(ValueError, match="no version candidate"):
            _parse_tool_version("   \n")

    def test_raises_when_no_version_token(self):
        with pytest.raises(ValueError, match="no version candidate"):
            _parse_tool_version("something went wrong\n")

    def test_handles_two_part_version(self):
        out = "black, 24.3\n"
        assert _parse_tool_version(out) == "24.3"

    def test_uses_first_line_only(self):
        # A second line that contains a version is ignored; we only look
        # at the first line because that's where tools emit their banner.
        out = "black, 24.3.0\nsome other 1.2.3.4 token\n"
        assert _parse_tool_version(out) == "24.3.0"
