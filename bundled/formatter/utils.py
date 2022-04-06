# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Utility functions and classes for use with LSP.
"""


import contextlib
import importlib
import io
import os.path
import runpy
import site
import subprocess
import sys
from typing import Any, List, Sequence

from packaging.version import parse


def as_list(content):
    """Ensures we always get a list"""
    if isinstance(content, (list, tuple)):
        return content
    return [content]


_site_paths = tuple(
    [
        os.path.normcase(os.path.normpath(p))
        for p in (as_list(site.getsitepackages()) + as_list(site.getusersitepackages()))
    ]
)


def is_stdlib_file(file_path):
    """Return True if the file belongs to standard library."""
    return os.path.normcase(os.path.normpath(file_path)).startswith(_site_paths)


def _get_formatter_version_by_path(settings_path: List[str]) -> str:
    """Extract version number when using path to run formatter."""
    try:
        args = settings_path + ["--version"]
        result = subprocess.run(
            args,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except SystemExit:
        pass

    # This is to just get the version number:
    # > black --version
    # black, 22.3.0 (compiled: yes)
    #        ^----^ this is all we want
    first_line = result.stdout.splitlines(keepends=False)[0]
    return first_line.split(" ")[1]


def _get_formatter_version_by_module(module):
    """Extracts formatter version when using the module to format."""
    imported = importlib.import_module(module)
    return imported.__getattr__("__version__")


def get_formatter_options_by_version(raw_options, formatter_path):
    """Gets the settings based on the version of the formatter."""
    name = raw_options["name"]
    module = raw_options["module"]

    default = {
        "name": name,
        "module": module,
        "args": raw_options["patterns"]["default"]["args"],
    }

    options = default

    if len(raw_options["patterns"]) == 1:
        return options

    try:
        version = parse(
            _get_formatter_version_by_path(formatter_path)
            if len(formatter_path) > 0
            else _get_formatter_version_by_module(module)
        )
    except Exception:
        return options

    for ver in filter(lambda k: not k == "default", raw_options["patterns"].keys()):
        if version >= parse(ver):
            options = {
                "name": name,
                "module": module,
                "args": raw_options["patterns"][ver]["args"],
            }

    return options


class FormatterResult:
    """Object to hold result from running formatter."""

    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr


class CustomIO(io.TextIOWrapper):
    """Custom stream object to replace stdio."""

    name = None

    def __init__(self, name, encoding="utf-8", newline=None):
        self._buffer = io.BytesIO()
        self._buffer.name = name
        super().__init__(self._buffer, encoding=encoding, newline=newline)

    def close(self):
        """Provide this close method which is used by some formatters."""
        # This is intentionally empty.

    def get_value(self) -> str:
        """Returns value from the buffer as string."""
        self.seek(0)
        return self.read()


@contextlib.contextmanager
def substitute_attr(obj: Any, attribute: str, new_value: Any):
    """Manage object attributes context when using runpy.run_module()."""
    old_value = getattr(obj, attribute)
    setattr(obj, attribute, new_value)
    yield
    setattr(obj, attribute, old_value)


@contextlib.contextmanager
def redirect_io(stream: str, new_stream):
    """Redirect stdio streams to a custom stream."""
    old_stream = getattr(sys, stream)
    setattr(sys, stream, new_stream)
    yield
    setattr(sys, stream, old_stream)


def run_module(
    module: str, argv: Sequence[str], use_stdin: bool, source: str = None
) -> FormatterResult:
    """Runs formatter as a module."""
    str_output = CustomIO("<stdout>", encoding="utf-8")
    str_error = CustomIO("<stderr>", encoding="utf-8")

    try:
        with substitute_attr(sys, "argv", argv):
            with redirect_io("stdout", str_output):
                with redirect_io("stderr", str_error):
                    if use_stdin and source:
                        str_input = CustomIO("<stdin>", encoding="utf-8", newline="\n")
                        with redirect_io("stdin", str_input):
                            str_input.write(source)
                            str_input.seek(0)
                            runpy.run_module(
                                module, run_name="__main__", alter_sys=True
                            )
                    else:
                        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit:
        pass

    return FormatterResult(str_output.get_value(), str_error.get_value())


def run_path(
    argv: Sequence[str], use_stdin: bool, source: str = None
) -> FormatterResult:
    """Runs formatter as an executable."""
    if use_stdin:
        with subprocess.Popen(
            argv,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        ) as process:
            return FormatterResult(*process.communicate(input=source))
    else:
        result = subprocess.run(
            argv,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return FormatterResult(result.stdout, result.stderr)
