// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { assert } from 'chai';
import * as sinon from 'sinon';
import { EventEmitter, extensions, Uri } from 'vscode';
import { PythonExtension } from '@vscode/python-extension';
import { getInterpreterDetails, _resetForTesting } from '../../../../common/python';

suite('Python Interpreter Resolution Tests', () => {
    let getExtensionStub: sinon.SinonStub;
    let pythonExtensionApiStub: sinon.SinonStub;

    setup(() => {
        _resetForTesting();
        getExtensionStub = sinon.stub(extensions, 'getExtension');
        pythonExtensionApiStub = sinon.stub(PythonExtension, 'api');
    });

    teardown(() => {
        sinon.restore();
    });

    test('Finds interpreter using Python Environments extension', async () => {
        const mockEnvsApi = {
            getEnvironment: sinon.stub().resolves({
                version: '3.12.0',
                execInfo: {
                    run: { executable: '/usr/bin/python3.12', args: [] },
                },
                envId: { id: 'test-env', managerId: 'test-manager' },
                sysPrefix: '/usr',
                name: 'test',
                displayName: 'Python 3.12',
                environmentPath: Uri.file('/usr/bin/python3.12'),
            }),
            resolveEnvironment: sinon.stub(),
            onDidChangeEnvironment: new EventEmitter().event,
        };

        getExtensionStub.withArgs('ms-python.vscode-python-envs').returns({
            isActive: true,
            activate: sinon.stub().resolves(),
            exports: mockEnvsApi,
        });

        const result = await getInterpreterDetails(Uri.file('/test/workspace'));

        assert.isDefined(result.path);
        assert.strictEqual(result.path![0], '/usr/bin/python3.12');
        assert.isTrue(mockEnvsApi.getEnvironment.calledOnce);
        // Legacy API should not be called
        assert.isTrue(pythonExtensionApiStub.notCalled);
    });

    test('Finds interpreter using legacy ms-python.python extension', async () => {
        // Envs extension not installed
        getExtensionStub.withArgs('ms-python.vscode-python-envs').returns(undefined);

        const interpreterUri = Uri.file('/usr/bin/python3.10');
        const mockLegacyApi = {
            environments: {
                getActiveEnvironmentPath: sinon.stub().returns('/usr/bin/python3.10'),
                resolveEnvironment: sinon.stub().resolves({
                    executable: {
                        uri: interpreterUri,
                        bitness: '64-bit',
                        sysPrefix: '/usr',
                    },
                    version: {
                        major: 3,
                        minor: 10,
                        micro: 0,
                        release: { level: 'final', serial: 0 },
                        sysVersion: '3.10.0',
                    },
                }),
                onDidChangeActiveEnvironmentPath: new EventEmitter().event,
            },
            debug: {
                getDebuggerPackagePath: sinon.stub(),
            },
        };

        pythonExtensionApiStub.resolves(mockLegacyApi);

        const result = await getInterpreterDetails(Uri.file('/test/workspace'));

        assert.isDefined(result.path);
        assert.strictEqual(result.path![0], interpreterUri.fsPath);
        assert.isTrue(mockLegacyApi.environments.resolveEnvironment.calledOnce);
    });
});
