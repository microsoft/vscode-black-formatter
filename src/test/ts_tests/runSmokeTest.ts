// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.
/* eslint-disable @typescript-eslint/naming-convention */

import * as cp from 'child_process';
import * as path from 'path';

import { runTests, downloadAndUnzipVSCode, resolveCliArgsFromVSCodeExecutablePath } from '@vscode/test-electron';
import { EXTENSION_ROOT_DIR } from '../../common/constants';

const TEST_PROJECT_DIR = path.join(EXTENSION_ROOT_DIR, 'src', 'test', 'ts_tests', 'test_data', 'project');

async function main() {
    try {
        console.log('Downloading VS Code...');
        const vscodeExecutablePath = await downloadAndUnzipVSCode('stable');
        console.log('Finished downloading VS Code.');

        const [cli, ...args] = resolveCliArgsFromVSCodeExecutablePath(vscodeExecutablePath);
        const command = path.relative(EXTENSION_ROOT_DIR, cli);
        console.log('Installing Python extension...', [command, ...args, '--install-extension', 'ms-python.python']);
        cp.spawnSync(command, [...args, '--install-extension', 'ms-python.python'], {
            encoding: 'utf-8',
            stdio: 'inherit',
        });
        console.log('Finished installing Python extension.');

        const extensionDevelopmentPath = EXTENSION_ROOT_DIR;
        const extensionTestsPath = path.resolve(__dirname, './index');

        console.log('Running tests...');
        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            extensionTestsEnv: { SMOKE_TESTS: 'true' },
            launchArgs: [TEST_PROJECT_DIR],
        });
    } catch (err) {
        console.error('Failed to run tests');
        console.error(err);
        process.exit(1);
    }
}

main();
