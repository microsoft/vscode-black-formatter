"""Unit tests for lsp_server._parse_tool_version.

The version parser is called on the raw stdout of the user's local
``black --version`` invocation, which on a real install can include
parenthetical info ("compiled: yes"), the embedded Python interpreter
version ("(Python 3.12.1)"), or just be empty. The previous
inline implementation only kept a version when exactly one such token
appeared on the first line, so the parenthetical case silently fell
back to the literal string "0.0.0" and logged a misleading
"NOT supported" line for every workspace.
"""
from __future__ import annotations

import pathlib
import sys

# Ensure bundled/tool is on sys.path so we can import lsp_server directly.
_TOOL_DIR = str(pathlib.Path(__file__).resolve().parent.parent)
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)

import lsp_server  # noqa: E402


class TestParseToolVersion:
    """Tests for lsp_server._parse_tool_version."""

    def test_standard_black_output(self):
        assert lsp_server._parse_tool_version("black, 26.3.1 (compiled: yes)") == "26.3.1"

    def test_just_version(self):
        assert lsp_server._parse_tool_version("black, 22.3.0") == "22.3.0"

    def test_pre_release_version(self):
        # PEP 440 pre-release syntax: 24.3.0rc1
        assert lsp_server._parse_tool_version("black, 24.3.0rc1") == "24.3.0rc1"

    def test_dev_version_with_local_segment(self):
        # PEP 440 dev / local-version: 24.3.0.dev1+g1234
        assert (
            lsp_server._parse_tool_version("black, 24.3.0.dev1+g1234")
            == "24.3.0.dev1+g1234"
        )

    def test_compiled_and_python_in_parens(self):
        # The original bug: the parenthetical "(Python 3.12.1)" is matched
        # by the version regex, so the previous "exactly one match" check
        # silently fell back to "0.0.0".
        out = lsp_server._parse_tool_version(
            "black, 26.3.1 (compiled: yes, Python 3.12.1)"
        )
        assert out == "26.3.1"

    def test_compiled_and_python_in_parens_alternate(self):
        out = lsp_server._parse_tool_version(
            "black 22.3.0 (compiled: yes, Python: 3.11.4)"
        )
        assert out == "22.3.0"

    def test_trailing_newline(self):
        assert lsp_server._parse_tool_version("black, 22.3.0\n") == "22.3.0"

    def test_crlf_line_endings(self):
        # Black is a Windows-friendly formatter; on Windows the captured
        # stdout uses CRLF. The helper should ignore the trailing CR.
        assert lsp_server._parse_tool_version("black, 22.3.0\r\n") == "22.3.0"

    def test_empty_stdout(self):
        # Empty input must not crash — returning the literal "0.0.0" lets
        # the >= 22.3.0 comparison below it report "NOT supported" with
        # a clear message instead of a KeyError or IndexError.
        assert lsp_server._parse_tool_version("") == "0.0.0"

    def test_whitespace_only(self):
        assert lsp_server._parse_tool_version("\n   \n") == "0.0.0"

    def test_no_version_token(self):
        assert lsp_server._parse_tool_version("no version here") == "0.0.0"

    def test_only_python_banner(self):
        # Standalone CPython banner (no tool name). Leftmost match wins.
        assert lsp_server._parse_tool_version("Python 3.12.0") == "3.12.0"

    def test_uses_first_line_only(self):
        # The first line is the only one that matters — a banner on the
        # second line should be ignored.
        out = "black, 22.3.0 (compiled: yes)\nPython 3.12.0\n"
        assert lsp_server._parse_tool_version(out) == "22.3.0"
