# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""IO handling to communicate with LSP client."""

import argparse
import contextlib
import socket
import sys
from typing import Optional, Sequence


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--socket", type=int, default=None)
    parser.add_argument("--pipe", type=str, default=None)
    parser.add_argument("--clientProcessId", type=int, default=None)

    return parser.parse_args(args)


@contextlib.contextmanager
def use_pipe(pipe_name: str):
    if sys.platform == "win32":
        with open(pipe_name, "r+b") as f:
            yield (f, f)
    else:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(pipe_name)
        f = sock.makefile("rwb")
        yield (f, f)
