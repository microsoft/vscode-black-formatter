# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime
import json
import pathlib
from typing import Tuple, Union

EXT_ROOT = pathlib.Path(__file__).parent.parent.parent
PACKAGE_JSON_PATH = EXT_ROOT / "package.json"


def is_even(v: Union[int, str]) -> bool:
    """Returns True if `v` is even."""
    return not int(v) % 2


def parse_version(version: str) -> Tuple[int, int, int, str]:
    """Parse a version string into a tuple of version parts."""
    major, minor, parts = version.split(".", maxsplit=2)
    try:
        micro, suffix = parts.split("-", maxsplit=1)
    except ValueError:
        micro = parts
        suffix = ""
    return int(major), int(minor), int(micro), suffix


def main(package_json: pathlib.Path) -> None:
    package = json.loads(package_json.read_text(encoding="utf-8"))

    major, minor, micro, _ = parse_version(package["version"])

    if is_even(minor):
        year = datetime.datetime.now().year
        if int(major) < year:
            major = year
        version = f"{major}.{int(minor)+1}.{micro}-dev"
        package["version"] = version

        # Overwrite package.json with new data add a new-line at the end of the file.
        package_json.write_text(
            json.dumps(package, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main(PACKAGE_JSON_PATH)
