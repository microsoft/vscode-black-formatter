# Formatter extension for Visual Studio Code using the Black formatter

A Visual Studio Code extension with support for the Black formatter. The extension ships with `black=26.5.1`.

> Note: The minimum version of Black this extension supports is `26.5.1`.

This extension includes support for all [actively supported versions](https://devguide.python.org/#status-of-python-branches) of the Python language.

For more information on the Black formatter, see https://black.readthedocs.io/en/stable/.

## Usage and Features

The Black extension for Visual Studio Code provides formatting support for your Python files. Check out the [Settings section](#settings) for more details on how to customize the extension.

-   **Integrated formatting**: Once this extension is installed in VS Code, Black will be automatically available as a formatter for Python. This is because the extension ships with a Black binary. You can ensure VS Code uses Black by default for all your Python files by setting the following in your User settings (**View** > **Command Palette...** and run **Preferences: Open User Settings (JSON)**):

    ```json
      "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
      }
    ```

-   **Format on save**: Automatically format your Python files on save by setting the `editor.formatOnSave` setting to `true` and the `editor.defaultFormatter` setting to `ms-python.black-formatter`. You can also enable format on save for Python files only by adding the following to your settings:

    ```json
      "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true
      }
    ```

-   **Customize Black**: You can customize the behavior of Black by setting the `black-formatter.args` setting.

-   **Keyboard Shortcuts**: The code formatting is available in Visual Studio Code through the following keyboard shortcuts:
    - On Windows: Shift + Alt + F
    - On Mac: Shift + Option + F
    - On Linux: Ctrl + Shift + I

### Disabling formatting with Black

If you want to disable Black formatter, you can [disable this extension](https://code.visualstudio.com/docs/editor/extension-marketplace#_disable-an-extension) per workspace in Visual Studio Code.

## Settings

There are several settings you can configure to customize the behavior of this extension.

<table>
  <thead>
    <tr>
      <th>Settings</th>
      <th>Default</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>black-formatter.args</td>
      <td><code>[]</code></td>
      <td>Arguments passed to Black to format Python files. Each argument should be provided as a separate string in the array. E.g <code>"black-formatter.args" = ["--config", "&lt;file&gt;"]</code></td>
    </tr>
    <tr>
      <td>black-formatter.cwd</td>
      <td><code>[]</code></td>
      <td>Sets the current working directory used to format Python files with Black. By default, it uses the root directory of the workspace <code>${workspaceFolder}</code>. You can set it to <code>${fileDirname}</code> to use the parent folder of the file being formatted as the working directory for Black.</td>
    </tr>
    <tr>
      <td>black-formatter.path</td>
      <td><code>[]</code></td>
      <td>Path or command to be used by the extension to format Python files with Black. Accepts an array of a single or multiple strings. If passing a command, each argument should be provided as a separate string in the array. If set to <code>["black"]</code>, it will use the version of Black available in the <code>PATH</code> environment variable. Note: Using this option may slowdown formatting. <br> Examples: <br> <code>["~/global_env/black"]</code> <br> <code>["conda", "run", "-n", "lint_env", "python", "-m", "black"]</code></td>
    </tr>
    <tr>
      <td>black-formatter.interpreter</td>
      <td><code>[]</code></td>
      <td>Path to a Python executable or a command that will be used to launch the Black server and any subprocess. Accepts an array of a single or multiple strings. When set to <code>[]</code>, the extension will use the path to the selected Python interpreter. If passing a command, each argument should be provided as a separate string in the array.</td>
    </tr>
    <tr>
      <td>black-formatter.importStrategy</td>
      <td><code>useBundled</code></td>
      <td>
      Defines which Black formatter binary to be used to format Python files. When set to <code>useBundled</code>, the extension will use the Black formatter binary that is shipped with the extension. When set to <code>fromEnvironment</code>, the extension will attempt to use the Black formatter binary and all dependencies that are available in the currently selected environment. **Note**: If the extension can't find a valid Black formatter binary in the selected environment, it will fallback to using the binary that is shipped with the extension. The <code>black-formatter.path</code> setting takes precedence and overrides the behavior of <code>black-formatter.importStrategy</code>.
      </td>
    </tr>
    <tr>
      <td>black-formatter.showNotification</td>
      <td><code>off</code></td>
      <td> Controls when notifications are shown by this extension.  Accepted values are <code>onError</code>, <code>onWarning</code>, <code>always</code> and <code>off</code>.</td>
    </tr>
    <tr>
      <td>black-formatter.serverTransport</td>
      <td><code>stdio</code></td>
      <td> Selects the transport protocol to be used by the Black server. When set to <code>stdio</code>, the extension will use the standard input/output streams to communicate with the Black server. When set to <code>pipe</code>, the extension will use a named pipe (on Windows) or Unix Domain Socket (on Linux/Mac) to communicate with the Black server. The <code>stdio</code> transport protocol is the default and recommended option for most users.</td>
    </tr>
  </tbody>
</table>

## Commands

<table>
  <thead>
    <tr>
      <th>Command</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Black Formatter: Restart</td>
      <td>Force re-start the format server.</td>
    </tr>
  </tbody>
</table>

## Logging

From the Command Palette (**View** > **Command Palette ...**), run the **Developer: Set Log Level...** command. Select **Black Formatter** from the **Extension logs** group. Then select the log level you want to set.

Alternatively, you can set the `black-formatter.trace.server` setting to `verbose` to get more detailed logs from the Black server. This can be helpful when filing bug reports.

To open the logs, click on the language status icon (`{}`) on the bottom right of the Status bar, next to the Python language mode. Locate the **Black Formatter** entry and select **Open logs**.

## Troubleshooting

In this section, you will find some common issues you might encounter and how to resolve them. If you are experiencing any issues that are not covered here, please [file an issue](https://github.com/microsoft/vscode-black-formatter/issues).

-   If the `black-formatter.importStrategy` setting is set to `fromEnvironment` but Black is not found in the selected environment, this extension will fallback to using the Black binary that is shipped with the extension. However, if there are dependencies installed in the environment, those dependencies will be used along with the shipped Black binary. This can lead to problems if the dependencies are not compatible with the shipped Black binary.

    To resolve this issue, you can:

    -   Set the `black-formatter.importStrategy` setting to `useBundled` and the `black-formatter.path` setting to point to the custom binary of Black you want to use; or
    -   Install Black in the selected environment.

## Development

The TypeScript client depends on the published [`@vscode/common-python-lsp`](https://www.npmjs.com/package/@vscode/common-python-lsp) package, so npm installation and TypeScript compilation do not require building the shared TypeScript submodule. Python bundling still reads the pinned [`vscode-common-python-lsp`](https://github.com/microsoft/vscode-common-python-lsp) submodule at `external/vscode-common-python-lsp`; the setup commands below initialize it.

When cloning the repository, pull the submodule at the same time:

```bash
git clone --recurse-submodules https://github.com/microsoft/vscode-black-formatter.git
```

If you already cloned without `--recurse-submodules`, initialize (or update) the submodule from the repository root:

```bash
git submodule update --init --recursive
```

Then choose the appropriate local package-feed setup below.

### Local package feeds

Use Node.js supported by this repository and Python 3.10 or later. Both setup commands create or reuse `.venv` and install the Python bundling tools. Choose the appropriate setup below before installing dependencies. Committed lockfiles use public npm URLs; Microsoft setup rewrites working copies for proxy installs.

#### Public contributors (non-Microsoft employees)

Use the public setup, which selects `https://registry.npmjs.org/` and `https://pypi.org/simple/` for its child processes. No Microsoft account or internal-feed credentials are needed, and this command works before `node_modules` exists:

From the repository root:

```bash
npm run setup
```

For subsequent npm installs, use `npm ci`. Public contributors do not need the Microsoft feed commands or lockfile hook.

#### Microsoft employees only

> **Microsoft users only:** The commands in this section configure Microsoft package feeds. Public contributors should use the public setup above.

Use the Microsoft setup, which selects `https://packagefeedproxy.microsoft.io/npm/` and `https://packagefeedproxy.microsoft.io/pypi/simple/` for its child processes:

```bash
npm run setup:msft
```

Microsoft setup initializes the Python shared-library submodule, then rewrites public npm and Yarn `resolved` URLs in the root `package-lock.json` to the npm proxy before running `npm ci`. Versions, integrity hashes, formatting, and private-feed URLs are preserved. The public setup leaves lockfiles unchanged.

After pulling a new lockfile from GitHub, rerun `npm run setup:msft`, or run the dependency-free rewrite step alone before your next install/build:

```bash
npm run setup:msft-registry
```

The standalone step requires the root lockfile to exist; it does not require a shared TypeScript checkout. Rewriting is idempotent and stops on missing or invalid lockfiles. Keep committed lockfile URLs public using the optional pre-commit hook below (or `npm run normalize-lockfile` for the root lockfile).

For subsequent root npm installs, use:

```bash
npm run ci:msft
```

This rewrites the root lockfile, then runs root `npm ci` with the proxy registry explicitly selected for package, audit, and metadata requests. Use `npm run setup:msft` for full setup, including Python dependencies.

Local setup, lockfile rewriting, and `ci:msft` share the feed URLs in `build/package-feeds.json`.

Both setup commands use the same implementation, stop on errors, and keep registry overrides scoped to setup's child processes; they do not change your shell environment, edit `.npmrc`, or add credentials. The standalone rewrite step only edits lockfiles; it does not configure the registry for subsequent commands.

After setup, run `npm run compile` to build the extension. For subsequent Python commands, use `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux (or activate that virtual environment). Registry overrides are not retained after setup.

#### Microsoft contributor pre-commit hook

If you use the Microsoft feeds and will commit changes, enable the recommended lockfile hook once per clone (no installed npm dependencies are required). It is not needed just to install or build:

```bash
npm run setup-hooks
```

The installer sets the clone's local `core.hooksPath` to `.githooks`, which also affects its linked worktrees. It refuses to replace an existing hook or a different hooks configuration. If you already use hooks, add `node build/normalize-package-lock.js --staged` to your existing pre-commit hook instead. Only enable this configuration in worktrees/branches that contain these hook files.

Before a local commit, the hook converts known `Pylance_PublicPackages`, `packagefeedproxy.microsoft.io/npm/`, and named `1es-public/npm-public` mirror tarball URLs in the staged root `package-lock.json` to public npm URLs. It preserves versions, integrity hashes, formatting, and intentional Azure-hosted dependencies such as `msft_consumption`. Unknown feeds are left unchanged. It re-stages only the lockfile; if normalization is needed and the lockfile has unstaged changes, the commit is blocked without modifying it. Stage or stash those changes, then retry.

To normalize manually, run `npm run normalize-lockfile`, review the changes, and stage them. To disable the installed hook, run `git config --local --unset core.hooksPath`. These are local Git hooks: GitHub and Dependabot do not execute them. No workflow writes changes to PR branches.

### GitHub Actions package feeds

The PR and push workflows set `PIP_INDEX_URL` to `https://packagefeedproxy.microsoft.io/pypi/simple/` for pip and nox installs. Their Node installation steps select `https://packagefeedproxy.microsoft.io/npm/` explicitly through `npm run ci:msft`, so these workflows do not set `NPM_CONFIG_REGISTRY`. CodeQL retains both environment variables because its autobuild step does not use the install helper. The npm endpoint follows the [TypeScript CI package-feed-proxy job](https://github.com/microsoft/TypeScript/blob/main/.github/workflows/ci.yml).

The shared lint and VSIX build actions and applicable PR/push test jobs use `npm run ci:msft`, rewriting working-copy lockfile URLs before installation and explicitly selecting the proxy for npm requests. Workflows do not commit these rewrites or change local registry configuration or Dependabot configuration. Existing dependency caches are retained; the VSIX build also retains its offline-cache preference. CodeQL retains workflow-level feed settings for its autobuild step.

### Azure release package feeds

The DevDiv Azure stable/prerelease pipelines pass the npm proxy to their build/publish templates using `customNPMRegistry`. After initializing the Python shared-library submodule, their dependency install steps use `npm run ci:msft` to rewrite the root npm lockfile and install through the proxy.

Each Python bootstrap and bundled-library install step explicitly sets `PIP_INDEX_URL` from `PIP_PROXY_INDEX_URL`, selecting the pip proxy even when a template's authentication setup changes the job-level index. Release triggers, approval gates, signing, and publishing behavior are unchanged.

Dependabot continues to use public registries and its existing update settings. Legacy Azure stable, prerelease, and validation definitions are unchanged.

### Localization

The **Localization** GitHub workflow submits English strings using the [shared composite action and Python tooling](https://github.com/microsoft/vscode-common-python-lsp#shared-localization-automation). Stable and pre-release DevDiv pipelines independently retrieve translations through Pylance-Eng's `pullLocalization: true`; releases never submit English or create translation-update PRs.

Both paths use `microsoft/vscode-python-extensions-loc`, branch **`dev`**, with canonical extension ID **`ms-python.black-formatter`**. English XLF is stored in `src/en/ms-python.black-formatter` and handbacks in `out/ms-python.black-formatter`. The action and Azure tooling checkout are pinned to the same reviewed revision.

Configure the `PYTHON_LOCALIZATION_APP_ID` Actions variable and `PYTHON_LOCALIZATION_PRIVATE_KEY` secret here, or grant access to organization-level credentials. The app needs Contents write access only to the localization drop; the caller's repository token stays read-only. The shared action uses the Microsoft npm proxy and pinned localization CLI. Authorize the literal `Github-Pylance` service connection for both Azure repository resources and release pipelines.

Keep English `package.nls.json` tracked. Root `package.nls.<locale>.json` and `l10n/` runtime files are generated, git-ignored release outputs. VSCE must include generated locale files despite Git ignores. Local builds are English-only unless translations are imported explicitly.

Translation is asynchronous. All 14 supported locales must be present, and every required real-language table must contain translation evidence. Individual untranslated strings are allowed. Missing, incomplete, or wholly untranslated handbacks fail before packaging, without falling back to stale translations. Do not publish while onboarding or real translated output is pending.
