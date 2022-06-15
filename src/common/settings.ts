// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { ConfigurationChangeEvent } from 'vscode';
import { getInterpreterDetails } from './python';
import { LoggingLevelSettingType } from './log/types';
import { getConfiguration, getWorkspaceFolders } from './vscodeapi';

export interface ISettings {
    workspace: string;
    trace: LoggingLevelSettingType;
    args: string[];
    path: string[];
    interpreter: string[];
}

export async function getExtensionSettings(namespace: string, includeInterpreter?: boolean): Promise<ISettings[]> {
    const settings: ISettings[] = [];
    const workspaces = getWorkspaceFolders();

    for (const workspace of workspaces) {
        const config = getConfiguration(namespace, workspace.uri);
        const interpreter = includeInterpreter ? (await getInterpreterDetails(workspace.uri)).path : [];
        const workspaceSetting = {
            workspace: workspace.uri.toString(),
            trace: config.get<LoggingLevelSettingType>(`trace`) ?? 'error',
            args: config.get<string[]>(`args`) ?? [],
            severity: config.get<Record<string, string>>(`severity`) ?? {},
            path: config.get<string[]>(`path`) ?? [],
            interpreter: interpreter ?? [],
        };

        settings.push(workspaceSetting);
    }

    return settings;
}

export function checkIfConfigurationChanged(e: ConfigurationChangeEvent, namespace: string): boolean {
    const settings = [`${namespace}.trace`, `${namespace}.args`, `${namespace}.path`];
    const changed = settings.map((s) => e.affectsConfiguration(s));
    return changed.includes(true);
}
