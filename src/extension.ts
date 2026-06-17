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
import { registerEmptyFormatter, unregisterEmptyFormatterOnServerStart } from './common/nullFormatter';

let toolContext: ToolExtensionContext | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
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
    // Remove the placeholder formatter once the language server registers its
    // own formatter, so VS Code does not see two Black formatters (issue #752).
    context.subscriptions.push(unregisterEmptyFormatterOnServerStart(toolContext, pythonProvider));
    logDefaultFormatter();
    logLegacySettings();

    setImmediate(() => toolContext!.initialize(context.subscriptions));
}

export async function deactivate(): Promise<void> {
    await deactivateServer(toolContext);
}
