// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

// Extension-specific settings: ISettings type, server transport, and legacy settings logging.
// All shared settings resolution is handled by @vscode/common-python-lsp directly.

import { Uri } from 'vscode';
import {
    IBaseSettings,
    getConfiguration,
    getWorkspaceFolders,
    logLegacySettings as _logLegacySettings,
    traceInfo,
    traceWarn,
} from '@vscode/common-python-lsp';
import { EXTENSION_ID } from './constants';
import { TransportKind } from 'vscode-languageclient/node';

export type ISettings = IBaseSettings;

export function getServerTransport(namespace: string, uri: Uri): TransportKind {
    const config = getConfiguration(namespace, uri);
    const value = config.get<string>('serverTransport', 'stdio');
    return value === 'pipe' ? TransportKind.pipe : TransportKind.stdio;
}

export function logDefaultFormatter(): void {
    getWorkspaceFolders().forEach((workspace) => {
        let config = getConfiguration('editor', { uri: workspace.uri, languageId: 'python' });
        if (!config) {
            config = getConfiguration('editor', workspace.uri);
            if (!config) {
                traceInfo('Unable to get editor configuration');
            }
        }
        const formatter = config.get<string>('defaultFormatter', '');
        traceInfo(`Default formatter is set to ${formatter} for workspace ${workspace.uri.fsPath}`);
        if (formatter !== EXTENSION_ID) {
            traceWarn(`Black Formatter is NOT set as the default formatter for workspace ${workspace.uri.fsPath}`);
            traceWarn('To set Black Formatter as the default formatter, add the following to your settings.json file:');
            traceWarn(`\n"[python]": {\n    "editor.defaultFormatter": "${EXTENSION_ID}"\n}`);
        }
    });
}

export function logLegacySettings(): void {
    _logLegacySettings('black-formatter', [
        { legacyKey: 'formatting.blackArgs', newKey: 'args', isArray: true },
        { legacyKey: 'formatting.blackPath', newKey: 'path' },
    ]);
}
