// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as path from 'path';

export const EXTENSION_ID = 'ms-python.black-formatter';
const folderName = path.basename(__dirname);
export const EXTENSION_ROOT_DIR =
    folderName === 'common' ? path.dirname(path.dirname(__dirname)) : path.dirname(__dirname);
export const BUNDLED_PYTHON_SCRIPTS_DIR = path.join(EXTENSION_ROOT_DIR, 'bundled');
export const SERVER_SCRIPT_PATH = path.join(BUNDLED_PYTHON_SCRIPTS_DIR, 'tool', `lsp_server.py`);
export const DEBUG_SERVER_SCRIPT_PATH = path.join(BUNDLED_PYTHON_SCRIPTS_DIR, 'tool', `_debug_server.py`);
export const PYTHON_MAJOR = 3;
export const PYTHON_MINOR = 8;
export const PYTHON_VERSION = `${PYTHON_MAJOR}.${PYTHON_MINOR}`;
export const LS_SERVER_RESTART_DELAY = 1000;
