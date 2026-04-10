// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { assert } from 'chai';
import * as sinon from 'sinon';
import { Disposable, FileSystemWatcher, workspace } from 'vscode';
import { createConfigFileWatchers } from '../../../../common/configWatcher';
import { BLACK_CONFIG_FILES } from '../../../../common/constants';

interface MockFileSystemWatcher {
    watcher: FileSystemWatcher;
    changeDisposable: { dispose: sinon.SinonStub };
    createDisposable: { dispose: sinon.SinonStub };
    deleteDisposable: { dispose: sinon.SinonStub };
    fireDidCreate(): Promise<void>;
    fireDidChange(): Promise<void>;
    fireDidDelete(): Promise<void>;
}

function createMockFileSystemWatcher(sb: sinon.SinonSandbox): MockFileSystemWatcher {
    const changeDisposable = { dispose: sb.stub() };
    const createDisposable = { dispose: sb.stub() };
    const deleteDisposable = { dispose: sb.stub() };

    let onDidChangeHandler: (() => Promise<void>) | undefined;
    let onDidCreateHandler: (() => Promise<void>) | undefined;
    let onDidDeleteHandler: (() => Promise<void>) | undefined;

    const watcher = {
        onDidChange: sb.stub().callsFake((handler: () => Promise<void>): Disposable => {
            onDidChangeHandler = handler;
            return changeDisposable as unknown as Disposable;
        }),
        onDidCreate: sb.stub().callsFake((handler: () => Promise<void>): Disposable => {
            onDidCreateHandler = handler;
            return createDisposable as unknown as Disposable;
        }),
        onDidDelete: sb.stub().callsFake((handler: () => Promise<void>): Disposable => {
            onDidDeleteHandler = handler;
            return deleteDisposable as unknown as Disposable;
        }),
        dispose: sb.stub(),
    } as unknown as FileSystemWatcher;

    return {
        watcher,
        changeDisposable,
        createDisposable,
        deleteDisposable,
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
    let onConfigChangedCallback: sinon.SinonStub;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let mockWatcher: any;
    let changeDisposable: { dispose: sinon.SinonStub };
    let createDisposable: { dispose: sinon.SinonStub };
    let deleteDisposable: { dispose: sinon.SinonStub };

    setup(() => {
        sandbox = sinon.createSandbox();
        mockWatchers = BLACK_CONFIG_FILES.map(() => createMockFileSystemWatcher(sandbox));
        onConfigChangedCallback = sandbox.stub().resolves();
        mockWatcher = mockWatchers[0].watcher;
        changeDisposable = mockWatchers[0].changeDisposable;
        createDisposable = mockWatchers[0].createDisposable;
        deleteDisposable = mockWatchers[0].deleteDisposable;

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

    test('Should dispose all subscriptions and watcher on dispose', () => {
        const watchers = createConfigFileWatchers(onConfigChangedCallback);

        watchers[0].dispose();

        assert.strictEqual(changeDisposable.dispose.callCount, 1, 'Change subscription should be disposed');
        assert.strictEqual(createDisposable.dispose.callCount, 1, 'Create subscription should be disposed');
        assert.strictEqual(deleteDisposable.dispose.callCount, 1, 'Delete subscription should be disposed');
        assert.strictEqual(mockWatcher.dispose.callCount, 1, 'Watcher should be disposed');
    });

    test('Should not call callback after dispose', () => {
        const watchers = createConfigFileWatchers(onConfigChangedCallback);

        // Dispose the watcher
        watchers[0].dispose();

        // Get the handlers and call them after disposal
        const changeHandler = mockWatcher.onDidChange.getCall(0).args[0];
        changeHandler();

        assert.strictEqual(onConfigChangedCallback.callCount, 0, 'Callback should not be called after dispose');
    });
});
