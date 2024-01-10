import * as path from 'path';

import { runTests } from '@vscode/test-electron';
import { EXTENSION_ROOT_DIR } from '../../common/constants';

const TEST_PROJECT_DIR = path.join(EXTENSION_ROOT_DIR, 'src', 'test', 'ts_tests', 'test_data', 'project');

async function main() {
    try {
        // The folder containing the Extension Manifest package.json
        // Passed to `--extensionDevelopmentPath`
        const extensionDevelopmentPath = EXTENSION_ROOT_DIR;

        // The path to test runner
        // Passed to --extensionTestsPath
        const extensionTestsPath = path.resolve(__dirname, './index');

        // Download VS Code, unzip it and run the integration test
        // eslint-disable-next-line @typescript-eslint/naming-convention
        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            extensionTestsEnv: { SMOKE_TESTS: 'true' },
            timeout: 60000,
            launchArgs: [TEST_PROJECT_DIR],
        });
    } catch (err) {
        console.error('Failed to run tests');
        console.error(err);
        process.exit(1);
    }
}

main();
