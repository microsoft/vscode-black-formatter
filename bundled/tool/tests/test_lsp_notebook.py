# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for lsp_notebook helpers: build_notebook_source and remap_diagnostics_to_cells."""

from __future__ import annotations

import pathlib
import sys

import pytest
from lsprotocol import types as lsp

# Ensure bundled/tool is on sys.path so we can import lsp_notebook directly.
_TOOL_DIR = str(pathlib.Path(__file__).parent.parent)
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)

import lsp_notebook  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeCell:
    """Minimal stand-in for a NotebookCell."""

    def __init__(self, uri: str, kind=lsp.NotebookCellKind.Code):
        self.document = uri
        self.kind = kind


class FakeTextDocument:
    """Minimal stand-in for a text document."""

    def __init__(self, source: str, language_id: str = "python"):
        self.source = source
        self.language_id = language_id


def _make_docs(mapping: dict[str, str]):
    """Return a get_text_document callable backed by *mapping*."""
    store = {uri: FakeTextDocument(src) for uri, src in mapping.items()}
    return lambda uri: store.get(uri)


def _diag(
    start_line: int,
    start_char: int,
    end_line: int,
    end_char: int,
    message: str = "error",
    **kwargs,
) -> lsp.Diagnostic:
    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=start_line, character=start_char),
            end=lsp.Position(line=end_line, character=end_char),
        ),
        message=message,
        **kwargs,
    )


# ===================================================================
# SyntheticDocument
# ===================================================================


class TestSyntheticDocument:
    """Tests for the SyntheticDocument dataclass."""

    def test_defaults(self):
        doc = lsp_notebook.SyntheticDocument(
            uri="notebook:abc", path="/nb.ipynb", source="x = 1"
        )
        assert doc.uri == "notebook:abc"
        assert doc.path == "/nb.ipynb"
        assert doc.source == "x = 1"
        assert doc.language_id == "python"
        assert doc.version == 0

    def test_custom_fields(self):
        doc = lsp_notebook.SyntheticDocument(
            uri="nb:1",
            path="/a.ipynb",
            source="y = 2",
            language_id="r",
            version=3,
        )
        assert doc.language_id == "r"
        assert doc.version == 3

    def test_satisfies_text_document_like(self):
        """SyntheticDocument should satisfy the TextDocumentLike Protocol."""
        doc = lsp_notebook.SyntheticDocument(uri="nb:1", path="/a.ipynb", source="code")
        # If this function accepts TextDocumentLike, the doc must work.
        assert doc.source == "code"
        assert doc.language_id == "python"


# ===================================================================
# build_notebook_source
# ===================================================================


