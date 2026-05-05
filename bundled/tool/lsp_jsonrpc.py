# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Light-weight JSON-RPC over standard IO.

Thin wrapper: delegates to vscode-common-python-lsp shared package,
providing backward-compatible names used by lsp_server.py.
"""

from __future__ import annotations

import pathlib
from collections.abc import Sequence
from typing import Optional, Union

from vscode_common_python_lsp import JsonRpc, RpcRunResult, StreamClosedException
from vscode_common_python_lsp import get_or_start_json_rpc as _get_or_start_json_rpc
from vscode_common_python_lsp import run_over_json_rpc as _run_over_json_rpc
from vscode_common_python_lsp import shutdown_json_rpc

RUNNER_SCRIPT = str(pathlib.Path(__file__).parent / "lsp_runner.py")

__all__ = [
    "JsonRpc",
    "RpcRunResult",
    "StreamClosedException",
    "create_json_rpc",
    "get_or_start_json_rpc",
    "run_over_json_rpc",
    "shutdown_json_rpc",
    "RUNNER_SCRIPT",
]


def create_json_rpc(readable, writable) -> JsonRpc:
    """Creates JSON-RPC wrapper for the readable and writable streams."""
    return JsonRpc(readable, writable)


def get_or_start_json_rpc(
    workspace: str,
    interpreter: Sequence[str],
    cwd: str,
    env: Optional[dict[str, str]] = None,
) -> Union[JsonRpc, None]:
    """Gets an existing JSON-RPC connection or starts one and return it."""
    return _get_or_start_json_rpc(workspace, interpreter, cwd, RUNNER_SCRIPT, env)


def run_over_json_rpc(
    workspace: str,
    interpreter: Sequence[str],
    module: str,
    argv: Sequence[str],
    use_stdin: bool,
    cwd: str,
    source: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> RpcRunResult:
    """Uses JSON-RPC to execute a command."""
    return _run_over_json_rpc(
        workspace=workspace,
        interpreter=interpreter,
        module=module,
        argv=argv,
        use_stdin=use_stdin,
        cwd=cwd,
        runner_script=RUNNER_SCRIPT,
        source=source,
        env=env,
        timeout=timeout,
    )
