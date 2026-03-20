---
description: >
  Scheduled and on-demand check to detect unsynced changes from the
  upstream microsoft/vscode-python-tools-extension-template. Compares
  recent template PRs against this repo's files and opens an issue
  for each PR whose changes are not yet present.
on:
  schedule:
    - cron: daily
  workflow_dispatch:
permissions:
  contents: read
  pull-requests: read
  issues: read
tools:
  github:
    toolsets: [repos, issues, pull_requests]
network:
  allowed: []
safe-outputs:
  create-issue:
    max: 10
steps:
- name: Checkout repository
  uses: actions/checkout@v5
  with:
    persist-credentials: false
- name: Checkout template repo
  uses: actions/checkout@v5
  with:
    repository: microsoft/vscode-python-tools-extension-template
    path: template
    persist-credentials: false
---

# Extension Template Sync

You are an AI agent that monitors the **vscode-black-formatter** repository for unsynced changes from the upstream **[vscode-python-tools-extension-template](https://github.com/microsoft/vscode-python-tools-extension-template)**.

This workflow runs **daily on a schedule** and can also be **triggered manually**. It examines recently merged PRs in the template repository, compares the affected files against this repository, and opens an issue for each PR whose changes have not yet been incorporated.

## Context

This repository (`microsoft/vscode-black-formatter`) is a VS Code extension that wraps [Black](https://black.readthedocs.io/) for Python code formatting. It was scaffolded from the **vscode-python-tools-extension-template**, which provides shared infrastructure used by many Python-tool VS Code extensions.

Key **shared areas** that come from the template (and should be kept in sync):

- **TypeScript client code** (`src/common/`): settings resolution, server lifecycle, logging, Python discovery, status bar, utilities. Key files: `settings.ts`, `server.ts`, `utilities.ts`, `python.ts`, `logging.ts`, `setup.ts`, `status.ts`, `constants.ts`, `vscodeapi.ts`, `nullFormatter.ts`.
- **Python LSP server scaffolding** (`bundled/tool/`): `lsp_runner.py`, `lsp_jsonrpc.py`, `lsp_utils.py`, `lsp_edit_utils.py`, `lsp_io.py`.
- **Build & CI infrastructure**: `noxfile.py`, webpack config, ESLint config, Azure Pipelines definitions, GitHub Actions workflows.
- **Dependency management**: `requirements.in` / `requirements.txt`, bundled libs pattern.

Key **Black-specific areas** that are NOT expected to match the template:

- Tool-specific logic in `bundled/tool/lsp_server.py` (the template provides a skeleton; this repo has Black-specific implementation).
- Black-specific settings in `package.json` (`contributes.configuration`).
- Black-specific tests in `src/test/`.
- Any file that has been intentionally customized for this extension.

## Security

**CRITICAL**: Do not open, fetch, or follow any external URLs. Only use GitHub tools to read files, issues, and PRs within `microsoft/vscode-black-formatter` and `microsoft/vscode-python-tools-extension-template`.

## Your Task

### Step 1: Fetch recent template PRs

- List merged PRs in `microsoft/vscode-python-tools-extension-template` that were merged in the **last 48 hours**. Ignore any PRs merged before that window.
- If there are no recently merged PRs, stop.

### Step 2: For each merged PR, detect missing changes

For each merged template PR:

1. **Get the list of changed files and the diff.**
2. For each changed file, determine:
   - **Does a corresponding file exist in this repository?** Template files map by path (e.g., `src/common/server.ts` → `src/common/server.ts`).
   - **Is it a shared/template file or a tool-specific placeholder?** Refer to the shared vs. Black-specific areas listed in the Context section. Skip files that are entirely tool-specific.
   - **Compare the post-change version from the template PR (head) against the current file in this repository.** If the relevant changes introduced by the PR are already present in this repo's version, the PR is considered synced.

3. Classify the PR as:
   - **Synced**: All relevant changes from the PR are already present in this repository — skip it.
   - **Not applicable**: Changes are entirely template-placeholder-specific or affect files that don't exist here — skip it.
   - **Unsynced**: One or more relevant files in this repository do not yet contain the changes from the PR — proceed to Step 3.

### Step 3: Create an issue for each unsynced PR

For each unsynced template PR, use the `create-issue` safe output with:

- **Title**: `Template Sync: <Title of template PR>`
- **Body** structured as:

```
### 🔄 Template Sync Required

Changes from the upstream [vscode-python-tools-extension-template](https://github.com/microsoft/vscode-python-tools-extension-template) have not yet been incorporated into this repository.

#### Source PR
- [microsoft/vscode-python-tools-extension-template#<NUMBER> — <title>](https://github.com/microsoft/vscode-python-tools-extension-template/pull/<NUMBER>)

#### Summary
<Brief summary of what the template PR changed and why.>

#### Files with missing changes
<List each file in this repo that differs from the template PR's post-change version, with a brief note on what differs.>

#### Suggested fix
<For each file with missing changes, provide a concrete diff or code snippet showing the recommended changes to bring this repo in line with the template. Preserve any Black-specific customizations — only suggest changes for shared/template code. Use fenced diff blocks for clarity.>

#### Files skipped
<List any files from the template PR that were skipped because they are tool-specific or don't exist in this repo. Omit this section if none.>

---
🤖 This issue was auto-generated by the [`extension-template-sync`](.github/workflows/extension-template-sync.md) workflow.
```

**IMPORTANT**: When referencing a template PR anywhere in the issue (title, body, or comments), always use the **full URL** (e.g., `https://github.com/microsoft/vscode-python-tools-extension-template/pull/123`), never the shorthand `#123` or `microsoft/vscode-python-tools-extension-template#123`, to avoid confusion with this repository's own issues and PRs.

### Step 4: Handle edge cases

- **CI/workflow files** (`.github/workflows/`, Azure Pipelines): These are often shared — still assess relevance.
- **Large refactors**: Flag differing files and summarize in the issue body.
- **Dependency updates** (`requirements.in`, `requirements.txt`, `package.json`): Only consider shared dependencies, not tool-specific ones.
- **No unsynced changes found**: Do nothing — do not create any issues.
- **Duplicate prevention**: Before creating a new issue, search for existing issues **and** pull requests in this repository — both **open and closed** — with the same title pattern (`Template Sync: <title>`) or that reference the same template PR number. If a matching issue or PR already exists, skip it to avoid duplicates.
