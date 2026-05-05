# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Notebook-specific helpers for whole-notebook linting with cross-cell context.

Thin wrapper: delegates to vscode-common-python-lsp shared package.
"""

from vscode_common_python_lsp import (  # noqa: F401
    MAGIC_LINE_RE,
    NOTEBOOK_SYNC_OPTIONS,
    CellOffset,
    SyntheticDocument,
    TextDocumentLike,
    build_notebook_source,
    get_cell_for_line,
    remap_diagnostics_to_cells,
)

# Re-export CellMap type alias for backward compatibility.
CellMap = list[CellOffset]
