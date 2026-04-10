# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unit tests for the logging/notification helpers in lsp_server.

Covers the Pygls 2 migration which changed logging calls from
show_message_log/show_message to window_log_message/window_show_message
with parameter objects, and verifies the LS_SHOW_NOTIFICATION gating logic.

Mock setup is provided by conftest.py (setup_lsp_mocks).
LSP_SERVER patching uses the ``patched_lsp_server`` fixture which restores
originals automatically via ``unittest.mock.patch.object``.
"""

import os
from unittest.mock import patch

import lsp_server


# ---------------------------------------------------------------------------
# log_to_output
# ---------------------------------------------------------------------------
def test_log_to_output_calls_window_log_message(patched_lsp_server):
    """log_to_output uses the Pygls 2 window_log_message API."""
    log_mock, show_mock = patched_lsp_server

    lsp_server.log_to_output("hello")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


# ---------------------------------------------------------------------------
# log_error
# ---------------------------------------------------------------------------
def test_log_error_always_logs(patched_lsp_server):
    """log_error always calls window_log_message regardless of notification setting."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "off"}):
        lsp_server.log_error("error occurred")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


def test_log_error_shows_notification_on_error(patched_lsp_server):
    """log_error shows a notification popup when LS_SHOW_NOTIFICATION=onError."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "onError"}):
        lsp_server.log_error("error occurred")

    log_mock.assert_called_once()
    show_mock.assert_called_once()


def test_log_error_shows_notification_on_always(patched_lsp_server):
    """log_error shows a notification popup when LS_SHOW_NOTIFICATION=always."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "always"}):
        lsp_server.log_error("error occurred")

    log_mock.assert_called_once()
    show_mock.assert_called_once()


# ---------------------------------------------------------------------------
# log_warning
# ---------------------------------------------------------------------------
def test_log_warning_no_notification_when_off(patched_lsp_server):
    """log_warning does not show notification when LS_SHOW_NOTIFICATION=off."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "off"}):
        lsp_server.log_warning("warning message")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


def test_log_warning_no_notification_on_error_only(patched_lsp_server):
    """log_warning does not show notification when LS_SHOW_NOTIFICATION=onError."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "onError"}):
        lsp_server.log_warning("warning message")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


def test_log_warning_shows_notification_on_warning(patched_lsp_server):
    """log_warning shows notification when LS_SHOW_NOTIFICATION=onWarning."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "onWarning"}):
        lsp_server.log_warning("warning message")

    log_mock.assert_called_once()
    show_mock.assert_called_once()


def test_log_warning_shows_notification_on_always(patched_lsp_server):
    """log_warning shows notification when LS_SHOW_NOTIFICATION=always."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "always"}):
        lsp_server.log_warning("warning message")

    log_mock.assert_called_once()
    show_mock.assert_called_once()


# ---------------------------------------------------------------------------
# log_always
# ---------------------------------------------------------------------------
def test_log_always_no_notification_when_off(patched_lsp_server):
    """log_always does not show notification when LS_SHOW_NOTIFICATION=off."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "off"}):
        lsp_server.log_always("info message")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


def test_log_always_no_notification_on_error(patched_lsp_server):
    """log_always does not show notification when LS_SHOW_NOTIFICATION=onError."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "onError"}):
        lsp_server.log_always("info message")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


def test_log_always_no_notification_on_warning(patched_lsp_server):
    """log_always does not show notification when LS_SHOW_NOTIFICATION=onWarning."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "onWarning"}):
        lsp_server.log_always("info message")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


def test_log_always_shows_notification_on_always(patched_lsp_server):
    """log_always shows notification only when LS_SHOW_NOTIFICATION=always."""
    log_mock, show_mock = patched_lsp_server

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": "always"}):
        lsp_server.log_always("info message")

    log_mock.assert_called_once()
    show_mock.assert_called_once()
