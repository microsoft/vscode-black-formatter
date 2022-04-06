// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { ConfigurationChangeEvent, ConfigurationTarget } from 'vscode';
import { LoggingLevelSettingType } from './types';
import { getConfiguration } from './vscodeapi';

export interface ISettings {
    trace: LoggingLevelSettingType;
    args: string[];
    path: string[];
}

export function getFormatterExtensionSettings(moduleName: string): ISettings {
    const config = getConfiguration(moduleName);
    return {
        trace: config.get<LoggingLevelSettingType>(`trace`) ?? 'error',
        args: config.get<string[]>(`args`) ?? [],
        path: config.get<string[]>(`path`) ?? [],
    };
}

export function checkIfConfigurationChanged(e: ConfigurationChangeEvent, moduleName: string): boolean {
    const settings = [`${moduleName}.trace`, `${moduleName}.args`, `${moduleName}.path`];
    const changed = settings.map((s) => e.affectsConfiguration(s));
    return changed.includes(true);
}
