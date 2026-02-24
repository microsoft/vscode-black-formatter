// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { assert } from 'chai';
import * as sinon from 'sinon';
import { Disposable, FileSystemWatcher, workspace } from 'vscode';
import { createConfigFileWatchers } from '../../../../common/configWatcher';
import { BLACK_CONFIG_FILES } from '../../../../common/constants';

interface MockFileSystemWatcher {
    watcher: FileSystemWatcher;
    fireDidCreate(): Promise<void>;
    fireDidChange(): Promise<void>;
    fireDidDelete(): Promise<void>;
}

function createMockFileSystemWatcher(): MockFileSystemWatcher {
    let onDidChangeHandler: (() => Promise<void>) | undefined;
    let onDidCreateHandler: (() => Promise<void>) | undefined;
    let onDidDeleteHandler: (() => Promise<void>) | undefined;

    const watcher = {
        onDidChange: (handler: () => Promise<void>): Disposable => {
            onDidChangeHandler = handler;
            return { dispose: () => {} };
        },
        onDidCreate: (handler: () => Promise<void>): Disposable => {
            onDidCreateHandler = handler;
            return { dispose: () => {} };
        },
        onDidDelete: (handler: () => Promise<void>): Disposable => {
            onDidDeleteHandler = handler;
            return { dispose: () => {} };
        },
        dispose: () => {},
    } as unknown as FileSystemWatcher;

    return {
        watcher,
        fireDidCreate: async () => {
            if (onDidCreateHandler) {
                await onDidCreateHandler();
            }
        },
        fireDidChange: async () => {
            if (onDidChangeHandler) {
                await onDidChangeHandler();
            }
        },
        fireDidDelete: async () => {
            if (onDidDeleteHandler) {
                await onDidDeleteHandler();
            }
        },
    };
}

suite('Config File Watcher Tests', () => {
    let sandbox: sinon.SinonSandbox;
    let createFileSystemWatcherStub: sinon.SinonStub;
    let mockWatchers: MockFileSystemWatcher[];

    setup(() => {
        sandbox = sinon.createSandbox();
        mockWatchers = BLACK_CONFIG_FILES.map(() => createMockFileSystemWatcher());

        let watcherIndex = 0;
        createFileSystemWatcherStub = sandbox.stub(workspace, 'createFileSystemWatcher').callsFake(() => {
            return mockWatchers[watcherIndex++].watcher;
        });
    });

    teardown(() => {
        sandbox.restore();
    });

    test('Creates a file watcher for each Black config file pattern', () => {
        const onConfigChanged = sandbox.stub().resolves();
        createConfigFileWatchers(onConfigChanged);

        assert.strictEqual(createFileSystemWatcherStub.callCount, BLACK_CONFIG_FILES.length);
        for (let i = 0; i < BLACK_CONFIG_FILES.length; i++) {
            assert.isTrue(
                createFileSystemWatcherStub.getCall(i).calledWith(`**/${BLACK_CONFIG_FILES[i]}`),
                `Expected watcher for pattern **/${BLACK_CONFIG_FILES[i]}`,
            );
        }
    });

    test('Server restarts when a config file is created', async () => {
        const onConfigChanged = sandbox.stub().resolves();
        createConfigFileWatchers(onConfigChanged);

        // Simulate creating a pyproject.toml file
        await mockWatchers[0].fireDidCreate();

        assert.isTrue(onConfigChanged.calledOnce, 'Expected onConfigChanged to be called when config file is created');
    });

    test('Server restarts when a config file is changed', async () => {
        const onConfigChanged = sandbox.stub().resolves();
        createConfigFileWatchers(onConfigChanged);

        // Simulate modifying .black
        await mockWatchers[1].fireDidChange();

        assert.isTrue(onConfigChanged.calledOnce, 'Expected onConfigChanged to be called when config file is changed');
    });

    test('Server restarts when a config file is deleted', async () => {
        const onConfigChanged = sandbox.stub().resolves();
        createConfigFileWatchers(onConfigChanged);

        // Simulate deleting setup.cfg
        await mockWatchers[2].fireDidDelete();

        assert.isTrue(onConfigChanged.calledOnce, 'Expected onConfigChanged to be called when config file is deleted');
    });

    test('Server restarts for each config file type on create', async () => {
        const onConfigChanged = sandbox.stub().resolves();
        createConfigFileWatchers(onConfigChanged);

        // Fire onDidCreate for every config file pattern
        for (const mock of mockWatchers) {
            await mock.fireDidCreate();
        }

        assert.strictEqual(
            onConfigChanged.callCount,
            BLACK_CONFIG_FILES.length,
            `Expected onConfigChanged to be called once for each of the ${BLACK_CONFIG_FILES.length} config file patterns`,
        );
    });

    test('Returns a disposable for each watcher', () => {
        const onConfigChanged = sandbox.stub().resolves();
        const disposables = createConfigFileWatchers(onConfigChanged);

        assert.strictEqual(disposables.length, BLACK_CONFIG_FILES.length);
        for (const d of disposables) {
            assert.isFunction(d.dispose);
        }
    });
});
