# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Regression tests for bundled server bootstrap path handling."""

import pathlib
import sys

import lsp_server


def test_configure_bundled_sys_path_prepends_bundled_paths(
    monkeypatch, tmp_path: pathlib.Path
):
    bundle_dir = tmp_path / "bundled"
    tool_dir = bundle_dir / "tool"
    libs_dir = bundle_dir / "libs"
    tool_dir.mkdir(parents=True)
    libs_dir.mkdir(parents=True)

    monkeypatch.setattr(sys, "path", ["env-site-packages"])

    lsp_server.configure_bundled_sys_path(bundle_dir)

    assert set(sys.path[:2]) == {str(tool_dir), str(libs_dir)}
    assert sys.path[2] == "env-site-packages"
