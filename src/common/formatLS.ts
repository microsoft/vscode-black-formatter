// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as path from 'path';
import { Disposable, OutputChannel, Uri, WorkspaceFolder } from 'vscode';
import { State } from 'vscode-languageclient';
import {
    LanguageClient,
    LanguageClientOptions,
    RevealOutputChannelOn,
    ServerOptions,
} from 'vscode-languageclient/node';
import { FORMATTER_SCRIPT_PATH } from './constants';
import { traceInfo, traceVerbose } from './logging/api';
import { getInterpreterDetails } from './python';
import { ISettings } from './settings';
import { traceLevelToLSTrace } from './utilities';
import { getWorkspaceFolder, getWorkspaceFolders, isVirtualWorkspace } from './vscodeapi';

export type IFormatterInitOptions = { settings: ISettings };

let _disposables: Disposable[] = [];

function getProjectRoot(): WorkspaceFolder {
    const workspaces: readonly WorkspaceFolder[] = getWorkspaceFolders();
    if (workspaces.length === 1) {
        return workspaces[0];
    } else {
        let root = workspaces[0];
        for (const w of workspaces) {
            if (root.uri.fsPath.length > w.uri.fsPath.length) {
                root = w;
            }
        }
        return root;
    }
}

export async function createFormatServer(
    interpreter: string[],
    serverId: string,
    serverName: string,
    outputChannel: OutputChannel,
    initializationOptions: IFormatterInitOptions,
    workspaceFolder: WorkspaceFolder,
): Promise<LanguageClient> {
    const command = interpreter[0];
    const serverOptions: ServerOptions = {
        command,
        args: interpreter.slice(1).concat([FORMATTER_SCRIPT_PATH]),
        options: { cwd: workspaceFolder.uri.fsPath },
    };

    const root = workspaceFolder.uri.fsPath.replace(/\\/g, '/');
    const pattern = `${root}/**`;

    // Options to control the language client
    const clientOptions: LanguageClientOptions = {
        // Register the server for python documents
        documentSelector: isVirtualWorkspace()
            ? [{ language: 'python' }]
            : [
                  { scheme: 'file', language: 'python', pattern },
                  { scheme: 'untitled', language: 'python', pattern },
                  { scheme: 'vscode-notebook', language: 'python', pattern },
                  { scheme: 'vscode-notebook-cell', language: 'python', pattern },
              ],
        outputChannel: outputChannel,
        traceOutputChannel: outputChannel,
        revealOutputChannelOn: RevealOutputChannelOn.Never,
        initializationOptions,
        workspaceFolder,
    };

    const client = new LanguageClient(serverId, serverName, serverOptions, clientOptions);
    client.trace = traceLevelToLSTrace(initializationOptions.settings.trace);

    return client;
}

const _lsClients: Map<string, LanguageClient> = new Map();
export async function restartFormatServer(
    resource: Uri | undefined,
    serverId: string,
    serverName: string,
    outputChannel: OutputChannel,
    initializationOptions: IFormatterInitOptions,
): Promise<void> {
    const workspaceFolder = resource ? getWorkspaceFolder(resource) : getProjectRoot();
    if (workspaceFolder) {
        const lsClient = _lsClients.get(workspaceFolder.uri.toString());
        if (lsClient) {
            traceInfo(`Server: Stop requested`);
            await lsClient.stop();
            _disposables.forEach((d) => d.dispose());
        }

        const interpreter = await getInterpreterDetails(workspaceFolder.uri);
        if (interpreter.path) {
            const newLSClient = await createFormatServer(
                interpreter.path,
                serverId,
                serverName,
                outputChannel,
                initializationOptions,
                workspaceFolder,
            );
            _lsClients.set(workspaceFolder.uri.toString(), newLSClient);
            traceInfo(`Server: Start requested.`);
            _disposables.push(
                newLSClient.onDidChangeState((e) => {
                    switch (e.newState) {
                        case State.Stopped:
                            traceVerbose(`Server State: Stopped`);
                            break;
                        case State.Starting:
                            traceVerbose(`Server State: Starting`);
                            break;
                        case State.Running:
                            traceVerbose(`Server State: Running`);
                            break;
                    }
                }),
                newLSClient.start(),
            );
        }
    }
}
