# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import argparse
import json
import pathlib
import re
import urllib.request

RELEASE_CYCLE_URL = "https://peps.python.org/api/release-cycle.json"
SUPPORTED_STATUSES = {"bugfix", "security"}


def supported_versions(release_cycle):
    """Return released Python 3 versions that are still maintained."""
    versions = [
        version
        for version, details in release_cycle.items()
        if re.fullmatch(r"3\.\d+", version)
        and isinstance(details, dict)
        and details.get("status") in SUPPORTED_STATUSES
    ]
    if not versions:
        raise ValueError("The release cycle did not contain supported Python versions")
    return sorted(versions, key=lambda version: tuple(map(int, version.split("."))))


def fetch_release_cycle():
    """Fetch Python release lifecycle data from the PEP API."""
    request = urllib.request.Request(
        RELEASE_CYCLE_URL, headers={"User-Agent": "vscode-python-tools-version-check"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _replace(path, pattern, replacement, expected=1):
    content = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count != expected:
        raise RuntimeError(
            f"Expected {expected} version field(s) in {path}, found {count}"
        )
    path.write_text(updated, encoding="utf-8")


def update_repository(root, versions):
    """Update every supported-Python reference in an extension repository."""
    minimum = versions[0]
    minor = minimum.split(".")[1]
    matrix = ", ".join(f"'{version}'" for version in versions)

    for relative_path in (
        ".github/workflows/pr-check.yml",
        ".github/workflows/push-check.yml",
    ):
        path = root / relative_path
        _replace(
            path,
            r"^(\s*PYTHON_VERSION:\s*)'3\.\d+'(.*)$",
            rf"\g<1>'{minimum}'\g<2>",
        )
        _replace(
            path,
            r"^(\s*python:\s*)\[[^\]\n]+\](\s*)$",
            rf"\g<1>[{matrix}]\g<2>",
        )

    azure_pipelines = [
        root / "build" / filename
        for filename in (
            "azure-pipeline.stable.yml",
            "azure-pipeline.pre-release.yml",
            "azure-devdiv-pipeline.stable.yml",
            "azure-devdiv-pipeline.pre-release.yml",
        )
        if (root / "build" / filename).exists()
    ]
    updated_pipelines = 0
    for path in azure_pipelines:
        content = path.read_text(encoding="utf-8")
        if re.search(r"^\s*PYTHON_VERSION:", content, flags=re.MULTILINE):
            pattern = r"^(\s*PYTHON_VERSION:\s*)'3\.\d+'(.*)$"
        elif "name: PythonVersion" in content:
            pattern = (
                r"^(\s*-\s+name:\s+PythonVersion\s*\n" r"\s*value:\s*)'3\.\d+'(.*)$"
            )
        else:
            continue
        _replace(path, pattern, rf"\g<1>'{minimum}'\g<2>")
        updated_pipelines += 1
    if updated_pipelines < 2:
        raise RuntimeError("Fewer than two Azure pipeline versions were found")

    constants = root / "src/common/constants.ts"
    content = constants.read_text(encoding="utf-8")
    if "MINIMUM_PYTHON_MINOR" in content:
        pattern = r"^(export const MINIMUM_PYTHON_MINOR = )\d+(;.*)$"
        replacement = rf"\g<1>{minor}\g<2>"
    else:
        pattern = r"(minimumPythonVersion:\s*\{\s*major:\s*3,\s*minor:\s*)\d+"
        replacement = rf"\g<1>{minor}"
    _replace(constants, pattern, replacement)

    noxfile = root / "noxfile.py"
    content = noxfile.read_text(encoding="utf-8")
    if "MINIMUM_PYTHON_VERSION" in content:
        _replace(
            noxfile,
            r'^(MINIMUM_PYTHON_VERSION\s*=\s*)"3\.\d+"(.*)$',
            rf'\g<1>"{minimum}"\g<2>',
        )
    else:
        count = len(re.findall(r'@nox\.session\(python="3\.\d+"\)', content))
        if not count:
            raise RuntimeError(f"No Python session versions were found in {noxfile}")
        _replace(
            noxfile,
            r'(@nox\.session\(python=)"3\.\d+"(\))',
            rf'\g<1>"{minimum}"\g<2>',
            expected=count,
        )

    _replace(
        root / "runtime.txt",
        r"^(python-)3\.\d+\.\d+(\s*)$",
        rf"\g<1>{minimum}.0\g<2>",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Update CI to use all maintained Python versions."
    )
    parser.add_argument(
        "--release-cycle-file",
        type=pathlib.Path,
        help="Read release lifecycle JSON from a local file instead of the PEP API.",
    )
    args = parser.parse_args()
    if args.release_cycle_file:
        release_cycle = json.loads(args.release_cycle_file.read_text(encoding="utf-8"))
    else:
        release_cycle = fetch_release_cycle()
    versions = supported_versions(release_cycle)
    print(f"Maintained Python versions: {', '.join(versions)}")
    update_repository(pathlib.Path(__file__).parent.parent, versions)


if __name__ == "__main__":
    main()
