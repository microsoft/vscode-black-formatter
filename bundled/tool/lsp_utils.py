# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Utility functions and classes for use with running tools over LSP.

Thin wrapper: delegates to vscode-common-python-lsp shared package,
providing backward-compatible names used by lsp_server.py.
"""

from __future__ import annotations

from typing import Sequence

from vscode_common_python_lsp import (
    RunResult,
    classify_python_file,
)
from vscode_common_python_lsp import run_module as _run_module
from vscode_common_python_lsp import run_path as _run_path

__all__ = [
    "is_stdlib_file",
    "run_module",
    "run_path",
]


# Compatibility wrapper: the shared package uses classify_python_file()
# returning a PythonFileKind enum; this preserves the old boolean API.


def is_stdlib_file(file_path: str) -> bool:
    """Return True if the file belongs to a non-user Python path.

    The original implementation included stdlib, system site-packages,
    user site-packages, and extensions dir. Matching that broad semantics.
    """
    return classify_python_file(file_path) is not None


# Compatibility wrappers: the shared package's run_module does not accept
# a timeout parameter (in-process execution cannot be reliably timed out).
# The original lsp_utils accepted it as a no-op.  run_path passes through.


def run_module(
    module: str,
    argv: Sequence[str],
    use_stdin: bool,
    cwd: str,
    source: str = None,
    timeout: float = None,
) -> RunResult:
    """Runs as a module. timeout is accepted for compatibility but ignored."""
    return _run_module(module, argv, use_stdin, cwd, source)


def run_path(
    argv: Sequence[str],
    use_stdin: bool,
    cwd: str,
    source: str = None,
    timeout: float = None,
) -> RunResult:
    """Runs as an executable."""
    return _run_path(argv, use_stdin, cwd, source, timeout=timeout)
