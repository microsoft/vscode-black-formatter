# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for the get_cwd() helper in lsp_server.

Mock setup for pygls/lsprotocol and sys.path configuration is provided
by conftest.py — no per-file ``_setup_mocks()`` is needed.
"""

import os
import types

import lsp_server

WORKSPACE = "/home/user/myproject"


def _make_settings(cwd=None):
    s = {"workspaceFS": WORKSPACE}
    if cwd is not None:
        s["cwd"] = cwd
    return s


def _make_doc(path):
    # Include uri so _get_document_path() can resolve the path correctly.
    doc = types.SimpleNamespace(path=path, uri="file://" + path)
    return doc


# ---------------------------------------------------------------------------
# No-document (fallback) cases
# ---------------------------------------------------------------------------


def test_no_cwd_no_document_returns_workspace():
    """When neither cwd nor document is provided, return workspaceFS."""
    settings = _make_settings()
    assert lsp_server.get_cwd(settings, None) == WORKSPACE


def test_plain_cwd_no_document_returned_unchanged():
    """A cwd without variables is returned as-is even without a document."""
    settings = _make_settings(cwd="/custom/path")
    assert lsp_server.get_cwd(settings, None) == "/custom/path"


def test_file_variable_no_document_falls_back_to_workspace():
    """Unresolvable ${file*} variable with no document falls back to workspaceFS."""
    for token in [
        "${file}",
        "${fileBasename}",
        "${fileBasenameNoExtension}",
        "${fileExtname}",
        "${fileDirname}",
        "${fileDirnameBasename}",
        "${fileWorkspaceFolder}",
    ]:
        settings = _make_settings(cwd=token + "/extra")
        assert lsp_server.get_cwd(settings, None) == WORKSPACE, f"Failed for {token}"


def test_relative_file_variable_no_document_falls_back_to_workspace():
    """Unresolvable ${relativeFile*} variable with no document falls back to workspaceFS."""
    for token in ["${relativeFile}", "${relativeFileDirname}"]:
        settings = _make_settings(cwd=token)
        assert lsp_server.get_cwd(settings, None) == WORKSPACE, f"Failed for {token}"


# ---------------------------------------------------------------------------
# With document
# ---------------------------------------------------------------------------

DOC_PATH = "/home/user/myproject/src/foo.py"
DOC = _make_doc(DOC_PATH)


def test_file_resolved():
    settings = _make_settings(cwd="${file}")
    assert lsp_server.get_cwd(settings, DOC) == DOC_PATH


def test_file_basename_resolved():
    settings = _make_settings(cwd="${fileBasename}")
    assert lsp_server.get_cwd(settings, DOC) == "foo.py"


def test_file_basename_no_extension_resolved():
    settings = _make_settings(cwd="${fileBasenameNoExtension}")
    assert lsp_server.get_cwd(settings, DOC) == "foo"


def test_file_extname_resolved():
    settings = _make_settings(cwd="${fileExtname}")
    assert lsp_server.get_cwd(settings, DOC) == ".py"


def test_file_dirname_resolved():
    settings = _make_settings(cwd="${fileDirname}")
    assert lsp_server.get_cwd(settings, DOC) == "/home/user/myproject/src"


def test_file_dirname_basename_resolved():
    settings = _make_settings(cwd="${fileDirnameBasename}")
    assert lsp_server.get_cwd(settings, DOC) == "src"


def test_relative_file_resolved():
    settings = _make_settings(cwd="${relativeFile}")
    assert lsp_server.get_cwd(settings, DOC) == os.path.relpath(DOC_PATH, WORKSPACE)


def test_relative_file_dirname_resolved():
    settings = _make_settings(cwd="${relativeFileDirname}")
    assert lsp_server.get_cwd(settings, DOC) == os.path.relpath(
        "/home/user/myproject/src", WORKSPACE
    )


def test_file_workspace_folder_resolved():
    settings = _make_settings(cwd="${fileWorkspaceFolder}")
    assert lsp_server.get_cwd(settings, DOC) == WORKSPACE


def test_composite_pattern_resolved():
    """Variables embedded inside a longer path are substituted correctly."""
    settings = _make_settings(cwd="${fileDirname}/subdir")
    assert lsp_server.get_cwd(settings, DOC) == "/home/user/myproject/src/subdir"


def test_multiple_variables_in_one_cwd():
    """Multiple different variables in the same cwd string are all resolved."""
    settings = _make_settings(cwd="${fileDirname}/${fileBasename}")
    result = lsp_server.get_cwd(settings, DOC)
    assert result == "/home/user/myproject/src/foo.py"


def test_no_variable_in_cwd_unchanged():
    """A cwd with no variables is returned unchanged even when a document exists."""
    settings = _make_settings(cwd="/static/path")
    assert lsp_server.get_cwd(settings, DOC) == "/static/path"


def test_document_with_no_path_falls_back_to_workspace():
    """A document object whose path is falsy triggers the fallback."""
    doc = types.SimpleNamespace(path="", uri="file://")
    settings = _make_settings(cwd="${fileDirname}")
    assert lsp_server.get_cwd(settings, doc) == WORKSPACE
