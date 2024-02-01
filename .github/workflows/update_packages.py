# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import random
import subprocess


def has_changes() -> bool:
    """Returns True if there are changes in the working tree."""
    print("Detecting changes")
    result = subprocess.run(["git", "diff", "--exit-code"], check=False)
    return result.returncode != 0


def main():
    random_name = "".join(random.choice("1234567890") for _ in range(9))
    branch_name = f"version-updater/pkg-{random_name}"

    print(f"Creating branch {branch_name}")
    subprocess.run(["git", "switch", "--create", branch_name], check=True)

    print("Update packages")
    subprocess.run(["nox", "--session", "update_packages"], check=True)

    if not has_changes():
        print("No changes detected, exiting")
        return

    print("Committing changes")
    subprocess.run(["git", "add", "--all", "."], check=True)

    subprocess.run(
        ["git", "commit", "-m", "Update extension dependencies"],
        check=True,
    )


if __name__ == "__main__":
    main()
