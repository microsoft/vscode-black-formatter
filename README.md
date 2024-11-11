# Formatter extension for Visual Studio Code using the Black formatter

A Visual Studio Code extension with support for the Black formatter. The extension ships with `black=24.8.0`.

> Note: The minimum version of Black this extension supports is `22.3.0`.

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
