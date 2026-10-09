# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import update_python_versions


def _write(root, relative_path, content):
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_repository(root):
    for workflow in ("pr-check.yml", "push-check.yml"):
        _write(
            root,
            f".github/workflows/{workflow}",
            "env:\n  PYTHON_VERSION: '3.10' # Minimum\n"
            "strategy:\n  matrix:\n    python: ['3.10', '3.11']\n",
        )
    _write(
        root,
        "build/azure-pipeline.stable.yml",
        "variables:\n  - name: PythonVersion\n    value: '3.10'\n",
    )
    _write(
        root,
        "build/azure-pipeline.pre-release.yml",
        "variables:\n  - name: PythonVersion\n    value: '3.10'\n",
    )
    _write(
        root,
        "src/common/constants.ts",
        "minimumPythonVersion: { major: 3, minor: 10 },\n",
    )
    _write(
        root,
        "noxfile.py",
        '@nox.session(python="3.10")\n@nox.session(python="3.10")\n',
    )
    _write(root, "runtime.txt", "python-3.10.19\n")


def test_supported_versions_excludes_unreleased_and_eol_versions():
    release_cycle = {
        "3.10": {"status": "end-of-life"},
        "3.11": {"status": "security"},
        "3.12": {"status": "bugfix"},
        "3.13": {"status": "feature"},
    }

    assert update_python_versions.supported_versions(release_cycle) == [
        "3.11",
        "3.12",
    ]


def test_update_repository(tmp_path):
    _create_repository(tmp_path)

    update_python_versions.update_repository(tmp_path, ["3.11", "3.12"])

    pr_check = (tmp_path / ".github/workflows/pr-check.yml").read_text()
    assert "PYTHON_VERSION: '3.11' # Minimum" in pr_check
    assert "python: ['3.11', '3.12']" in pr_check
    assert "value: '3.11'" in (tmp_path / "build/azure-pipeline.stable.yml").read_text()
    assert "minor: 11" in (tmp_path / "src/common/constants.ts").read_text()
    assert (tmp_path / "noxfile.py").read_text().count('python="3.11"') == 2
    assert (tmp_path / "runtime.txt").read_text() == "python-3.11.0\n"


def test_update_repository_fails_when_a_version_field_is_missing(tmp_path):
    _create_repository(tmp_path)
    (tmp_path / "runtime.txt").write_text("invalid\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="runtime.txt"):
        update_python_versions.update_repository(tmp_path, ["3.11", "3.12"])
