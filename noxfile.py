# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
All the action we need during build
"""

import json
import pathlib
import re

import nox


@nox.session(python="3.7")
def install_bundled_libs(session):
    """Installs the libraries that will be bundled with the extension."""
    session.install("wheel")
    session.install(
        "-t",
        "./bundled/libs",
        "--no-cache-dir",
        "--implementation",
        "py",
        "--no-deps",
        "--upgrade",
        "-r",
        "./requirements.txt",
    )


@nox.session()
def tests(session):
    """Runs all the tests for the extension."""
    session.install("-r", "src/test/python_tests/requirements.txt")
    session.run("pytest", "src/test/python_tests")

    session.install("freezegun")
    session.run("pytest", "build")


@nox.session()
def lint(session):
    """Runs linter and formater checks on python files."""
    session.install("-r" "./requirements.txt")
    session.install("-r", "src/test/python_tests/requirements.txt")

    session.install("flake8")
    session.run("flake8", "./bundled/formatter")
    session.run(
        "flake8",
        "--extend-exclude",
        "./src/test/python_tests/test_data",
        "./src/test/python_tests",
    )
    session.run("flake8", "noxfile.py")

    # check formatting using black
    session.install("black")
    session.run("black", "--check", "./bundled/formatter")
    session.run("black", "--check", "./src/test/python_tests")
    session.run("black", "--check", "noxfile.py")

    # check import sorting using isort
    session.install("isort")
    session.run("isort", "--check", "./bundled/formatter")
    session.run("isort", "--check", "./src/test/python_tests")
    session.run("isort", "--check", "noxfile.py")


@nox.session()
def update_build_number(session):
    """Updates buildnumber for the extension."""
    if len(session.posargs) == 0:
        session.log("No updates to package version")
        return

    package_json_path = pathlib.Path(__file__).parent / "package.json"
    session.log(f"Reading package.json at: {package_json_path}")

    package_json = json.loads(package_json_path.read_text(encoding="utf-8"))

    parts = re.split("\\.|-", package_json["version"])
    major, minor = parts[:2]

    version = f"{major}.{minor}.{session.posargs[0]}"
    version = version if len(parts) == 3 else f"{version}-{''.join(parts[3:])}"

    session.log(f"Updating version from {package_json['version']} to {version}")
    package_json["version"] = version
    package_json_path.write_text(json.dumps(package_json, indent=4), encoding="utf-8")


@nox.session()
def validate_readme(session):
    """Ensures the formatter version in 'requirements.txt' matches 'readme.md'."""
    requirements_file = pathlib.Path(__file__).parent / "requirements.txt"
    readme_file = pathlib.Path(__file__).parent / "README.md"

    lines = requirements_file.read_text(encoding="utf-8").splitlines(keepends=False)
    formatter_ver = list(line for line in lines if line.startswith("black"))[0]
    name, version = formatter_ver.split(" ")[0].split("==")

    session.log(f"Looking for {name}={version} in README.md")
    content = readme_file.read_text(encoding="utf-8")
    if f"{name}={version}" not in content:
        raise ValueError(f"Formatter info {name}={version} was not found in README.md.")
    session.log(f"FOUND {name}={version} in README.md")
