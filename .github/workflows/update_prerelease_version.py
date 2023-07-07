# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime
import json
import pathlib
from typing import Tuple

PACKAGE_JSON_PATH = pathlib.Path(__file__).parent.parent.parent / "package.json"


def parse_version(version: str) -> Tuple[int, int, int, str]:
    """Parse a version string into a tuple of version parts."""
    major, minor, parts = version.split(".", maxsplit=2)
    try:
        micro, suffix = parts.split("-", maxsplit=1)
    except ValueError:
        micro, _, suffix = parts.partition("-")
    return int(major), int(minor), int(micro), suffix


def update_version(package_json: pathlib.Path, new_version: str) -> None:
    package = json.loads(package_json.read_text(encoding="utf-8"))
    package["version"] = new_version
    print(f"Updating version to {new_version}")

    # Overwrite package.json with new data add a new-line at the end of the file.
    package_json.write_text(
        json.dumps(package, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def get_version(package_json: pathlib.Path) -> str:
    package = json.loads(package_json.read_text(encoding="utf-8"))
    return package["version"]


def main(package_json: pathlib.Path) -> None:
    major, minor, micro, suffix = parse_version(get_version(package_json))

    # Pre-release minor should always be odd
    new_minor = minor + (0 if minor % 2 else 1)

    # major version should always match the current year
    new_major = int(datetime.datetime.now().year)

    # reset minor version to 1 on year change
    new_minor = new_minor if major == new_major else 1

    if not (major, minor, micro, suffix) == (new_major, new_minor, 0, "dev"):
        version = f"{new_major}.{new_minor}.{0}-dev"
        update_version(package_json, version)


if __name__ == "__main__":
    main(PACKAGE_JSON_PATH)
