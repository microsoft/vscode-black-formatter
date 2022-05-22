# Formatter extension for Visual Studio Code using `black`

A Visual Studio Code extension with support for the `black` formatter. The extension ships with `black=22.3.0`.

Note:

-   This extension is supported for all [actively supported versions](https://devguide.python.org/#status-of-python-branches) of the `python` language (i.e., python >= 3.7).
-   The bundled `black` is only used if there is no installed version of `black` found in the selected `python` environment.
-   Minimum supported version of `black` is `22.3.0`.

## Usage

Once installed in Visual Studio Code, "Black Formatter" will be available as a formatter for python files. Please select "Black Formatter" (extension id:`ms-python.black-formatter`) as the default formatter. You can do this either by using the context menu (right click on a open python file in the editor) and select "Format Document With...", or you can add the following to your settings:

```json
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
```

### Format on save

You can enable format on save for python by having the following values in your settings:

```json
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
```

### Disabling formatting with `black`

If you want to disable Black formatter, you can [disable this extension](https://code.visualstudio.com/docs/editor/extension-marketplace#_disable-an-extension) per workspace in Visual Studio Code.

## Settings

| Settings              | Default | Description                                                                                                                                                                                                                                                              |
| --------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| black-formatter.args  | `[]`    | Custom arguments passed to `black`. E.g `"black-formatter.args" = ["--config", "<file>"]`                                                                                                                                                                                |
| black-formatter.trace | `error` | Sets the tracing level for the extension.                                                                                                                                                                                                                                |
| black-formatter.path  | `[]`    | Setting to provide custom `black` executable. This will slow down formatting, since we will have to run `black` executable every time or file save or open. Example 1: `["~/global_env/black"]` Example 2: `["conda", "run", "-n", "lint_env", "python", "-m", "black"]` |
| black-formatter.show-formatting-messages | `true` | Whether to show messages in UI when extension didn't format file for any reason.

## Commands

| Command                  | Description                       |
| ------------------------ | --------------------------------- |
| Black Formatter: Restart | Force re-start the format server. |
