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
        const vscodeExecutablePath = await downloadAndUnzipVSCode('stable');

        const [cli, ...args] = resolveCliArgsFromVSCodeExecutablePath(vscodeExecutablePath);
        const isWin = process.platform === 'win32';
        const command = cli;
        console.log('Resolved VSCode CLI absolute path:', command);
        console.log('CLI args:', args);
        const fullArgs = [...args, '--verbose', '--install-extension', 'ms-python.python'];
        console.log('Full command to execute:', `${command} ${fullArgs.join(' ')}`);

        const spawnOptions: cp.SpawnSyncOptions = {
            encoding: 'utf-8',
            stdio: 'inherit',
            ...(isWin ? { shell: true } : {}),
        };

        try {
            const installResult = cp.spawnSync(command, fullArgs, spawnOptions);
            console.log('spawnSync result:', installResult);
            console.log(`Python extension installation exit code: ${installResult.status}`);
            if (installResult.error) {
                console.error('Python extension installation error:', installResult.error);
            }
            if (installResult.stderr) {
                console.error('Python extension installation stderr:', installResult.stderr);
            }
            if (installResult.stdout) {
                console.log('Python extension installation stdout:', installResult.stdout);
            }
        } catch (e) {
            console.error('Exception thrown during spawnSync:', e);
        }

        console.log('Waiting for extension registration...');
        await new Promise((resolve) => setTimeout(resolve, 2000)); // Wait 2 seconds for extension registration

        const extensionDevelopmentPath = EXTENSION_ROOT_DIR;
        const extensionTestsPath = path.resolve(__dirname, './index');

        console.log('Starting test run...');
        console.log('Extension development path:', extensionDevelopmentPath);
        console.log('Extension tests path:', extensionTestsPath);
        console.log('Test project directory:', TEST_PROJECT_DIR);

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
