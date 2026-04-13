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
import pytest


def test_log_to_output_calls_window_log_message(patched_lsp_server):
    """log_to_output uses the Pygls 2 window_log_message API."""
    log_mock, show_mock = patched_lsp_server

    lsp_server.log_to_output("hello")

    log_mock.assert_called_once()
    show_mock.assert_not_called()


@pytest.mark.parametrize(
    "log_func_name, message, notification_setting, expect_show",
    [
        pytest.param("log_error", "error occurred", "off", False, id="error-off"),
        pytest.param(
            "log_error", "error occurred", "onError", True, id="error-onError"
        ),
        pytest.param("log_error", "error occurred", "always", True, id="error-always"),
        pytest.param("log_warning", "warning message", "off", False, id="warning-off"),
        pytest.param(
            "log_warning", "warning message", "onError", False, id="warning-onError"
        ),
        pytest.param(
            "log_warning", "warning message", "onWarning", True, id="warning-onWarning"
        ),
        pytest.param(
            "log_warning", "warning message", "always", True, id="warning-always"
        ),
        pytest.param("log_always", "info message", "off", False, id="always-off"),
        pytest.param(
            "log_always", "info message", "onError", False, id="always-onError"
        ),
        pytest.param(
            "log_always", "info message", "onWarning", False, id="always-onWarning"
        ),
        pytest.param("log_always", "info message", "always", True, id="always-always"),
    ],
)
def test_notification_gating(
    patched_lsp_server, log_func_name, message, notification_setting, expect_show
):
    """Log functions always log; notifications are gated by LS_SHOW_NOTIFICATION."""
    log_mock, show_mock = patched_lsp_server
    log_func = getattr(lsp_server, log_func_name)

    with patch.dict(os.environ, {"LS_SHOW_NOTIFICATION": notification_setting}):
        log_func(message)

    log_mock.assert_called_once()
    if expect_show:
        show_mock.assert_called_once()
    else:
        show_mock.assert_not_called()
