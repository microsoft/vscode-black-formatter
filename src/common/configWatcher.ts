// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { Disposable, workspace } from 'vscode';
import { BLACK_CONFIG_FILES } from './constants';
import { traceLog } from './logging';

export function createConfigFileWatchers(onConfigChanged: () => Promise<void>): Disposable[] {
    return BLACK_CONFIG_FILES.map((pattern) => {
        const watcher = workspace.createFileSystemWatcher(`**/${pattern}`);
        const changeDisposable = watcher.onDidChange(async () => {
            traceLog(`Black config file changed: ${pattern}`);
            await onConfigChanged();
        });
        const createDisposable = watcher.onDidCreate(async () => {
            traceLog(`Black config file created: ${pattern}`);
            await onConfigChanged();
        });
        const deleteDisposable = watcher.onDidDelete(async () => {
            traceLog(`Black config file deleted: ${pattern}`);
            await onConfigChanged();
        });
        return Disposable.from(watcher, changeDisposable, createDisposable, deleteDisposable);
    });
}
