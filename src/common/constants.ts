// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as path from 'path';
import { resolveExtensionRoot, ToolConfig } from '@vscode/common-python-lsp';

export const EXTENSION_ID = 'ms-python.black-formatter';
export const EXTENSION_ROOT_DIR = resolveExtensionRoot(__dirname);

export const BLACK_CONFIG_FILES = ['pyproject.toml', '.black', 'setup.cfg', 'tox.ini'];

export const BLACK_TOOL_CONFIG: ToolConfig = {
    toolId: 'black-formatter',
    toolDisplayName: 'Black',
    toolModule: 'black',
    minimumPythonVersion: { major: 3, minor: 10 },
    configFiles: BLACK_CONFIG_FILES,
    serverScript: path.join(EXTENSION_ROOT_DIR, 'bundled', 'tool', 'lsp_server.py'),
    debugServerScript: path.join(EXTENSION_ROOT_DIR, 'bundled', 'tool', '_debug_server.py'),
    settingsDefaults: {
        serverTransport: 'stdio',
    },
    trackedSettings: ['args', 'cwd', 'path', 'interpreter', 'importStrategy', 'showNotifications', 'serverTransport'],
};
