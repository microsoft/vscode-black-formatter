# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime
import json
import pathlib
import re
import urllib.request

RELEASE_CYCLE_URL = "https://peps.python.org/api/release-cycle.json"
RELEASED_STATUSES = {"bugfix", "security"}
VERSION_MATRIX = re.compile(
    r"^\s*python:\s*\[(?P<versions>[^\]\n]+)\]\s*$", re.MULTILINE
)


def fetch_release_cycle():
    """Fetch Python release lifecycle data from the PEP API."""
    request = urllib.request.Request(
        RELEASE_CYCLE_URL, headers={"User-Agent": "vscode-python-tools-version-check"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def latest_released_version(release_cycle, today=None):
    """Return the newest released Python 3 series."""
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    versions = []
    for version, details in release_cycle.items():
        if (
            not re.fullmatch(r"3\.\d+", version)
            or not isinstance(details, dict)
            or details.get("status") not in RELEASED_STATUSES
        ):
            continue
        try:
            release_date = datetime.date.fromisoformat(details["first_release"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid first_release for Python {version}") from exc
        if release_date <= today:
            versions.append(version)
    if not versions:
        raise ValueError("The release cycle did not contain a released Python version")
    return max(versions, key=lambda version: tuple(map(int, version.split("."))))


def configured_versions(workflow):
    """Return the Python versions in the workflow's test matrix."""
    matches = VERSION_MATRIX.findall(workflow.read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one Python version matrix in {workflow}")
    versions = set(re.findall(r"['\"](3\.\d+)['\"]", matches[0]))
    if not versions:
        raise RuntimeError(f"No Python versions found in {workflow}")
    return versions


def main():
    latest = latest_released_version(fetch_release_cycle())
    workflow = pathlib.Path(__file__).parent.parent / ".github/workflows/pr-check.yml"
    if latest not in configured_versions(workflow):
        print(latest)


if __name__ == "__main__":
    main()
