# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Runner to use when running under a different interpreter.
"""

import pathlib
import runpy
import sys

# Ensure that we can import LSP libraries, and other bundled libraries
sys.path.append(str(pathlib.Path(__file__).parent.parent / "libs"))
sys.argv = sys.argv[1:]
runpy.run_module(sys.argv[0], run_name="__main__")
