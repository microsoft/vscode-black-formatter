// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { ConfigurationChangeEvent, ConfigurationScope, WorkspaceConfiguration, WorkspaceFolder } from 'vscode';
import { getInterpreterDetails } from './python';
import { getConfiguration, getWorkspaceFolders } from './vscodeapi';
import { traceLog } from './logging';

export interface ISettings {
    cwd: string;
    workspace: string;
    args: string[];
    path: string[];
    interpreter: string[];
    importStrategy: string;
    showNotifications: string;
}

export function getExtensionSettings(namespace: string, includeInterpreter?: boolean): Promise<ISettings[]> {
    return Promise.all(getWorkspaceFolders().map((w) => getWorkspaceSettings(namespace, w, includeInterpreter)));
}

function resolveVariables(value: string[], workspace?: WorkspaceFolder): string[] {
    const substitutions = new Map<string, string>();
    const home = process.env.HOME || process.env.USERPROFILE;
    if (home) {
        substitutions.set('${userHome}', home);
    }
    if (workspace) {
        substitutions.set('${workspaceFolder}', workspace.uri.fsPath);
    }
    substitutions.set('${cwd}', process.cwd());
    getWorkspaceFolders().forEach((w) => {
        substitutions.set('${workspaceFolder:' + w.name + '}', w.uri.fsPath);
    });

    return value.map((s) => {
        for (const [key, value] of substitutions) {
            s = s.replace(key, value);
        }
        return s;
    });
}

function getArgs(namespace: string, workspace: WorkspaceFolder): string[] {
    const config = getConfiguration(namespace, workspace.uri);
    const args = config.get<string[]>('args', []);

    if (args.length > 0) {
        return args;
    }

    const legacyConfig = getConfiguration('python', workspace.uri);
    return legacyConfig.get<string[]>('formatting.blackArgs', []);
}

function getPath(namespace: string, workspace: WorkspaceFolder): string[] {
    const config = getConfiguration(namespace, workspace.uri);
    const path = config.get<string[]>('path', []);

    if (path.length > 0) {
        return path;
    }

    const legacyConfig = getConfiguration('python', workspace.uri);
    const legacyPath = legacyConfig.get<string>('formatting.blackPath', '');
    if (legacyPath.length > 0 && legacyPath !== 'black') {
        return [legacyPath];
    }
    return [];
}

export function getInterpreterFromSetting(namespace: string, scope?: ConfigurationScope) {
    const config = getConfiguration(namespace, scope);
    return config.get<string[]>('interpreter');
}

export async function getWorkspaceSettings(
    namespace: string,
    workspace: WorkspaceFolder,
    includeInterpreter?: boolean,
): Promise<ISettings> {
    const config = getConfiguration(namespace, workspace.uri);

    let interpreter: string[] = [];
    if (includeInterpreter) {
        interpreter = getInterpreterFromSetting(namespace, workspace) ?? [];
        if (interpreter.length === 0) {
            traceLog(`No interpreter found from setting ${namespace}.interpreter`);
            traceLog(`Getting interpreter from ms-python.python extension for workspace ${workspace.uri.fsPath}`);
            interpreter = (await getInterpreterDetails(workspace.uri)).path ?? [];
            if (interpreter.length > 0) {
                traceLog(
                    `Interpreter from ms-python.python extension for ${workspace.uri.fsPath}:`,
                    `${interpreter.join(' ')}`,
                );
            }
        } else {
            traceLog(`Interpreter from setting ${namespace}.interpreter: ${interpreter.join(' ')}`);
        }

        if (interpreter.length === 0) {
            traceLog(`No interpreter found for ${workspace.uri.fsPath} in settings or from ms-python.python extension`);
        }
    }

    const args = getArgs(namespace, workspace);
    const path = getPath(namespace, workspace);
    const workspaceSetting = {
        cwd: workspace.uri.fsPath,
        workspace: workspace.uri.toString(),
        args: resolveVariables(args, workspace),
        path: resolveVariables(path, workspace),
        interpreter: resolveVariables(interpreter, workspace),
        importStrategy: config.get<string>('importStrategy', 'fromEnvironment'),
        showNotifications: config.get<string>('showNotifications', 'off'),
    };
    return workspaceSetting;
}

function getGlobalValue<T>(config: WorkspaceConfiguration, key: string): T | undefined {
    const inspect = config.inspect<T>(key);
    return inspect?.globalValue ?? inspect?.defaultValue;
}

export async function getGlobalSettings(namespace: string, includeInterpreter?: boolean): Promise<ISettings> {
    const config = getConfiguration(namespace);

    let interpreter: string[] = [];
    if (includeInterpreter) {
        interpreter = getGlobalValue<string[]>(config, 'interpreter') ?? [];
        if (interpreter === undefined || interpreter.length === 0) {
            interpreter = (await getInterpreterDetails()).path ?? [];
        }
    }

    const setting = {
        cwd: process.cwd(),
        workspace: process.cwd(),
        args: getGlobalValue<string[]>(config, 'args') ?? [],
        path: getGlobalValue<string[]>(config, 'path') ?? [],
        interpreter: interpreter ?? [],
        importStrategy: getGlobalValue<string>(config, 'importStrategy') ?? 'fromEnvironment',
        showNotifications: getGlobalValue<string>(config, 'showNotifications') ?? 'off',
    };
    return setting;
}

export function checkIfConfigurationChanged(e: ConfigurationChangeEvent, namespace: string): boolean {
    const settings = [
        `${namespace}.args`,
        `${namespace}.path`,
        `${namespace}.interpreter`,
        `${namespace}.importStrategy`,
        `${namespace}.showNotifications`,
    ];
    const changed = settings.map((s) => e.affectsConfiguration(s));
    return changed.includes(true);
}
