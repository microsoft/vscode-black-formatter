// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as fsapi from 'fs-extra';
import { Disposable, env, l10n, LanguageStatusSeverity, LogOutputChannel, Uri, WorkspaceFolder } from 'vscode';
import { State } from 'vscode-languageclient';
import {
    LanguageClient,
    LanguageClientOptions,
    RevealOutputChannelOn,
    ServerOptions,
    TransportKind,
} from 'vscode-languageclient/node';
import { DEBUG_SERVER_SCRIPT_PATH, SERVER_SCRIPT_PATH } from './constants';
import { traceError, traceInfo, traceVerbose } from './logging';
import { getDebuggerPath } from './python';
import { getExtensionSettings, getGlobalSettings, getServerTransport, ISettings } from './settings';
import { getDocumentSelector, getLSClientTraceLevel } from './utilities';
import { updateStatus } from './status';
import { unregisterEmptyFormatter } from './nullFormatter';

export type IInitOptions = { settings: ISettings[]; globalSettings: ISettings };

async function createServer(
    settings: ISettings,
    serverId: string,
    serverName: string,
    outputChannel: LogOutputChannel,
    initializationOptions: IInitOptions,
): Promise<LanguageClient> {
    const command = settings.interpreter[0];
    const workspaceUri = Uri.parse(settings.workspace);
    const cwd = settings.cwd === '${fileDirname}' ? workspaceUri.fsPath : settings.cwd;

    // Set debugger path needed for debugging python code.
    const newEnv = { ...process.env };
    const debuggerPath = await getDebuggerPath();
    const isDebugScript = await fsapi.pathExists(DEBUG_SERVER_SCRIPT_PATH);
    if (newEnv.USE_DEBUGPY && debuggerPath) {
        newEnv.DEBUGPY_PATH = debuggerPath;
    } else {
        newEnv.USE_DEBUGPY = 'False';
    }

    // Set import strategy
    newEnv.LS_IMPORT_STRATEGY = settings.importStrategy;

    // Set notification type
    newEnv.LS_SHOW_NOTIFICATION = settings.showNotifications;

    const args =
        newEnv.USE_DEBUGPY === 'False' || !isDebugScript
            ? settings.interpreter.slice(1).concat([SERVER_SCRIPT_PATH])
            : settings.interpreter.slice(1).concat([DEBUG_SERVER_SCRIPT_PATH]);
    traceInfo(`Server run command: ${[command, ...args].join(' ')}`);

    const serverOptions: ServerOptions = {
        command,
        args,
        options: { cwd, env: newEnv },
        transport: getServerTransport(serverId, workspaceUri),
    };

    // Options to control the language client
    const clientOptions: LanguageClientOptions = {
        // Register the server for python documents
        documentSelector: getDocumentSelector(),
        outputChannel: outputChannel,
        traceOutputChannel: outputChannel,
        revealOutputChannelOn: RevealOutputChannelOn.Never,
        initializationOptions,
    };

    return new LanguageClient(serverId, serverName, serverOptions, clientOptions);
}

let _disposables: Disposable[] = [];
export async function restartServer(
    workspaceSetting: ISettings,
    serverId: string,
    serverName: string,
    outputChannel: LogOutputChannel,
    lsClient?: LanguageClient,
): Promise<LanguageClient | undefined> {
    if (lsClient) {
        traceInfo(`Server: Stop requested`);
        try {
            await lsClient.stop();
        } catch (ex) {
            traceError(`Server: Stop failed: ${ex}`);
        }
        _disposables.forEach((d) => d.dispose());
        _disposables = [];
    }
    updateStatus(undefined, LanguageStatusSeverity.Information, true);

    const newLSClient = await createServer(workspaceSetting, serverId, serverName, outputChannel, {
        settings: await getExtensionSettings(serverId, true),
        globalSettings: await getGlobalSettings(serverId, false),
    });

    traceInfo(`Server: Start requested.`);
    _disposables.push(
        newLSClient.onDidChangeState((e) => {
            switch (e.newState) {
                case State.Stopped:
                    traceVerbose(`Server State: Stopped`);
                    break;
                case State.Starting:
                    traceVerbose(`Server State: Starting`);
                    unregisterEmptyFormatter();
                    break;
                case State.Running:
                    traceVerbose(`Server State: Running`);
                    updateStatus(undefined, LanguageStatusSeverity.Information, false);
                    break;
            }
        }),
    );
    try {
        await newLSClient.start();
    } catch (ex) {
        updateStatus(l10n.t('Server failed to start.'), LanguageStatusSeverity.Error);
        traceError(`Server: Start failed: ${ex}`);
    }
    await newLSClient.setTrace(getLSClientTraceLevel(outputChannel.logLevel, env.logLevel));
    return newLSClient;
}
