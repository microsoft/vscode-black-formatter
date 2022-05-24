// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as vscode from 'vscode';
import { restartFormatServer } from './common/formatLS';
import { registerLogger, setLoggingLevel, traceLog, traceVerbose } from './common/logging/api';
import { OutputChannelLogger } from './common/logging/outputChannelLogger';
import { IInterpreterDetails, initializePython, onDidChangePythonInterpreter } from './common/python';
import {
    checkIfConfigurationChanged,
    configurationChangedScope,
    getFormatterExtensionSettings,
    ISettings,
} from './common/settings';
import { loadFormatterDefaults } from './common/setup';
import {
    createOutputChannel,
    getWorkspaceFolders,
    onDidChangeConfiguration,
    registerCommand,
} from './common/vscodeapi';

function setupLogging(settings: ISettings[], outputChannel: vscode.OutputChannel, disposables: vscode.Disposable[]) {
    if (settings.length > 0) {
        setLoggingLevel(settings[0].trace);
    }

    disposables.push(registerLogger(new OutputChannelLogger(outputChannel)));
}

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // This is required to get formatter name and module. This should be
    // the first thing that we do in this extension.
    const formatter = loadFormatterDefaults();

    const settings: ISettings[] = [];
    for (const workspace of getWorkspaceFolders()) {
        settings.push(await getFormatterExtensionSettings(formatter.module, workspace.uri));
    }

    const formatterName = `${formatter.name} Formatter`;
    const formatterId = `${formatter.module}-formatter`;

    // Setup logging
    const outputChannel = createOutputChannel(formatterName);
    context.subscriptions.push(outputChannel);
    setupLogging(settings, outputChannel, context.subscriptions);

    traceLog(`Formatter Name: ${formatter.name}`);
    traceLog(`Formatter Module: ${formatter.module}`);
    traceVerbose(`Formatter configuration: ${JSON.stringify(formatter)}`);

    const runServer = async (resource: vscode.Uri | undefined) => {
        await restartFormatServer(resource, formatterId, formatterName, outputChannel, {
            settings: await getFormatterExtensionSettings(formatter.module, resource, true),
        });
    };

    context.subscriptions.push(
        onDidChangePythonInterpreter(async (e: IInterpreterDetails) => {
            await runServer(e.resource);
        }),
    );

    context.subscriptions.push(
        registerCommand(`${formatter.module}-formatter.restart`, async () => {
            await Promise.all(getWorkspaceFolders().map((w) => runServer(w.uri)));
        }),
    );

    context.subscriptions.push(
        onDidChangeConfiguration(async (e: vscode.ConfigurationChangeEvent) => {
            const scope = configurationChangedScope(e, formatter.module);
            if (scope) {
                await runServer(scope.uri);
            }
        }),
    );

    setImmediate(async () => {
        traceVerbose(`Python extension loading`);
        await initializePython(context.subscriptions);
        traceVerbose(`Python extension loaded`);
    });
}