class TestBuildNotebookSource:
    """Tests for build_notebook_source."""

    def test_single_cell(self):
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "x = 1\ny = 2\n"})
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        assert source == "x = 1\ny = 2\n"
        assert len(cell_map) == 1
        assert cell_map[0].cell_uri == "cell:0"
        assert cell_map[0].start_line == 0
        assert cell_map[0].line_count == 2

    def test_multiple_cells(self):
        cells = [FakeCell("cell:0"), FakeCell("cell:1"), FakeCell("cell:2")]
        docs = _make_docs(
            {
                "cell:0": "a = 1",
                "cell:1": "b = 2\nc = 3",
                "cell:2": "d = 4",
            }
        )
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        assert source == "a = 1\nb = 2\nc = 3\nd = 4\n"
        assert len(cell_map) == 3
        # Cell 0: line 0, 1 line
        assert cell_map[0].start_line == 0
        assert cell_map[0].line_count == 1
        # Cell 1: line 1, 2 lines
        assert cell_map[1].start_line == 1
        assert cell_map[1].line_count == 2
        # Cell 2: line 3, 1 line
        assert cell_map[2].start_line == 3
        assert cell_map[2].line_count == 1

    def test_skips_non_code_cells(self):
        cells = [
            FakeCell("cell:0", kind=lsp.NotebookCellKind.Markup),
            FakeCell("cell:1"),
        ]
        docs = _make_docs({"cell:0": "# Markdown", "cell:1": "x = 1"})
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        assert source == "x = 1\n"
        assert len(cell_map) == 1
        assert cell_map[0].cell_uri == "cell:1"

    def test_skips_non_python_cells(self):
        store = {
            "cell:0": FakeTextDocument("console.log(1)", language_id="javascript"),
            "cell:1": FakeTextDocument("x = 1"),
        }
        cells = [FakeCell("cell:0"), FakeCell("cell:1")]
        source, cell_map = lsp_notebook.build_notebook_source(
            cells, lambda uri: store.get(uri)
        )

        assert source == "x = 1\n"
        assert len(cell_map) == 1

    def test_skips_empty_cells(self):
        cells = [FakeCell("cell:0"), FakeCell("cell:1")]
        docs = _make_docs({"cell:0": "", "cell:1": "x = 1"})
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        assert source == "x = 1\n"
        assert len(cell_map) == 1

    def test_skips_missing_document(self):
        cells = [FakeCell("cell:0"), FakeCell("cell:1")]
        docs = _make_docs({"cell:1": "x = 1"})  # cell:0 not in store
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        assert source == "x = 1\n"
        assert len(cell_map) == 1

    def test_magic_lines_replaced_with_pass(self):
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "%matplotlib inline\nx = 1\n!pip install foo\n"})
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        lines = source.splitlines()
        assert lines[0] == "pass"
        assert lines[1] == "x = 1"
        assert lines[2] == "pass"

    def test_double_magic_replaced(self):
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "%%timeit\nx = 1\n"})
        source, _ = lsp_notebook.build_notebook_source(cells, docs)

        assert source.startswith("pass\n")

    def test_magic_regex_does_not_match_modulo_continuation(self):
        """Ensure % as modulo in continuation line is NOT treated as magic."""
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "    % name)\n"})
        source, _ = lsp_notebook.build_notebook_source(cells, docs)

        assert "% name)" in source  # must NOT be replaced with pass

    def test_magic_regex_does_not_match_not_equal(self):
        """Ensure != operator at start of continuation is NOT treated as magic."""
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "    != 0)\n"})
        source, _ = lsp_notebook.build_notebook_source(cells, docs)

        assert "!= 0)" in source  # must NOT be replaced with pass

    def test_magic_regex_does_not_match_modulo_assign(self):
        """Ensure %= (augmented assignment) is NOT treated as magic."""
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "  %= 10\n"})
        source, _ = lsp_notebook.build_notebook_source(cells, docs)

        assert "%= 10" in source

    def test_shell_capture_replaced(self):
        """Ensure !! (shell capture) IS treated as magic."""
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "!!echo hello\n"})
        source, _ = lsp_notebook.build_notebook_source(cells, docs)

        assert source.strip() == "pass"

    def test_trailing_newline_added(self):
        cells = [FakeCell("cell:0")]
        docs = _make_docs({"cell:0": "x = 1"})  # no trailing newline
        source, cell_map = lsp_notebook.build_notebook_source(cells, docs)

        assert source.endswith("\n")

    def test_empty_notebook_returns_empty(self):
        source, cell_map = lsp_notebook.build_notebook_source([], lambda _: None)

        assert source == ""
        assert cell_map == []

    def test_cell_with_none_document(self):
        cell = FakeCell("cell:0")
        cell.document = None
        source, cell_map = lsp_notebook.build_notebook_source([cell], lambda _: None)
        assert source == ""
        assert cell_map == []


# ===================================================================
# get_cell_for_line
# ===================================================================


class TestGetCellForLine:
    """Tests for get_cell_for_line."""

    @pytest.fixture()
    def cell_map(self) -> lsp_notebook.CellMap:
        return [
            lsp_notebook.CellOffset("cell:0", start_line=0, line_count=3),
            lsp_notebook.CellOffset("cell:1", start_line=3, line_count=2),
            lsp_notebook.CellOffset("cell:2", start_line=5, line_count=1),
        ]

    def test_first_cell(self, cell_map):
        assert lsp_notebook.get_cell_for_line(0, cell_map).cell_uri == "cell:0"
        assert lsp_notebook.get_cell_for_line(2, cell_map).cell_uri == "cell:0"

    def test_middle_cell(self, cell_map):
        assert lsp_notebook.get_cell_for_line(3, cell_map).cell_uri == "cell:1"
        assert lsp_notebook.get_cell_for_line(4, cell_map).cell_uri == "cell:1"

    def test_last_cell(self, cell_map):
        assert lsp_notebook.get_cell_for_line(5, cell_map).cell_uri == "cell:2"

    def test_out_of_range(self, cell_map):
        assert lsp_notebook.get_cell_for_line(6, cell_map) is None
        assert lsp_notebook.get_cell_for_line(100, cell_map) is None

    def test_empty_cell_map(self):
        assert lsp_notebook.get_cell_for_line(0, []) is None


