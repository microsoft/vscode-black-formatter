// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');

function load(deactivate = async () => {}) {
    const calls = [];
    const toolConfig = { isFormatter: true };
    const serverInfo = { name: 'Black', module: 'black' };
    const exports = {};
    const source = ts.transpileModule(readFileSync(path.join(__dirname, '..', 'src', 'extension.ts'), 'utf8'), {
        compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
    }).outputText;
    vm.runInNewContext(source, {
        exports,
        require(name) {
            switch (name) {
                case '../external/vscode-common-python-lsp/typescript/dist':
                    return {
                        loadServerDefaults(root) {
                            assert.equal(root, 'extension-root');
                            return serverInfo;
                        },
                        activateToolExtension(context, options) {
                            calls.push({ context, options });
                            return { deactivate };
                        },
                    };
                case './common/constants':
                    return { EXTENSION_ROOT_DIR: 'extension-root', BLACK_TOOL_CONFIG: toolConfig };
                case './common/settings':
                    return {
                        logDefaultFormatter: () => calls.push('default formatter'),
                        logLegacySettings: () => calls.push('legacy settings'),
                    };
                default:
                    throw new Error(`Unexpected dependency: ${name}`);
            }
        },
    });
    return { extension: exports, calls, toolConfig, serverInfo };
}

test('activation delegates common ownership while retaining Black identity and settings logging', async () => {
    const { extension, calls, toolConfig, serverInfo } = load();
    const context = { subscriptions: [{ dispose() {} }] };
    await extension.activate(context);
    assert.equal(calls[0].context, context);
    assert.equal(calls[0].options.toolConfig, toolConfig);
    assert.deepEqual({ ...calls[0].options.serverInfo }, { name: 'Black Formatter', module: 'black' });
    assert.equal(serverInfo.name, 'Black');
    assert.deepEqual(calls.slice(1), ['default formatter', 'legacy settings']);
    assert.equal(context.subscriptions.length, 1);
});

test('deactivation awaits the runtime and releases the handle once shutdown completes', async () => {
    let finish;
    let stops = 0;
    const stopping = new Promise((resolve) => {
        finish = resolve;
    });
    const { extension } = load(() => {
        stops++;
        return stopping;
    });
    await extension.deactivate();
    await extension.activate({ subscriptions: [] });
    let completed = false;
    const shutdown = extension.deactivate().then(() => {
        completed = true;
    });
    await Promise.resolve();
    assert.equal(stops, 1);
    assert.equal(completed, false);
    finish();
    await shutdown;
    assert.equal(completed, true);
    await extension.deactivate();
    assert.equal(stops, 1);
});
