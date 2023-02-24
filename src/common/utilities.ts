// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as path from 'path';
import * as fsapi from 'fs-extra';
import { Uri, WorkspaceFolder } from 'vscode';
import { Trace } from 'vscode-jsonrpc/node';
import { DocumentSelector } from 'vscode-languageclient';
import { getWorkspaceFolders, isVirtualWorkspace } from './vscodeapi';

export function getTimeForLogging(): string {
    const date = new Date();
    return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}.${date.getMilliseconds()}`;
}

export function traceLevelToLSTrace(level: string): Trace {
    switch (level) {
        case 'error':
        case 'warn':
        case 'info':
            return Trace.Messages;
        case 'debug':
            return Trace.Verbose;
        default:
            return Trace.Off;
    }
}

export async function getProjectRoot(): Promise<WorkspaceFolder> {
    const workspaces: readonly WorkspaceFolder[] = getWorkspaceFolders();
    if (workspaces.length === 0) {
        return {
            uri: Uri.file(process.cwd()),
            name: path.basename(process.cwd()),
            index: 0,
        };
    } else if (workspaces.length === 1) {
        return workspaces[0];
    } else {
        let rootWorkspace: WorkspaceFolder | undefined;
        for (const w of workspaces) {
            if (await fsapi.pathExists(w.uri.fsPath)) {
                if (!rootWorkspace) {
                    rootWorkspace = w;
                }

                if (rootWorkspace.uri.fsPath.length > w.uri.fsPath.length) {
                    rootWorkspace = w;
                }
            }
        }

        if (!rootWorkspace) {
            return {
                uri: Uri.file(process.cwd()),
                name: path.basename(process.cwd()),
                index: 0,
            };
        }
        return rootWorkspace;
    }
}

export function getDocumentSelector(): DocumentSelector {
    return isVirtualWorkspace()
        ? [{ language: 'python' }]
        : [
              { scheme: 'file', language: 'python' },
              { scheme: 'untitled', language: 'python' },
              { scheme: 'vscode-notebook', language: 'python' },
              { scheme: 'vscode-notebook-cell', language: 'python' },
          ];
}
