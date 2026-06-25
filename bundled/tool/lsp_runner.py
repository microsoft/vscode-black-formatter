# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Runner to use when running under a different interpreter.
"""

import os
import pathlib
import sys


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        else:
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
BUNDLE_DIR = pathlib.Path(__file__).parent.parent
# Always use bundled server files.
update_sys_path(os.fspath(BUNDLE_DIR / "tool"), "useBundled")
update_sys_path(
    os.fspath(BUNDLE_DIR / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)


from vscode_common_python_lsp import (  # noqa: E402
    JsonRpc,
    RunResult,
    run_message_loop,
    run_module,
)

RPC = JsonRpc(sys.stdin.buffer, sys.stdout.buffer)
# run_message_loop handles the sys.path manipulation internally:
# it wraps each run_module call with substitute_attr(sys, "path", [""] + sys.path[:])
# so tool modules can import from CWD.
run_message_loop(RPC, run_module, RunResult)
