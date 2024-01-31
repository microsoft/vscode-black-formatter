# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import pathlib
import os
import random
import subprocess


def get_next_odd_number(number: int) -> int:
    """Returns the next odd number."""
    return number + 1 if number % 2 == 0 else number + 2


def get_next_even_number(number: int) -> int:
    """Returns the next even number."""
    return number if number % 2 == 0 else number + 1


def main():
    package_json = pathlib.Path("package.json")
    package = json.loads(package_json.read_text(encoding="utf-8"))
    version = package["version"].split(".")
    release_type = os.getenv("RELEASE_TYPE", None)
    if release_type == "release":
        version[1] = str(get_next_even_number(int(version[1])))
        version[2] = "0"
    elif release_type == "pre-release":
        version[1] = str(get_next_odd_number(int(version[2])))
        version[2] = "0-dev"
    elif release_type == "hotfix":
        version[2] = str(int(version[2]) + 1)
    else:
        print("Unknown release type, skipping version update.")
        exit(1)

    package["version"] = ".".join(version)
    random_name = "".join(random.choice("1234567890") for _ in range(9))
    branch_name = f"version-updater/ext-{package['version']}-{random_name}"

    print(f"Creating branch {branch_name}")
    subprocess.run(["git", "switch", "--create", branch_name], check=True)

    print(f"Updating build TO: {package['version']}")
    package_json.write_text(
        json.dumps(package, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print("Running npm install")
    subprocess.run(["npm", "install"], check=True, shell=True)

    print("Committing changes")
    subprocess.run(["git", "add", "package.json"], check=True)
    subprocess.run(["git", "add", "package-lock.json"], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Update extension version to {package['version']}"],
        check=True,
    )

    print("Creating a PR")
    subprocess.run(
        ["gh", "pr", "create", "--fill", "--base", "main", "--head", branch_name],
        check=True,
    )


if __name__ == "__main__":
    main()
