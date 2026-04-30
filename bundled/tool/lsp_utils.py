# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Utility functions and classes for use with running tools over LSP.

Thin wrapper: delegates to vscode-common-python-lsp shared package,
providing backward-compatible names used by lsp_server.py.
"""

from __future__ import annotations

from typing import Sequence

from vscode_common_python_lsp import (
    CWD_LOCK,
    SERVER_CWD,
    CustomIO,
    PythonFileKind,
    QuickFixRegistrationError,
    RunResult,
    as_list,
    change_cwd,
    classify_python_file,
    is_current_interpreter,
    is_match,
    is_same_path,
    normalize_path,
    redirect_io,
    run_api,
    run_module as _run_module,
    run_path as _run_path,
    substitute_attr,
)

__all__ = [
    "SERVER_CWD",
    "CWD_LOCK",
    "as_list",
    "normalize_path",
    "is_same_path",
    "is_current_interpreter",
    "is_user_site_packages_file",
    "is_system_site_packages_file",
    "is_stdlib_file",
    "is_match",
    "RunResult",
    "CustomIO",
    "substitute_attr",
    "redirect_io",
    "change_cwd",
    "run_module",
    "run_path",
    "run_api",
    "QuickFixRegistrationError",
]


# Compatibility wrappers: the shared package uses classify_python_file()
# returning a PythonFileKind enum; these preserve the old per-kind API.


def is_user_site_packages_file(file_path: str) -> bool:
    """Return True if the file belongs to the user site-packages directory."""
    return classify_python_file(file_path) == PythonFileKind.USER_SITE


def is_system_site_packages_file(file_path: str) -> bool:
    """Return True if the file belongs to system site-packages directories."""
    return classify_python_file(file_path) == PythonFileKind.SYSTEM_SITE


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
