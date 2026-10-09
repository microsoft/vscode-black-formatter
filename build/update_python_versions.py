# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime
import json
import pathlib
import re
import urllib.request

DOWNLOADS_URL = (
    "https://www.python.org/api/v2/downloads/release/"
    "?is_published=true&pre_release=true&version=3"
)
RC_NAME = re.compile(r"Python (?P<series>3\.\d+)\.0rc(?P<candidate>\d+)")
VERSION_MATRIX = re.compile(
    r"^\s*python:\s*\[(?P<versions>[^\]\n]+)\]\s*$", re.MULTILINE
)


def fetch_releases():
    """Fetch published Python prereleases from Python.org."""
    request = urllib.request.Request(
        DOWNLOADS_URL, headers={"User-Agent": "vscode-python-tools-version-check"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def latest_release_candidate(releases, now=None):
    """Return the newest Python 3 series with a published release candidate."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    candidates = []
    for release in releases:
        if (
            not isinstance(release, dict)
            or release.get("is_published") is not True
            or release.get("pre_release") is not True
            or release.get("version") != 3
            or not isinstance(release.get("name"), str)
        ):
            continue
        match = RC_NAME.fullmatch(release["name"])
        if not match:
            continue
        try:
            release_date = datetime.datetime.fromisoformat(
                release["release_date"].replace("Z", "+00:00")
            )
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid release_date for {release['name']}") from exc
        if release_date.tzinfo is None:
            raise ValueError(f"Missing timezone in release_date for {release['name']}")
        if release_date <= now:
            series = match.group("series")
            candidates.append(
                (
                    tuple(map(int, series.split("."))),
                    int(match.group("candidate")),
                    series,
                )
            )
    if not candidates:
        raise ValueError("The downloads API did not contain a released Python RC")
    return max(candidates)[2]


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
    latest = latest_release_candidate(fetch_releases())
    workflow = pathlib.Path(__file__).parent.parent / ".github/workflows/pr-check.yml"
    if latest not in configured_versions(workflow):
        print(latest)


if __name__ == "__main__":
    main()
