// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { ConfigurationChangeEvent, Uri, WorkspaceFolder } from 'vscode';
import { getInterpreterDetails } from './python';
import { LoggingLevelSettingType } from './logging/types';
import { getConfiguration, getWorkspaceFolder, getWorkspaceFolders } from './vscodeapi';

export interface ISettings {
    workspace: string;
    trace: LoggingLevelSettingType;
    args: string[];
    path: string[];
    interpreter: string[];
}

export async function getFormatterExtensionSettings(
    moduleName: string,
    resource: Uri | undefined,
    includeInterpreter?: boolean,
): Promise<ISettings> {
    const workspace = resource ? getWorkspaceFolder(resource) : undefined;
    if (workspace) {
        const config = getConfiguration(`${moduleName}-formatter`, workspace.uri);
        const interpreter = includeInterpreter ? (await getInterpreterDetails(workspace.uri)).path : [];
        const workspaceSetting = {
            workspace: workspace.uri.toString(),
            trace: config.get<LoggingLevelSettingType>(`trace`) ?? 'error',
            args: config.get<string[]>(`args`) ?? [],
            path: config.get<string[]>(`path`) ?? [],
            interpreter: interpreter ?? [],
        };
        return workspaceSetting;
    }

    const config = getConfiguration(`${moduleName}-formatter`);
    const interpreter = includeInterpreter ? (await getInterpreterDetails()).path : [];

    const settings = {
        workspace: '',
        trace: config.get<LoggingLevelSettingType>(`trace`) ?? 'error',
        args: config.get<string[]>(`args`) ?? [],
        path: config.get<string[]>(`path`) ?? [],
        interpreter: interpreter ?? [],
    };
    return settings;
}

export function checkIfConfigurationChanged(e: ConfigurationChangeEvent, moduleName: string): boolean {
    const settings = [`${moduleName}-formatter.trace`, `${moduleName}-formatter.args`, `${moduleName}-formatter.path`];
    const changed = settings.map((s) => e.affectsConfiguration(s));
    return changed.includes(true);
}

export function configurationChangedScope(
    e: ConfigurationChangeEvent,
    moduleName: string,
): WorkspaceFolder | undefined {
    const settings = [`${moduleName}-formatter.trace`, `${moduleName}-formatter.args`, `${moduleName}-formatter.path`];

    for (const workspace of getWorkspaceFolders()) {
        const changed = settings.map((s) => e.affectsConfiguration(s, workspace));
        if (changed.includes(true)) {
            return workspace;
        }
    }

    return undefined;
}
