# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

import freezegun
import pytest
import update_prerelease_version

TEST_DATETIME = "2023-01-01 01:23:45"


def create_package_json(directory, version):
    """Create `package.json` in `directory` with a specified version of `version`."""
    json_data = json.loads(
        update_prerelease_version.PACKAGE_JSON_PATH.read_text(encoding="utf-8")
    )
    package_json = directory / "package.json"
    json_data["version"] = version
    package_json.write_text(json.dumps(json_data, ensure_ascii=False), encoding="utf-8")
    return package_json


@pytest.mark.parametrize(
    "version, expected",
    [
        ("2022.20.0", (2023, 1, 0, "dev")),
        ("2022.20.0-rc", (2023, 1, 0, "dev")),
        ("2022.20.1", (2023, 1, 0, "dev")),
        ("2022.1.0", (2023, 1, 0, "dev")),
        ("2023.1.0", (2023, 1, 0, "dev")),
        ("2023.0.0", (2023, 1, 0, "dev")),
        ("2023.0.1-rc", (2023, 1, 0, "dev")),
        ("2023.0.1", (2023, 1, 0, "dev")),
        ("2023.20.1", (2023, 21, 0, "dev")),
        ("2023.20.1-rc", (2023, 21, 0, "dev")),
    ],
)
@freezegun.freeze_time(TEST_DATETIME)
def test_update_prerelease_version(tmp_path, version, expected):
    package_json = create_package_json(tmp_path, version)
    update_prerelease_version.main(package_json)
    package = json.loads(package_json.read_text(encoding="utf-8"))
    assert expected == update_prerelease_version.parse_version(package["version"])
