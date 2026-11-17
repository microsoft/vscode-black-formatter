# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Tests that bundled package metadata is intact.

The extension ships bundled Python packages in ``bundled/libs/``.
Some packages use ``importlib.metadata`` at runtime to resolve their
version string, which requires the corresponding ``.dist-info``
directory to be present.  These tests verify the metadata was not
accidentally excluded.
"""

import importlib.metadata
import importlib.util
import json
import pathlib
import sys

import pytest

BUNDLED_LIBS = pathlib.Path(__file__).parent.parent.parent.parent / "bundled" / "libs"


@pytest.fixture(autouse=True)
def _ensure_bundled_on_path():
    """Temporarily prepend ``bundled/libs`` to ``sys.path``."""
    libs = str(BUNDLED_LIBS)
    if libs not in sys.path:
        sys.path.insert(0, libs)
        yield
        sys.path.remove(libs)
    else:
        yield


def test_black_metadata_version():
    """importlib.metadata must be able to resolve the bundled black version."""
    version = importlib.metadata.version("black")
    assert version, "black version string should not be empty"
    parts = version.split(".")
    assert len(parts) >= 2, f"Unexpected version format: {version}"


def test_common_lsp_package_is_bundled():
    """The server imports this package before it can start."""
    spec = importlib.util.find_spec("vscode_common_python_lsp")
    assert spec is not None
    assert pathlib.Path(spec.origin).is_relative_to(BUNDLED_LIBS)


def test_common_lsp_metadata_records_a_non_editable_local_install():
    """Keep local distribution metadata alongside the shared import package."""
    distribution = importlib.metadata.distribution("vscode-python-tool-internal")
    package = distribution.locate_file("vscode_common_python_lsp/__init__.py")
    assert package.is_relative_to(BUNDLED_LIBS)
    source = json.loads(distribution.read_text("direct_url.json"))
    assert source["url"].endswith("/external/vscode-common-python-lsp/python")
    assert source["dir_info"].get("editable", False) is False
