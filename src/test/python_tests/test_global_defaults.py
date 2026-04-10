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


def test_path_read_from_global_settings():
    """_get_global_defaults() returns path from GLOBAL_SETTINGS."""
    result = _with_global_settings(
        {"path": ["/usr/bin/black"]},
        lsp_server._get_global_defaults,
    )
    assert result["path"] == ["/usr/bin/black"]


def test_path_defaults_to_empty_list():
    """_get_global_defaults() returns [] when GLOBAL_SETTINGS has no path."""
    result = _with_global_settings({}, lsp_server._get_global_defaults)
    assert result["path"] == []


def test_interpreter_read_from_global_settings():
    """_get_global_defaults() returns interpreter from GLOBAL_SETTINGS."""
    result = _with_global_settings(
        {"interpreter": ["/usr/bin/python3"]},
        lsp_server._get_global_defaults,
    )
    assert result["interpreter"] == ["/usr/bin/python3"]


def test_interpreter_defaults_to_sys_executable():
    """_get_global_defaults() defaults interpreter to [sys.executable]."""
    result = _with_global_settings({}, lsp_server._get_global_defaults)
    assert result["interpreter"] == [sys.executable]


def test_args_read_from_global_settings():
    """_get_global_defaults() returns args from GLOBAL_SETTINGS."""
    result = _with_global_settings(
        {"args": ["--line-length", "120"]},
        lsp_server._get_global_defaults,
    )
    assert result["args"] == ["--line-length", "120"]


def test_args_defaults_to_empty_list():
    """_get_global_defaults() returns [] when GLOBAL_SETTINGS has no args."""
    result = _with_global_settings({}, lsp_server._get_global_defaults)
    assert result["args"] == []


def test_show_notifications_read_from_global_settings():
    """_get_global_defaults() returns showNotifications from GLOBAL_SETTINGS."""
    result = _with_global_settings(
        {"showNotifications": "always"},
        lsp_server._get_global_defaults,
    )
    assert result["showNotifications"] == "always"


def test_show_notifications_defaults_to_off():
    """_get_global_defaults() defaults showNotifications to 'off'."""
    result = _with_global_settings({}, lsp_server._get_global_defaults)
    assert result["showNotifications"] == "off"


def test_import_strategy_read_from_global_settings():
    """_get_global_defaults() returns importStrategy from GLOBAL_SETTINGS."""
    result = _with_global_settings(
        {"importStrategy": "fromEnvironment"},
        lsp_server._get_global_defaults,
    )
    assert result["importStrategy"] == "fromEnvironment"


def test_import_strategy_defaults_to_use_bundled():
    """_get_global_defaults() defaults importStrategy to 'useBundled'."""
    result = _with_global_settings({}, lsp_server._get_global_defaults)
    assert result["importStrategy"] == "useBundled"
