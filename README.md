# Black extension for Visual Studio Code

A Visual Studio Code extension with support for the `black` formatter. The extension ships with `black=22.3.0`.

Note:

-   This extension is supported for all [actively supported versions](https://devguide.python.org/#status-of-python-branches) of the `python` language (i.e., python >= 3.7).
-   The bundled `black` is only used if there is no installed version of `black` found in the selected `python` environment.
-   Minimum supported version of `black` is `22.3.0`.

## Usage

Once installed in Visual Studio Code, `black` will be automatically executed when you open a Python file.

If you want to disable `black`, you can [disable this extension](https://code.visualstudio.com/docs/editor/extension-marketplace#_disable-an-extension) per workspace in Visual Studio Code.

## Settings

| Settings    | Default | Description                                                                                                                                                                                                                                                              |
| ----------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| black.args  | `[]`    | Custom arguments passed to `black`. E.g `"black.args" = ["--config", "<file>"]`                                                                                                                                                                                          |
| black.trace | `error` | Sets the tracing level for the extension.                                                                                                                                                                                                                                |
| black.path  | `[]`    | Setting to provide custom `black` executable. This will slow down formatting, since we will have to run `black` executable every time or file save or open. Example 1: `["~/global_env/black"]` Example 2: `["conda", "run", "-n", "lint_env", "python", "-m", "black"]` |

## Commands

| Command                  | Description                       |
| ------------------------ | --------------------------------- |
| Black: Restart Formatter | Force re-start the format server. |
