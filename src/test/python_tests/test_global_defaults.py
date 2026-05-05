# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for _get_global_defaults() in lsp_server.

Verifies that each key in GLOBAL_SETTINGS is correctly read and returned
by _get_global_defaults(), and that sensible defaults are used when keys
are absent.

Mock setup is provided by conftest.py (setup_lsp_mocks).
"""

import sys

import lsp_server
import pytest


def _with_global_settings(overrides, fn):
    """Run fn with GLOBAL_SETTINGS temporarily set to overrides."""
    original = lsp_server.GLOBAL_SETTINGS.copy()
    try:
        lsp_server.GLOBAL_SETTINGS.clear()
        lsp_server.GLOBAL_SETTINGS.update(overrides)
        return fn()
    finally:
        lsp_server.GLOBAL_SETTINGS.clear()
        lsp_server.GLOBAL_SETTINGS.update(original)


@pytest.mark.parametrize(
    "overrides, key, expected",
    [
        pytest.param(
            {"path": ["/usr/bin/black"]}, "path", ["/usr/bin/black"], id="path-set"
        ),
        pytest.param({}, "path", [], id="path-default"),
        pytest.param(
            {"interpreter": ["/usr/bin/python3"]},
            "interpreter",
            ["/usr/bin/python3"],
            id="interpreter-set",
        ),
        pytest.param({}, "interpreter", [sys.executable], id="interpreter-default"),
        pytest.param(
            {"args": ["--line-length", "120"]},
            "args",
            ["--line-length", "120"],
            id="args-set",
        ),
        pytest.param({}, "args", [], id="args-default"),
        pytest.param(
            {"showNotifications": "always"},
            "showNotifications",
            "always",
            id="showNotifications-set",
        ),
        pytest.param({}, "showNotifications", "off", id="showNotifications-default"),
        pytest.param(
            {"importStrategy": "fromEnvironment"},
            "importStrategy",
            "fromEnvironment",
            id="importStrategy-set",
        ),
        pytest.param({}, "importStrategy", "useBundled", id="importStrategy-default"),
    ],
)
def test_global_defaults_setting(overrides, key, expected):
    """Each global setting is correctly read or defaults when absent."""
    result = _with_global_settings(overrides, lsp_server._get_global_defaults)
    assert result[key] == expected
