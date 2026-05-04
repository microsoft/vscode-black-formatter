// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

// NOTE: Variable resolution and validation tests live in the shared package
// (@vscode/common-python-lsp) test suite. Extension-level tests focus on
// extension-specific wrapper behavior that delegates to the shared package.

import { assert } from 'chai';
import * as path from 'path';
import * as sinon from 'sinon';
import * as TypeMoq from 'typemoq';
import { Uri, WorkspaceConfiguration, WorkspaceFolder } from 'vscode';
import { TransportKind } from 'vscode-languageclient/node';
import { EXTENSION_ROOT_DIR } from '../../../../common/constants';
import { getServerTransport, logLegacySettings, logDefaultFormatter } from '../../../../common/settings';
import * as vscodeapi from '../../../../common/vscodeapi';
import * as logging from '../../../../common/logging';

suite('Settings Tests', () => {
    const workspace1: WorkspaceFolder = {
        uri: Uri.file(path.join(EXTENSION_ROOT_DIR, 'src', 'test', 'testWorkspace', 'workspace1')),
        name: 'workspace1',
        index: 0,
    };

    suite('getServerTransport tests', () => {
        let getConfigurationStub: sinon.SinonStub;
        let configMock: TypeMoq.IMock<WorkspaceConfiguration>;

        setup(() => {
            getConfigurationStub = sinon.stub(vscodeapi, 'getConfiguration');
            configMock = TypeMoq.Mock.ofType<WorkspaceConfiguration>();
            getConfigurationStub.returns(configMock.object);
        });

        teardown(() => {
            sinon.restore();
        });

        test('Returns stdio by default', () => {
            configMock.setup((c) => c.get<string>('serverTransport', 'stdio')).returns(() => 'stdio');
            const transport = getServerTransport('black-formatter', workspace1.uri);
            assert.strictEqual(transport, TransportKind.stdio);
        });

        test('Returns pipe when configured', () => {
            configMock.setup((c) => c.get<string>('serverTransport', 'stdio')).returns(() => 'pipe');
            const transport = getServerTransport('black-formatter', workspace1.uri);
            assert.strictEqual(transport, TransportKind.pipe);
        });
    });

    suite('logLegacySettings tests', () => {
        let getConfigurationStub: sinon.SinonStub;
        let getWorkspaceFoldersStub: sinon.SinonStub;
        let traceWarnStub: sinon.SinonStub;
        let configMock: TypeMoq.IMock<WorkspaceConfiguration>;

        setup(() => {
            getConfigurationStub = sinon.stub(vscodeapi, 'getConfiguration');
            getWorkspaceFoldersStub = sinon.stub(vscodeapi, 'getWorkspaceFolders');
            getWorkspaceFoldersStub.returns([workspace1]);
            traceWarnStub = sinon.stub(logging, 'traceWarn');
            configMock = TypeMoq.Mock.ofType<WorkspaceConfiguration>();
            getConfigurationStub.returns(configMock.object);
        });

        teardown(() => {
            sinon.restore();
        });

        test('Logs warning when legacy blackArgs are set', () => {
            configMock.setup((c) => c.get<string[]>('formatting.blackArgs', [])).returns(() => ['--check']);
            configMock.setup((c) => c.get<string>('formatting.blackPath', '')).returns(() => '');

            logLegacySettings();

            assert.isTrue(traceWarnStub.calledWith(sinon.match('python.formatting.blackArgs')));
        });

        test('Logs warning when legacy blackPath is set', () => {
            configMock.setup((c) => c.get<string[]>('formatting.blackArgs', [])).returns(() => []);
            configMock.setup((c) => c.get<string>('formatting.blackPath', '')).returns(() => '/usr/bin/black');

            logLegacySettings();

            assert.isTrue(traceWarnStub.calledWith(sinon.match('python.formatting.blackPath')));
        });

        test('No warnings when legacy settings are empty', () => {
            configMock.setup((c) => c.get<string[]>('formatting.blackArgs', [])).returns(() => []);
            configMock.setup((c) => c.get<string>('formatting.blackPath', '')).returns(() => '');

            logLegacySettings();

            assert.isFalse(traceWarnStub.calledWith(sinon.match('deprecated')));
        });
    });

    suite('logDefaultFormatter tests', () => {
        let getConfigurationStub: sinon.SinonStub;
        let getWorkspaceFoldersStub: sinon.SinonStub;
        let traceWarnStub: sinon.SinonStub;
        let traceInfoStub: sinon.SinonStub;
        let configMock: TypeMoq.IMock<WorkspaceConfiguration>;

        setup(() => {
            getConfigurationStub = sinon.stub(vscodeapi, 'getConfiguration');
            getWorkspaceFoldersStub = sinon.stub(vscodeapi, 'getWorkspaceFolders');
            getWorkspaceFoldersStub.returns([workspace1]);
            traceWarnStub = sinon.stub(logging, 'traceWarn');
            traceInfoStub = sinon.stub(logging, 'traceInfo');
            configMock = TypeMoq.Mock.ofType<WorkspaceConfiguration>();
            getConfigurationStub.returns(configMock.object);
        });

        teardown(() => {
            sinon.restore();
        });

        test('No warning when black is default formatter', () => {
            configMock.setup((c) => c.get<string>('defaultFormatter', '')).returns(() => 'ms-python.black-formatter');

            logDefaultFormatter();

            assert.isTrue(traceInfoStub.calledWith(sinon.match('ms-python.black-formatter')));
            assert.isFalse(traceWarnStub.calledWith(sinon.match('NOT set')));
        });

        test('Warns when another formatter is set', () => {
            configMock.setup((c) => c.get<string>('defaultFormatter', '')).returns(() => 'other.formatter');

            logDefaultFormatter();

            assert.isTrue(traceWarnStub.calledWith(sinon.match('NOT set')));
        });
    });
});