# ===================================================================
# remap_diagnostics_to_cells
# ===================================================================


class TestRemapDiagnosticsToCells:
    """Tests for remap_diagnostics_to_cells."""

    @pytest.fixture()
    def cell_map(self) -> lsp_notebook.CellMap:
        # Cell 0: lines 0-2 (3 lines), Cell 1: lines 3-4 (2 lines)
        return [
            lsp_notebook.CellOffset("cell:0", start_line=0, line_count=3),
            lsp_notebook.CellOffset("cell:1", start_line=3, line_count=2),
        ]

    def test_single_diag_first_cell(self, cell_map):
        diags = [_diag(1, 5, 1, 10, "unused variable")]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        assert len(result["cell:0"]) == 1
        assert len(result["cell:1"]) == 0
        d = result["cell:0"][0]
        assert d.range.start.line == 1
        assert d.range.start.character == 5
        assert d.range.end.line == 1
        assert d.range.end.character == 10
        assert d.message == "unused variable"

    def test_single_diag_second_cell(self, cell_map):
        diags = [_diag(3, 0, 3, 5, "error in cell 1")]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        assert len(result["cell:0"]) == 0
        assert len(result["cell:1"]) == 1
        d = result["cell:1"][0]
        assert d.range.start.line == 0  # 3 - 3 = 0
        assert d.range.end.line == 0

    def test_diag_spanning_cells_is_clamped(self, cell_map):
        # Start in cell 0, end in cell 1 — should be clamped to cell 0 boundary.
        diags = [_diag(1, 5, 4, 3, "cross-cell")]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        assert len(result["cell:0"]) == 1
        d = result["cell:0"][0]
        assert d.range.start.line == 1
        assert d.range.end.line == 2  # clamped to max_end_line (3 - 1 = 2)
        assert d.range.end.character == 0  # clamped → character=0

    def test_diag_outside_all_cells_is_discarded(self, cell_map):
        diags = [_diag(10, 0, 10, 5, "orphaned")]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        assert len(result["cell:0"]) == 0
        assert len(result["cell:1"]) == 0

    def test_multiple_diags_in_same_cell(self, cell_map):
        diags = [
            _diag(0, 0, 0, 5, "error1"),
            _diag(2, 0, 2, 3, "error2"),
        ]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        assert len(result["cell:0"]) == 2

    def test_diags_distributed_across_cells(self, cell_map):
        diags = [
            _diag(1, 0, 1, 5, "in cell 0"),
            _diag(3, 0, 4, 2, "in cell 1"),
        ]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        assert len(result["cell:0"]) == 1
        assert len(result["cell:1"]) == 1

    def test_empty_diagnostics(self, cell_map):
        result = lsp_notebook.remap_diagnostics_to_cells([], cell_map)

        assert result["cell:0"] == []
        assert result["cell:1"] == []

    def test_preserves_severity_and_code(self, cell_map):
        diags = [
            _diag(
                0,
                0,
                0,
                5,
                message="test",
                severity=lsp.DiagnosticSeverity.Warning,
                code="W001",
                source="test-tool",
            )
        ]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        d = result["cell:0"][0]
        assert d.severity == lsp.DiagnosticSeverity.Warning
        assert d.code == "W001"
        assert d.source == "test-tool"

    def test_preserves_tags_and_data(self, cell_map):
        diags = [
            _diag(
                0,
                0,
                0,
                5,
                message="deprecated",
                tags=[lsp.DiagnosticTag.Deprecated],
                data={"key": "value"},
            )
        ]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        d = result["cell:0"][0]
        assert d.tags == [lsp.DiagnosticTag.Deprecated]
        assert d.data == {"key": "value"}

    def test_inverted_range_guard(self, cell_map):
        """When clamped end falls on same line as start with char=0, ensure no inversion."""
        # Cell 0 has 3 lines (0,1,2). Diag starts at line 2, char 5 and
        # ends at line 5 (outside cell) — clamped end = line 2, char 0.
        # Without the guard, end.character(0) < start.character(5) = inverted.
        diags = [_diag(2, 5, 5, 3, "clamped")]
        result = lsp_notebook.remap_diagnostics_to_cells(diags, cell_map)

        d = result["cell:0"][0]
        assert d.range.start.line == 2
        assert d.range.start.character == 5
        # Guard should ensure end >= start
        assert d.range.end.line == 2
        assert d.range.end.character >= d.range.start.character
