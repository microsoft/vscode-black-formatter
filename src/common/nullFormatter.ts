// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { Disposable } from 'vscode';
import { traceLog } from './logging';
import { registerDocumentFormattingEditProvider } from './vscodeapi';
import { getDocumentSelector } from './utilities';

let disposables: Disposable[] = [];
export function registerEmptyFormatter(): void {
    disposables.push(
        registerDocumentFormattingEditProvider(getDocumentSelector(), {
            provideDocumentFormattingEdits: function () {
                traceLog('Formatting requested before server has started.');
                return Promise.resolve(undefined);
            },
        }),
    );
}

export function unregisterEmptyFormatter(): void {
    if (disposables.length > 0) {
        disposables.forEach((d) => d.dispose());
        disposables = [];
    }
}
