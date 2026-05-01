// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

// Thin wrapper: delegates to vscode-common-python-lsp shared package.

import { Disposable, LogOutputChannel } from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import {
    IBaseSettings,
    getServerCwd as _getServerCwd,
    restartServer as _restartServer,
} from '@vscode/common-python-lsp';
import { BLACK_TOOL_CONFIG } from './constants';
import { traceError } from './logging';
import { getPythonProvider } from './python';
import { ISettings } from './settings';

export function getServerCwd(settings: ISettings): string {
    // ISettings is structurally compatible but lacks the index signature IBaseSettings requires
    return _getServerCwd(settings as unknown as IBaseSettings);
}

let _disposables: Disposable[] = [];

export async function restartServer(
    workspaceSetting: ISettings,
    serverId: string,
    serverName: string,
    outputChannel: LogOutputChannel,
    oldLsClient?: LanguageClient,
): Promise<LanguageClient | undefined> {
    _disposables.forEach((d) => {
        try {
            d.dispose();
        } catch (ex) {
            traceError(`Failed to dispose: ${ex}`);
        }
    });
    _disposables = [];

    const result = await _restartServer(
        {
            settings: workspaceSetting as unknown as IBaseSettings,
            serverId,
            serverName,
            outputChannel,
            toolConfig: BLACK_TOOL_CONFIG,
            pythonProvider: getPythonProvider(),
        },
        oldLsClient as unknown as undefined,
    );

    _disposables = result.disposables;
    return result.client as unknown as LanguageClient | undefined;
}
