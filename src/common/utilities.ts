// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as fs from 'fs-extra';
import * as path from 'path';
import { ConfigurationScope, env, LogLevel, Uri, WorkspaceFolder, Disposable, RelativePattern,FileSystemWatcher, workspace } from 'vscode';
import { Trace, TraceValues } from 'vscode-jsonrpc/node';
import { getConfiguration, getWorkspaceFolders, isVirtualWorkspace } from './vscodeapi';
import { DocumentSelector } from 'vscode-languageclient';
import { traceLog, traceInfo } from './logging';

function logLevelToTrace(logLevel: LogLevel): Trace {
    switch (logLevel) {
        case LogLevel.Error:
        case LogLevel.Warning:
        case LogLevel.Info:
            return Trace.Messages;

        case LogLevel.Debug:
        case LogLevel.Trace:
            return Trace.Verbose;

        case LogLevel.Off:
        default:
            return Trace.Off;
    }
}

export function getLSClientTraceLevel(channelLogLevel: LogLevel, globalLogLevel: LogLevel): Trace {
    if (channelLogLevel === LogLevel.Off) {
        return logLevelToTrace(globalLogLevel);
    }
    if (globalLogLevel === LogLevel.Off) {
        return logLevelToTrace(channelLogLevel);
    }
    const level = logLevelToTrace(channelLogLevel <= globalLogLevel ? channelLogLevel : globalLogLevel);
    return level;
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
        let rootWorkspace = workspaces[0];
        let root = undefined;
        for (const w of workspaces) {
            if (await fs.pathExists(w.uri.fsPath)) {
                root = w.uri.fsPath;
                rootWorkspace = w;
                break;
            }
        }

        for (const w of workspaces) {
            if (root && root.length > w.uri.fsPath.length && (await fs.pathExists(w.uri.fsPath))) {
                root = w.uri.fsPath;
                rootWorkspace = w;
            }
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

export function getInterpreterFromSetting(namespace: string, scope?: ConfigurationScope) {
    const config = getConfiguration(namespace, scope);
    return config.get<string[]>('interpreter');
}

const CONFIG_FILES = ['.black', 'pyproject.toml'];
export function createConfigFileWatcher(onConfigChanged: () => Promise<void>): Disposable {
    const watchers: FileSystemWatcher[] = [];
    
    const homeDir = process.env.HOME || process.env.USERPROFILE;
    if (homeDir) {
        for (const configFile of CONFIG_FILES) {
            watchConfigFile(path.join(homeDir, configFile));
        }
    }

    function watchConfigFile(filePath: string): void {
        if (fs.existsSync(filePath)) {
            traceLog(`Watching config file: ${filePath}`);
            const pattern = new RelativePattern(
                path.dirname(filePath),
                path.basename(filePath)
            );
            
            const watcher = workspace.createFileSystemWatcher(pattern);
            
            watcher.onDidChange(async () => {
                traceInfo(`Config file changed: ${filePath}`);
                await onConfigChanged();
            });
            
            watchers.push(watcher);
        }
    }

    // Disposable オブジェクトを返す
    return {
        dispose: () => {
            for (const watcher of watchers) {
                watcher.dispose();
            }
        }
    };
}
