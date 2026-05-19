# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for the get_cwd() helper in lsp_server.

Mock setup for pygls/lsprotocol and sys.path configuration is provided
by conftest.py — no per-file ``_setup_mocks()`` is needed.
"""

import os
import types

import lsp_server
import pytest

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


@pytest.mark.parametrize(
    "token, expected",
    [
        pytest.param("${file}", DOC_PATH, id="file"),
        pytest.param("${fileBasename}", "foo.py", id="fileBasename"),
        pytest.param("${fileBasenameNoExtension}", "foo", id="fileBasenameNoExtension"),
        pytest.param("${fileExtname}", ".py", id="fileExtname"),
        pytest.param("${fileDirname}", "/home/user/myproject/src", id="fileDirname"),
        pytest.param("${fileDirnameBasename}", "src", id="fileDirnameBasename"),
        pytest.param(
            "${relativeFile}",
            os.path.relpath(DOC_PATH, WORKSPACE),
            id="relativeFile",
        ),
        pytest.param(
            "${relativeFileDirname}",
            os.path.relpath("/home/user/myproject/src", WORKSPACE),
            id="relativeFileDirname",
        ),
        pytest.param("${fileWorkspaceFolder}", WORKSPACE, id="fileWorkspaceFolder"),
    ],
)
def test_single_variable_resolved(token, expected):
    """Each VS Code variable token resolves to its expected value."""
    settings = _make_settings(cwd=token)
    assert lsp_server.get_cwd(settings, DOC) == expected


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


def test_relative_file_variable_falls_back_to_absolute_path_on_mount_mismatch(monkeypatch):
    """Different mounts should not crash relative substitutions on Windows."""
    doc_path = r"X:\proj\src\foo.py"
    doc = _make_doc(doc_path)
    settings = {"workspaceFS": r"\\server\where_X_is_pointing_to", "cwd": "${relativeFile}"}

    def fake_relpath(path_value, start_value):
        raise ValueError(
            f"path is on mount '{path_value.split(os.sep)[0]}', start on mount '{start_value}'"
        )

    monkeypatch.setattr(os.path, "relpath", fake_relpath)

    assert lsp_server.get_cwd(settings, doc) == doc_path


def test_relative_file_dirname_variable_falls_back_to_absolute_dir_on_mount_mismatch(monkeypatch):
    """Different mounts should fall back to the document directory."""
    doc_path = r"X:\proj\src\foo.py"
    doc = _make_doc(doc_path)
    settings = {"workspaceFS": r"\\server\where_X_is_pointing_to", "cwd": "${relativeFileDirname}"}

    def fake_relpath(path_value, start_value):
        raise ValueError(
            f"path is on mount '{path_value.split(os.sep)[0]}', start on mount '{start_value}'"
        )

    monkeypatch.setattr(os.path, "relpath", fake_relpath)

    assert lsp_server.get_cwd(settings, doc) == os.path.dirname(doc_path)
