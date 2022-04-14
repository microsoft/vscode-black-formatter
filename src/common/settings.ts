// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { ConfigurationChangeEvent } from 'vscode';
import { getInterpreterDetails } from './python';
import { LoggingLevelSettingType } from './types';
import { getConfiguration, getWorkspaceFolders } from './vscodeapi';

export interface ISettings {
    workspace: string;
    trace: LoggingLevelSettingType;
    args: string[];
    path: string[];
    interpreter: string[];
}

export async function getFormatterExtensionSettings(
    moduleName: string,
    includeInterpreter?: boolean,
): Promise<ISettings[]> {
    const settings: ISettings[] = [];
    const workspaces = getWorkspaceFolders();

    for (const workspace of workspaces) {
        const config = getConfiguration(`${moduleName}-formatter`, workspace.uri);
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

export function checkIfConfigurationChanged(e: ConfigurationChangeEvent, moduleName: string): boolean {
    const settings = [`${moduleName}-formatter.trace`, `${moduleName}-formatter.args`, `${moduleName}-formatter.path`];
    const changed = settings.map((s) => e.affectsConfiguration(s));
    return changed.includes(true);
}
