# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Utility functions for use with tests.
"""
import contextlib
import json
import os
import pathlib
import platform
import random
import subprocess
import sys
from typing import Any, List

import lsprotocol.converters as cv
import lsprotocol.types as lsp

from .constants import PROJECT_ROOT


def normalizecase(path: str) -> str:
    """Fixes 'file' uri or path case for easier testing in windows."""
    if platform.system() == "Windows":
        return path.lower()
    return path


def as_uri(path: str) -> str:
    """Return 'file' uri as string."""
    return normalizecase(pathlib.Path(path).as_uri())


@contextlib.contextmanager
def python_file(contents: str, root: pathlib.Path):
    try:
        basename = (
            "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(9))
            + ".py"
        )
        fullpath = root / basename
        fullpath.write_text(contents, encoding="utf-8")
        yield fullpath
    finally:
        os.unlink(str(fullpath))


@contextlib.contextmanager
def install_packages(packages: List[str]):
    try:
        subprocess.run([sys.executable, "-m", "pip", "install"] + packages, check=True)
        yield
    finally:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y"] + packages, check=True
            )
        except Exception:
            pass


def get_server_info_defaults():
    """Returns server info from package.json"""
    package_json_path = PROJECT_ROOT / "package.json"
    package_json = json.loads(package_json_path.read_text())
    return package_json["serverInfo"]


def get_initialization_options():
    """Returns initialization options from package.json"""
    package_json_path = PROJECT_ROOT / "package.json"
    package_json = json.loads(package_json_path.read_text())

    server_info = package_json["serverInfo"]
    server_id = f"{server_info['module']}-formatter"

    properties = package_json["contributes"]["configuration"]["properties"]
    setting = {}
    for prop in properties:
        name = prop[len(server_id) + 1 :]
        value = properties[prop]["default"]
        setting[name] = value

    setting["workspace"] = as_uri(str(PROJECT_ROOT))
    setting["interpreter"] = []
    setting["cwd"] = str(PROJECT_ROOT)

    return {"settings": [setting], "globalSettings": setting}


def apply_text_edits(text: str, text_edits: List[lsp.TextEdit]) -> str:
    if not text_edits:
        return text

    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))

    for text_edit in reversed(text_edits):
        start_offset = (
            offsets[text_edit.range.start.line] + text_edit.range.start.character
        )
        end_offset = offsets[text_edit.range.end.line] + text_edit.range.end.character
        text = text[:start_offset] + text_edit.new_text + text[end_offset:]
    return text


def destructure_text_edits(text_edits: List[Any]) -> List[lsp.TextEdit]:
    """Converts text edits from the language server to the format used by the test client."""
    converter = cv.get_converter()
    return [converter.structure(text_edit, lsp.TextEdit) for text_edit in text_edits]
