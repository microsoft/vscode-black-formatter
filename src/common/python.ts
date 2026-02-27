// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { commands, Disposable, Event, EventEmitter, extensions, Uri } from 'vscode';
import { traceError, traceLog } from './logging';
import { PythonExtension, ResolvedEnvironment } from '@vscode/python-extension';
import { PythonEnvironmentsAPI } from '../typings/pythonEnvironments';
import { PYTHON_MAJOR, PYTHON_MINOR, PYTHON_VERSION } from './constants';
import { getProjectRoot } from './utilities';

export interface IInterpreterDetails {
    path?: string[];
    resource?: Uri;
}

const onDidChangePythonInterpreterEvent = new EventEmitter<void>();
export const onDidChangePythonInterpreter: Event<void> = onDidChangePythonInterpreterEvent.event;

let _api: PythonExtension | undefined;
async function getPythonExtensionAPI(): Promise<PythonExtension | undefined> {
    if (_api) {
        return _api;
    }
    _api = await PythonExtension.api();
    return _api;
}

const PYTHON_ENVIRONMENTS_EXTENSION_ID = 'ms-python.vscode-python-envs';

let _envsApi: PythonEnvironmentsAPI | undefined;
async function getEnvironmentsExtensionAPI(): Promise<PythonEnvironmentsAPI | undefined> {
    if (_envsApi) {
        return _envsApi;
    }
    const extension = extensions.getExtension(PYTHON_ENVIRONMENTS_EXTENSION_ID);
    if (!extension) {
        return undefined;
    }
    if (!extension.isActive) {
        await extension.activate();
    }
    _envsApi = extension.exports as PythonEnvironmentsAPI;
    return _envsApi;
}

function sameInterpreter(a: string[], b: string[]): boolean {
    if (a.length !== b.length) {
        return false;
    }
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) {
            return false;
        }
    }
    return true;
}

let serverPython: string[] | undefined;
function checkAndFireEvent(interpreter: string[] | undefined): void {
    if (interpreter === undefined) {
        if (serverPython) {
            // Python was reset for this uri
            serverPython = undefined;
            onDidChangePythonInterpreterEvent.fire();
            return;
        } else {
            return; // No change in interpreter
        }
    }

    if (!serverPython || !sameInterpreter(serverPython, interpreter)) {
        serverPython = interpreter;
        onDidChangePythonInterpreterEvent.fire();
    }
}

async function refreshServerPython(): Promise<void> {
    const projectRoot = await getProjectRoot();
    const interpreter = await getInterpreterDetails(projectRoot?.uri);
    checkAndFireEvent(interpreter.path);
}

export async function initializePython(disposables: Disposable[]): Promise<void> {
    try {
        // Prefer the Python Environments extension if it's available, as it provides a more comprehensive view of the available environments.
        const envsApi = await getEnvironmentsExtensionAPI();

        if (envsApi) {
            disposables.push(
                envsApi.onDidChangeEnvironment(async () => {
                    await refreshServerPython();
                }),
            );

            traceLog('Waiting for interpreter from python environments extension.');
            await refreshServerPython();
            return;
        }

        // Fall back to legacy ms-python.python extension API
        const api = await getPythonExtensionAPI();

        if (api) {
            disposables.push(
                api.environments.onDidChangeActiveEnvironmentPath(async () => {
                    await refreshServerPython();
                }),
            );

            traceLog('Waiting for interpreter from Python extension.');
            await refreshServerPython();
        }
    } catch (error) {
        traceError('Error initializing Python: ', error);
    }
}

export async function resolveInterpreter(interpreter: string[]): Promise<ResolvedEnvironment | undefined> {
    const api = await getPythonExtensionAPI();
    return api?.environments.resolveEnvironment(interpreter[0]);
}

export async function getInterpreterDetails(resource?: Uri): Promise<IInterpreterDetails> {
    // Prefer the Python Environments extension if it's available, as it provides a more comprehensive view of the available environments.
    const envsApi = await getEnvironmentsExtensionAPI();
    if (envsApi) {
        const environment = await envsApi.getEnvironment(resource);
        if (environment) {
            return {
                path: [environment.execInfo.run.executable],
                resource,
            };
        }
        return { path: undefined, resource };
    }

    // Fall back to legacy ms-python.python extension API
    const api = await getPythonExtensionAPI();
    const environment = await api?.environments.resolveEnvironment(
        api?.environments.getActiveEnvironmentPath(resource),
    );
    if (environment?.executable.uri && checkVersion(environment)) {
        return { path: [environment?.executable.uri.fsPath], resource };
    }
    return { path: undefined, resource };
}

export async function getDebuggerPath(): Promise<string | undefined> {
    const api = await getPythonExtensionAPI();
    return api?.debug.getDebuggerPackagePath();
}

export async function runPythonExtensionCommand(command: string, ...rest: unknown[]) {
    await getPythonExtensionAPI();
    return await commands.executeCommand(command, ...rest);
}

export function checkVersion(resolved: ResolvedEnvironment | undefined): boolean {
    const version = resolved?.version;
    if (version?.major === PYTHON_MAJOR && version?.minor >= PYTHON_MINOR) {
        return true;
    }
    traceError(`Python version ${version?.major}.${version?.minor} is not supported.`);
    traceError(`Selected python path: ${resolved?.executable.uri?.fsPath}`);
    traceError(`Supported versions are ${PYTHON_VERSION} and above.`);
    return false;
}
