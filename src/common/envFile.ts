// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as path from 'path';
import * as os from 'os';
import * as dotenv from 'dotenv';
import * as fsapi from 'fs-extra';
import { WorkspaceFolder } from 'vscode';
import { getConfiguration } from './vscodeapi';
import { traceLog, traceWarn } from './logging';

function expandTilde(filePath: string): string {
    if (filePath === '~') {
        return os.homedir();
    }
    if (filePath.startsWith('~/') || filePath.startsWith('~\\')) {
        return path.join(os.homedir(), filePath.slice(2));
    }
    return filePath;
}

// NOTE: We use Node's `dotenv` package to parse .env files. This has subtle
// differences from Python's `python-dotenv` (e.g., variable interpolation,
// multiline value handling). The Python subprocess receives env vars via
// process.env inheritance, not by re-parsing the .env file. If exact parity
// with python-dotenv is needed, consider passing the .env path to the Python
// side for re-parsing.

export async function getEnvFileVars(workspace: WorkspaceFolder): Promise<Record<string, string>> {
    const pythonConfig = getConfiguration('python', workspace.uri);
    let envFilePath = pythonConfig.get<string>('envFile', '${workspaceFolder}/.env');

    envFilePath = envFilePath.replace(/\$\{workspaceFolder\}/g, workspace.uri.fsPath);
    envFilePath = expandTilde(envFilePath);

    if (!path.isAbsolute(envFilePath)) {
        envFilePath = path.resolve(workspace.uri.fsPath, envFilePath);
    }

    try {
        if (await fsapi.pathExists(envFilePath)) {
            const content = await fsapi.readFile(envFilePath, 'utf-8');
            const vars = dotenv.parse(content);
            traceLog(`Loaded ${Object.keys(vars).length} env vars from ${envFilePath}`);
            return vars;
        }
    } catch (ex) {
        traceWarn(`Failed to read env file ${envFilePath}: ${ex}`);
    }
    return {};
}
