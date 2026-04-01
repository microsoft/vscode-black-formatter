// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { assert } from 'chai';
import * as sinon from 'sinon';
import * as vscodeapi from '../../../../common/vscodeapi';
import { getDocumentSelector, getInterpreterFromSetting } from '../../../../common/utilities';

suite('Document Selector Tests', () => {
    let isVirtualWorkspaceStub: sinon.SinonStub;
    setup(() => {
        isVirtualWorkspaceStub = sinon.stub(vscodeapi, 'isVirtualWorkspace');
        isVirtualWorkspaceStub.returns(false);
    });
    teardown(() => {
        sinon.restore();
    });

    test('Document selector default', () => {
        const selector = getDocumentSelector();
        assert.deepStrictEqual(selector, [
            { scheme: 'file', language: 'python' },
            { scheme: 'untitled', language: 'python' },
            { scheme: 'vscode-notebook', language: 'python' },
            { scheme: 'vscode-notebook-cell', language: 'python' },
        ]);
    });
    test('Document selector virtual workspace', () => {
        isVirtualWorkspaceStub.returns(true);
        const selector = getDocumentSelector();
        assert.deepStrictEqual(selector, [{ language: 'python' }]);
    });
});

suite('getInterpreterFromSetting Tests', () => {
    let getConfigurationStub: sinon.SinonStub;

    setup(() => {
        getConfigurationStub = sinon.stub(vscodeapi, 'getConfiguration');
    });

    teardown(() => {
        sinon.restore();
    });

    test('Returns interpreter array from configuration', () => {
        const expectedInterpreter = ['/usr/bin/python3'];
        getConfigurationStub.returns({
            get: (key: string) => {
                if (key === 'interpreter') {
                    return expectedInterpreter;
                }
                return undefined;
            },
        });

        const result = getInterpreterFromSetting('black-formatter');
        assert.deepStrictEqual(result, expectedInterpreter);
        assert.isTrue(getConfigurationStub.calledOnceWith('black-formatter'));
    });

    test('Returns undefined when interpreter is not set', () => {
        getConfigurationStub.returns({
            get: () => undefined,
        });

        const result = getInterpreterFromSetting('black-formatter');
        assert.isUndefined(result);
    });
});
