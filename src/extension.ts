// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as vscode from 'vscode';
import {
    createToolContext,
    deactivateServer,
    loadServerDefaults,
    PythonEnvironmentsProvider,
    registerCommonSubscriptions,
    registerLogger,
    ToolExtensionContext,
} from '@vscode/common-python-lsp';
import { EXTENSION_ROOT_DIR, BLACK_TOOL_CONFIG } from './common/constants';
import { logDefaultFormatter, logLegacySettings } from './common/settings';
import { registerEmptyFormatter } from './common/nullFormatter';

let toolContext: ToolExtensionContext | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    await vscode.commands.executeCommand('setContext', 'black-formatter.activated', true);
    const serverInfo = loadServerDefaults(EXTENSION_ROOT_DIR);
    const serverName = `${serverInfo.name} Formatter`;

    const outputChannel = vscode.window.createOutputChannel(serverName, { log: true });
    context.subscriptions.push(outputChannel, registerLogger(outputChannel));

    const resolvedServerInfo = { ...serverInfo, name: serverName };

    const pythonProvider = new PythonEnvironmentsProvider(BLACK_TOOL_CONFIG);
    context.subscriptions.push(pythonProvider);

    toolContext = createToolContext({
        serverInfo: resolvedServerInfo,
        outputChannel,
        toolConfig: BLACK_TOOL_CONFIG,
        pythonProvider,
    });
    context.subscriptions.push({ dispose: () => toolContext?.dispose() });

    registerCommonSubscriptions(context, {
        serverInfo: resolvedServerInfo,
        outputChannel,
        toolConfig: BLACK_TOOL_CONFIG,
        toolContext,
        pythonProvider,
    });

    registerEmptyFormatter();
    logDefaultFormatter();
    logLegacySettings();

    setImmediate(() => toolContext!.initialize(context.subscriptions));
}

export async function deactivate(): Promise<void> {
    await deactivateServer(toolContext);
}
