// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { restartServer } from './common/server';
import { initializeFileLogging, registerLogger, setLoggingLevel, traceLog, traceVerbose } from './common/log/logging';
import { OutputChannelLogger } from './common/log/outputChannelLogger';
import { getInterpreterDetails, initializePython, onDidChangePythonInterpreter } from './common/python';
import { checkIfConfigurationChanged, getExtensionSettings, ISettings } from './common/settings';
import { loadServerDefaults } from './common/setup';
import { createOutputChannel, onDidChangeConfiguration, registerCommand } from './common/vscodeapi';

let lsClient: LanguageClient | undefined;
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // This is required to get formatter name and module. This should be
    // the first thing that we do in this extension.
    const serverInfo = loadServerDefaults();
    const serverName = `${serverInfo.name} Formatter`;
    const serverId = `${serverInfo.module}-formatter`;

    const settings = await getExtensionSettings(serverId);

    // Setup logging
    const outputChannel = createOutputChannel(serverName);
    context.subscriptions.push(outputChannel);
    setLoggingLevel(settings[0].trace);
    context.subscriptions.push(registerLogger(new OutputChannelLogger(outputChannel)));

    traceLog(`Name: ${serverInfo.name}`);
    traceLog(`Module: ${serverInfo.module}`);
    traceVerbose(`Configuration: ${JSON.stringify(serverInfo)}`);

    const runServer = async () => {
        const interpreter = await getInterpreterDetails();
        if (interpreter.path) {
            lsClient = await restartServer(
                interpreter.path,
                serverId,
                serverName,
                outputChannel,
                {
                    settings: await getExtensionSettings(serverId, true),
                },
                lsClient,
            );
        }
    };

    context.subscriptions.push(
        onDidChangePythonInterpreter(async () => {
            await runServer();
        }),
    );

    context.subscriptions.push(
        registerCommand(`${serverId}.restart`, async () => {
            await runServer();
        }),
    );

    context.subscriptions.push(
        onDidChangeConfiguration(async (e: vscode.ConfigurationChangeEvent) => {
            if (checkIfConfigurationChanged(e, serverId)) {
                const newSettings = await getExtensionSettings(serverId);
                setLoggingLevel(newSettings[0].trace);
                await runServer();
            }
        }),
    );

    setImmediate(async () => {
        traceVerbose(`Python extension loading`);
        await initializePython(context.subscriptions);
        traceVerbose(`Python extension loaded`);
    });
}
