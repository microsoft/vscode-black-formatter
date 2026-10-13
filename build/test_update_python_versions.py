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


def test_configured_versions(tmp_path):
    workflow = tmp_path / "pr-check.yml"
    workflow.write_text(
        "matrix:\n  python: ['3.10', '3.11', '3.12']\n", encoding="utf-8"
    )

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
    "matrix, expected",
    [
        ("python: ['3.14']\n", "3.15"),
        ("python: ['3.14', '3.15']\n", None),
    ],
)
def test_unconfigured_version(tmp_path, matrix, expected):
    workflow = tmp_path / "pr-check.yml"
    workflow.write_text(matrix, encoding="utf-8")
    releases = [release("Python 3.15.0rc1", "2026-08-01T00:00:00Z")]

    assert (
        update_python_versions.unconfigured_version(releases, workflow, NOW) == expected
    )
