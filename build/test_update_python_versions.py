# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime

import pytest
import update_python_versions

NOW = datetime.datetime(2026, 8, 2, tzinfo=datetime.timezone.utc)


def release(name, release_date, **overrides):
    result = {
        "name": name,
        "release_date": release_date,
        "is_published": True,
        "pre_release": True,
        "version": 3,
    }
    result.update(overrides)
    return result


def test_latest_release_candidate_filters_and_orders_releases():
    releases = [
        release("Python 3.9.0rc10", "2020-08-01T00:00:00Z"),
        release("Python 3.10.0rc2", "2021-08-01T00:00:00Z"),
        release("Python 3.11.0b1", "2022-05-01T00:00:00Z"),
        release("Python 3.11.0rc1", "2027-08-01T00:00:00Z"),
        release("Python 3.12.0rc1", "2024-08-01T00:00:00Z", is_published=False),
    ]

    assert update_python_versions.latest_release_candidate(releases, NOW) == "3.10"


@pytest.mark.parametrize("release_date", [None, "invalid", "2026-08-01"])
def test_latest_release_candidate_rejects_malformed_release_date(release_date):
    releases = [release("Python 3.15.0rc1", release_date)]

    with pytest.raises(ValueError, match="release_date"):
        update_python_versions.latest_release_candidate(releases, NOW)


@pytest.mark.parametrize(
    "versions",
    ["['3.10', '3.11', '3.12']", "['3.10.9', '3.11-dev', '3.12.0rc1']"],
)
def test_configured_versions(tmp_path, versions):
    workflow = tmp_path / "pr-check.yml"
    workflow.write_text(f"matrix:\n  python: {versions}\n", encoding="utf-8")

    assert update_python_versions.configured_versions(workflow) == {
        "3.10",
        "3.11",
        "3.12",
    }


def test_configured_versions_requires_one_matrix(tmp_path):
    workflow = tmp_path / "pr-check.yml"
    workflow.write_text("matrix: {}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Expected one"):
        update_python_versions.configured_versions(workflow)


@pytest.mark.parametrize(
    "pr_version, push_version, expected",
    [
        ("3.14", "3.14", "3.15"),
        ("3.15", "3.14", "3.15"),
        ("3.14", "3.15", "3.15"),
        ("3.15", "3.15", None),
        ("3.15.1", "3.15.0-rc.2", None),
        ("3.150", "3.15", "3.15"),
    ],
)
def test_unconfigured_version(tmp_path, pr_version, push_version, expected):
    workflows = [tmp_path / name for name in ("pr-check.yml", "push-check.yml")]
    for workflow, version in zip(workflows, (pr_version, push_version)):
        workflow.write_text(f"python: ['{version}']\n", encoding="utf-8")
    releases = [release("Python 3.15.0rc1", "2026-08-01T00:00:00Z")]

    assert (
        update_python_versions.unconfigured_version(releases, workflows, NOW)
        == expected
    )


@pytest.mark.parametrize(
    "push_version, expected", [("3.14", "3.15\n"), ("3.15-dev", "")]
)
def test_main_checks_both_matrices(
    tmp_path, monkeypatch, capsys, push_version, expected
):
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "pr-check.yml").write_text("python: ['3.15.1']\n", encoding="utf-8")
    (workflow_dir / "push-check.yml").write_text(
        f"python: ['{push_version}']\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        update_python_versions,
        "__file__",
        str(tmp_path / "build" / "update_python_versions.py"),
    )
    monkeypatch.setattr(
        update_python_versions,
        "fetch_releases",
        lambda: [release("Python 3.15.0rc1", "2020-08-01T00:00:00Z")],
    )

    update_python_versions.main()

    assert capsys.readouterr().out == expected
