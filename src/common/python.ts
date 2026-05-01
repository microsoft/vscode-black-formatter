// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

// Thin wrapper: delegates to @vscode/common-python-lsp shared package.

import { Disposable, Event, EventEmitter, Uri } from 'vscode';
import { PythonExtension } from '@vscode/python-extension';
import { IInterpreterDetails, PythonEnvironmentsProvider } from '@vscode/common-python-lsp';
import { BLACK_TOOL_CONFIG } from './constants';

export type { IInterpreterDetails };

const _onDidChangePython = new EventEmitter<void>();
export const onDidChangePythonInterpreter: Event<void> = _onDidChangePython.event;

let _provider = new PythonEnvironmentsProvider(BLACK_TOOL_CONFIG);
let _providerSub = _provider.onDidChangeInterpreter(() => _onDidChangePython.fire());

export function getPythonProvider(): PythonEnvironmentsProvider {
    return _provider;
}

export async function initializePython(disposables: Disposable[]): Promise<void> {
    return _provider.initializePython(disposables);
}

export async function getInterpreterDetails(resource?: Uri): Promise<IInterpreterDetails> {
    return _provider.getInterpreterDetails(resource);
}

export async function getDebuggerPath(): Promise<string | undefined> {
    const result = await _provider.getDebuggerPath();
    if (result) return result;
    try {
        const legacyApi = await PythonExtension.api();
        return legacyApi?.debug?.getDebuggerPackagePath();
    } catch {
        return undefined;
    }
}

export function resetCachedApis(): void {
    _providerSub.dispose();
    _provider.dispose();
    _provider = new PythonEnvironmentsProvider(BLACK_TOOL_CONFIG);
    _providerSub = _provider.onDidChangeInterpreter(() => _onDidChangePython.fire());
}
