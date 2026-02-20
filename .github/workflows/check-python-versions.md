---
description: >
  Annual check of the latest supported Python versions from peps.python.org.
  Creates a PR to add newly released versions and remove end-of-life versions
  from CI workflows, actions, Azure Pipelines, and source code.
strict: false
engine:
  id: copilot
on:
  schedule:
    - cron: "0 12 15 10 *"
  workflow_dispatch:
permissions:
  pull-requests: read
tools:
  web-fetch:
  github:
    toolsets: [default]
network:
  allowed:
    - defaults
    - python
    - "peps.python.org"
safe-outputs:
  create-pull-request:
    draft: true
  noop:
    max: 1
---

# Annual Python Version Update

You are an AI agent that checks the latest supported Python versions and updates this repository's CI configuration to stay current.

## Context

This repository is a VS Code extension that supports all actively maintained Python versions. Python releases a new minor version every October (PEP 602). This workflow runs annually after the October release cycle to incorporate new versions and drop end-of-life ones.

## Your Task

### Step 1: Fetch current supported Python versions

Fetch `https://peps.python.org/api/release-cycle.json` and parse the JSON response.

Each key in the JSON object is a Python version (e.g., `"3.13"`), and its value contains a `"status"` field. Extract all versions where the status is **`security`**, **`bugfix`**, or **`feature`**. Ignore versions with status **`end-of-life`** (or any other status).

Build a sorted list of supported versions (e.g., `['3.10', '3.11', '3.12', '3.13', '3.14']`). The lowest is the minimum supported version, the highest is the newest.

If fetching fails, call the `noop` safe output with the error and stop.

### Step 2: Update all files

Compare the supported versions against what the repo currently has (see the `matrix.python` list and `PYTHON_VERSION` env var in `.github/workflows/pr-check.yml`). If everything is already up to date, call the `noop` safe output and stop.

Update the following files with the new version information. For each file, the specific changes are described below.

#### 2a. GitHub Actions workflows

**`.github/workflows/pr-check.yml`** and **`.github/workflows/push-check.yml`**:

- Update the `PYTHON_VERSION` env variable if the minimum version changed
- Update the `matrix.python` list to match `supported_versions`
  - The list format is: `['3.X', '3.Y', '3.Z']` (single-quoted, comma-separated)

#### 2b. Azure Pipelines

**`build/azure-pipeline.stable.yml`**, **`build/azure-pipeline.pre-release.yml`**, **`build/azure-devdiv-pipeline.stable.yml`**, and **`build/azure-devdiv-pipeline.pre-release.yml`**:

- Update the `PythonVersion` variable value if the minimum version changed
  - Look for the YAML block: `- name: PythonVersion` / `value: '3.X'`

#### 2c. Source code

**`src/common/constants.ts`**:

- Update `PYTHON_MAJOR` and `PYTHON_MINOR` constants if the minimum version changed
  - `export const PYTHON_MAJOR = 3;`
  - `export const PYTHON_MINOR = <new_minor>;`

#### 2d. Nox sessions

**`noxfile.py`**:

- Update the `python=` parameter in `@nox.session(python="3.X")` decorators if the minimum version changed
  - There are two sessions with explicit Python versions: `install_bundled_libs` and `setup`

#### 2e. Runtime file

**`runtime.txt`**:

- Update the Python version if the minimum version changed
  - Format: `python-3.X.0` (use `.0` as the patch version placeholder since the exact patch version is not critical here; if the current file has a specific patch version, keep the format but update the minor version)

### Step 3: Create a pull request

Create a pull request with all the changes using the `create-pull-request` safe output.

- **Branch name**: `update-python-versions-<year>` (e.g., `update-python-versions-2026`)
- **Title**: `Update supported Python versions`
- **Body**: Include:
  - A summary of what changed (versions added/removed, minimum version update if applicable)
  - A link to https://peps.python.org/api/release-cycle.json as the source of truth
  - The list of files modified
  - A note to verify CI passes before merging

## Guidelines

- Only modify version numbers; do not change the structure or formatting of any file
- Preserve the quoting style in YAML files (single quotes around version strings)
- Keep the matrix list sorted in ascending version order
- The `PYTHON_VERSION` / `PythonVersion` / `PYTHON_MINOR` values represent the **minimum** supported version and should only be updated if that version has gone end-of-life
- Do not include pre-release Python versions (status `feature` or `prerelease`) in any updates