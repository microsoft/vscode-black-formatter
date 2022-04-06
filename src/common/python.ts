// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { Disposable, Event, EventEmitter, extensions, Uri } from 'vscode';
import { traceError } from './logging';

interface IExtensionApi {
    ready: Promise<void>;
    debug: {
        getRemoteLauncherCommand(host: string, port: number, waitUntilDebuggerAttaches: boolean): Promise<string[]>;
        getDebuggerPackagePath(): Promise<string | undefined>;
    };
    settings: {
        readonly onDidChangeExecutionDetails: Event<Uri | undefined>;
        getExecutionDetails(resource?: Uri | undefined): {
            execCommand: string[] | undefined;
        };
    };
}

const onDidChangePythonInterpreterEvent = new EventEmitter<string>();
export const onDidChangePythonInterpreter: Event<string> = onDidChangePythonInterpreterEvent.event;

let _interpreterPath = '';
function updateInterpreterFromExtension(api: IExtensionApi) {
    const { execCommand } = api.settings.getExecutionDetails();
    const interpreterPath = execCommand ? execCommand.join(' ') : 'python';
    if (_interpreterPath !== interpreterPath) {
        _interpreterPath = interpreterPath;
        onDidChangePythonInterpreterEvent.fire(_interpreterPath);
    }
}

export async function initializePython(disposables: Disposable[]): Promise<void> {
    try {
        const extension = extensions.getExtension('ms-python.python');
        if (extension) {
            if (!extension.isActive) {
                await extension.activate();
            }

            const api: IExtensionApi = extension.exports as IExtensionApi;

            disposables.push(
                api.settings.onDidChangeExecutionDetails(() => {
                    updateInterpreterFromExtension(api);
                }),
            );

            updateInterpreterFromExtension(api);
        }
    } catch (error) {
        traceError('Error initializing python: ', error);
    }
}

export async function getInterpreterPath(disposables: Disposable[]): Promise<string> {
    if (_interpreterPath.length === 0) {
        await initializePython(disposables);
    }
    return _interpreterPath;
}
