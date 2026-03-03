# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for the change_cwd() context manager in lsp_utils."""

import logging
import os
import pathlib
import sys
from unittest.mock import patch

# Ensure bundled libs and tool are importable.
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, os.fsdecode(_PROJECT_ROOT / "bundled" / "libs"))
sys.path.insert(0, os.fsdecode(_PROJECT_ROOT / "bundled" / "tool"))

import lsp_utils


def test_change_cwd_happy_path(tmp_path):
    """change_cwd switches to the requested directory and restores SERVER_CWD after."""
    original_cwd = os.getcwd()
    target = str(tmp_path)

    with lsp_utils.change_cwd(target):
        inside_cwd = os.getcwd()

    assert os.path.normcase(inside_cwd) == os.path.normcase(target)
    # After the context manager exits the working directory is restored.
    assert os.path.normcase(os.getcwd()) == os.path.normcase(lsp_utils.SERVER_CWD)

    # Restore for other tests.
    os.chdir(original_cwd)


def test_change_cwd_permission_error_does_not_crash(caplog):
    """When os.chdir raises PermissionError the body still runs, cwd is unchanged, and a warning is logged."""
    original_cwd = os.getcwd()
    body_executed = False

    with patch("lsp_utils.os.chdir", side_effect=PermissionError("Access denied")):
        with caplog.at_level(logging.WARNING):
            with lsp_utils.change_cwd("/restricted/path"):
                body_executed = True
                # The working directory must not have changed.
                assert os.path.normcase(os.getcwd()) == os.path.normcase(original_cwd)

    assert body_executed
    # cwd is still the original after the context manager exits.
    assert os.path.normcase(os.getcwd()) == os.path.normcase(original_cwd)
    # A warning must have been emitted mentioning the inaccessible path and the error.
    assert any("/restricted/path" in r.message for r in caplog.records)
    assert any("Access denied" in r.message for r in caplog.records)


def test_change_cwd_oserror_does_not_crash(caplog):
    """When os.chdir raises an arbitrary OSError the body still runs and a warning is logged."""
    original_cwd = os.getcwd()
    body_executed = False

    with patch("lsp_utils.os.chdir", side_effect=OSError("Some OS error")):
        with caplog.at_level(logging.WARNING):
            with lsp_utils.change_cwd("/inaccessible"):
                body_executed = True
                assert os.path.normcase(os.getcwd()) == os.path.normcase(original_cwd)

    assert body_executed
    assert os.path.normcase(os.getcwd()) == os.path.normcase(original_cwd)
    assert any("/inaccessible" in r.message for r in caplog.records)
    assert any("Some OS error" in r.message for r in caplog.records)
