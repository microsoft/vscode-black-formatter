// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

// Extension-specific settings: ISettings type, server transport, and legacy settings logging.
// All shared settings resolution is handled by @vscode/common-python-lsp directly.

import { Uri } from 'vscode';
import { IBaseSettings, getConfiguration, getWorkspaceFolders, traceInfo, traceWarn } from '@vscode/common-python-lsp';
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
    getWorkspaceFolders().forEach((workspace) => {
        try {
            const legacyConfig = getConfiguration('python', workspace.uri);
            const legacyArgs = legacyConfig.get<string[]>('formatting.blackArgs', []);
            const legacyPath = legacyConfig.get<string>('formatting.blackPath', '');
            if (legacyArgs.length > 0) {
                traceWarn(`"python.formatting.blackArgs" is deprecated. Use "black-formatter.args" instead.`);
                traceWarn(`"python.formatting.blackArgs" for workspace ${workspace.uri.fsPath}:`);
                traceWarn(`\n${JSON.stringify(legacyArgs, null, 4)}`);
            }

            if (legacyPath.length > 0 && legacyPath !== 'black') {
                traceWarn(`"python.formatting.blackPath" is deprecated. Use "black-formatter.path" instead.`);
                traceWarn(`"python.formatting.blackPath" for workspace ${workspace.uri.fsPath}:`);
                traceWarn(`\n${JSON.stringify(legacyPath, null, 4)}`);
            }
        } catch (err) {
            traceWarn(`Error while logging legacy settings: ${err}`);
        }
    });
}
