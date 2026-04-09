// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { assert } from 'chai';
import * as fs from 'fs-extra';
import * as path from 'path';
import * as sinon from 'sinon';
import { Uri, WorkspaceFolder } from 'vscode';
import { getEnvFileVars } from '../../../../common/envFile';
import * as vscodeapi from '../../../../common/vscodeapi';

// Use real files instead of stubbing fs-extra (whose exports are non-configurable).
suite('getEnvFileVars Tests', () => {
    let getConfigurationStub: sinon.SinonStub;

    const fixtureDir = path.join(__dirname, '.envfile-test-fixtures');

    const workspaceFolder: WorkspaceFolder = {
        uri: Uri.file(fixtureDir),
        name: 'workspace',
        index: 0,
    };

    setup(async () => {
        await fs.ensureDir(fixtureDir);
        getConfigurationStub = sinon.stub(vscodeapi, 'getConfiguration');
    });

    teardown(async () => {
        sinon.restore();
        await fs.remove(fixtureDir);
    });

    test('returns parsed variables from existing .env file', async () => {
        await fs.writeFile(path.join(fixtureDir, '.env'), 'FOO=bar\nBAZ=qux\n');
        getConfigurationStub.returns({
            get: (_key: string, defaultValue: string) => defaultValue,
        });

        const vars = await getEnvFileVars(workspaceFolder);
        // eslint-disable-next-line @typescript-eslint/naming-convention
        assert.deepStrictEqual(vars, { FOO: 'bar', BAZ: 'qux' });
    });

    test('returns empty object for missing file', async () => {
        getConfigurationStub.returns({
            get: (_key: string, defaultValue: string) => defaultValue,
        });

        const vars = await getEnvFileVars(workspaceFolder);
        assert.deepStrictEqual(vars, {});
    });

    test('resolves ${workspaceFolder} in path', async () => {
        await fs.writeFile(path.join(fixtureDir, '.env.test'), 'KEY=value\n');
        getConfigurationStub.returns({
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            get: (_key: string, _defaultValue: string) => '${workspaceFolder}/.env.test',
        });

        const vars = await getEnvFileVars(workspaceFolder);
        // eslint-disable-next-line @typescript-eslint/naming-convention
        assert.deepStrictEqual(vars, { KEY: 'value' });
    });

    test('resolves relative paths', async () => {
        await fs.writeFile(path.join(fixtureDir, '.env.local'), 'RELATIVE=yes\n');
        getConfigurationStub.returns({
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            get: (_key: string, _defaultValue: string) => '.env.local',
        });

        const vars = await getEnvFileVars(workspaceFolder);
        // eslint-disable-next-line @typescript-eslint/naming-convention
        assert.deepStrictEqual(vars, { RELATIVE: 'yes' });
    });
});
