// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { commands, Disposable, Event, EventEmitter, extensions, Uri } from 'vscode';
import { traceError, traceLog } from './logging';
import { PythonExtension, ResolvedEnvironment } from '@vscode/python-extension';
import type { PythonEnvironment, PythonEnvironmentsAPI } from '../typings/pythonEnvironments';
import { PYTHON_MAJOR, PYTHON_MINOR, PYTHON_VERSION } from './constants';
import { getProjectRoot } from './utilities';

export interface IInterpreterDetails {
    path?: string[];
    resource?: Uri;
}

function parsePythonVersion(version: string | undefined): { major: number; minor: number; micro: number } | undefined {
    if (!version) {
        return undefined;
    }
    const parts = version.split('.');
    const major = Number(parts[0]);
    const minor = Number(parts[1] ?? 0);
    const micro = Number(parts[2] ?? 0);
    if (isNaN(major) || isNaN(minor) || isNaN(micro)) {
        return undefined;
    }
    return { major, minor, micro };
}

function convertToResolvedEnvironment(environment: PythonEnvironment): ResolvedEnvironment | undefined {
    const runConfig = environment.execInfo?.activatedRun ?? environment.execInfo?.run;
    const executable = runConfig?.executable;
    if (!executable) {
        return undefined;
    }
    const parsed = parsePythonVersion(environment.version);
    return {
        id: environment.envId?.id ?? '',
        path: executable,
        executable: {
            uri: Uri.file(executable),
            bitness: 'Unknown',
            sysPrefix: environment.sysPrefix ?? '',
        },
        version: parsed
            ? {
                  major: parsed.major,
                  minor: parsed.minor,
                  micro: parsed.micro,
                  release: { level: 'final', serial: 0 },
                  sysVersion: environment.version ?? '',
              }
            : undefined,
        environment: undefined,
        tools: [],
    } as ResolvedEnvironment;
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
    try {
        if (!extension.isActive) {
            await extension.activate();
        }
        const api = extension.exports;
        if (!api) {
            traceError('Python environments extension did not provide any exports.');
            return undefined;
        }
        _envsApi = api as PythonEnvironmentsAPI;
        return _envsApi;
    } catch (ex) {
        traceError('Failed to activate or retrieve API from Python environments extension.', ex as Error);
        return undefined;
    }
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

            traceLog('Waiting for interpreter from Python environments extension.');
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

// TODO: Unused code
export async function resolveInterpreter(interpreter: string[]): Promise<ResolvedEnvironment | undefined> {
    const envsApi = await getEnvironmentsExtensionAPI();
    if (envsApi) {
        const environment = await envsApi.resolveEnvironment(Uri.file(interpreter[0]));
        if (!environment) {
            return undefined;
        }
        return convertToResolvedEnvironment(environment);
    }
    const api = await getPythonExtensionAPI();
    return api?.environments.resolveEnvironment(interpreter[0]);
}

export async function getInterpreterDetails(resource?: Uri): Promise<IInterpreterDetails> {
    // Prefer the Python Environments extension if it's available, as it provides a more comprehensive view of the available environments.
    const envsApi = await getEnvironmentsExtensionAPI();
    if (envsApi) {
        try {
            const environment = await envsApi.getEnvironment(resource);
            if (environment) {
                const parsed = parsePythonVersion(environment.version);
                const runConfig = environment.execInfo?.activatedRun ?? environment.execInfo?.run;
                const executable = runConfig?.executable;
                const args = runConfig?.args ?? [];
                if (parsed && parsed.major === PYTHON_MAJOR && parsed.minor >= PYTHON_MINOR) {
                    if (executable) {
                        return { path: [executable, ...args], resource };
                    }
                    traceError('No executable found for selected Python environment.');
                    return { path: undefined, resource };
                }
                traceError(`Python version ${environment.version} is not supported.`);
                traceError(`Selected python path: ${runConfig?.executable}`);
                traceError(`Supported versions are ${PYTHON_VERSION} and above.`);
                return { path: undefined, resource };
            }
            // No environment found via envs API, fall through to legacy resolver.
        } catch (error) {
            traceError('Error getting interpreter from Python environments extension: ', error);
            // Fall through to legacy resolver.
        }
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

// TODO: The Python Environments extension does not expose a debug API yet; uses legacy ms-python.python
export async function getDebuggerPath(): Promise<string | undefined> {
    const api = await getPythonExtensionAPI();
    return api?.debug.getDebuggerPackagePath();
}

// TODO: Unused code
export async function runPythonExtensionCommand(command: string, ...rest: unknown[]) {
    const envsApi = await getEnvironmentsExtensionAPI();
    if (!envsApi) {
        await getPythonExtensionAPI();
    }
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
