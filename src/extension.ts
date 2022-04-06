// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { restartFormatServer } from './common/formatLS';
import { initializeFileLogging, registerLogger, setLoggingLevel, traceLog, traceVerbose } from './common/logging';
import { OutputChannelLogger } from './common/outputChannelLogger';
import { getInterpreterPath, initializePython, onDidChangePythonInterpreter } from './common/python';
import { checkIfConfigurationChanged, getFormatterExtensionSettings, ISettings } from './common/settings';
import { loadFormatterDefaults } from './common/setup';
import { createOutputChannel, onDidChangeConfiguration, registerCommand } from './common/vscodeapi';

function setupLogging(settings: ISettings, outputChannel: vscode.OutputChannel, disposables: vscode.Disposable[]) {
    setLoggingLevel(settings.trace);

    // let error: unknown;
    // if (settings.logPath && settings.logPath.length > 0) {
    //     error = initializeFileLogging(settings.logPath, disposables);
    // }

    disposables.push(registerLogger(new OutputChannelLogger(outputChannel)));

    // if (error) {
    //     // Capture and show log file creation error in the output channel
    //     traceLog(`Failed to create log file: ${settings.logPath} \r\n`, error);
    // }
}

let lsClient: LanguageClient | undefined;
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // This is required to get formatter name and module. This should be
    // the first thing that we do in this extension.
    const formatter = loadFormatterDefaults();

    const settings = getFormatterExtensionSettings(formatter.module);

    const formatterName = `${formatter.name} Formatter`;
    const formatterId = `${formatter.module}-formatter`;

    // Setup logging
    const outputChannel = createOutputChannel(formatterName);
    context.subscriptions.push(outputChannel);
    setupLogging(settings, outputChannel, context.subscriptions);

    traceLog(`Formatter Name: ${formatter.name}`);
    traceLog(`Formatter Module: ${formatter.module}`);
    traceVerbose(`Formatter configuration: ${JSON.stringify(formatter)}`);

    const runServer = async (interpreterPath: string) => {
        lsClient = await restartFormatServer(
            interpreterPath,
            formatterId,
            formatterName,
            outputChannel,
            {
                settings: getFormatterExtensionSettings(formatter.module),
            },
            lsClient,
        );
    };

    context.subscriptions.push(
        onDidChangePythonInterpreter(async (interpreterPath: string) => {
            await runServer(interpreterPath);
        }),
    );

    context.subscriptions.push(
        registerCommand(`${formatter.module}-formatter.restart`, async () => {
            const interpreterPath = await getInterpreterPath(context.subscriptions);
            await runServer(interpreterPath);
        }),
    );

    context.subscriptions.push(
        onDidChangeConfiguration(async (e: vscode.ConfigurationChangeEvent) => {
            if (checkIfConfigurationChanged(e, formatter.module)) {
                const newSettings = getFormatterExtensionSettings(formatter.module);
                setLoggingLevel(newSettings.trace);

                const interpreterPath = await getInterpreterPath(context.subscriptions);
                await runServer(interpreterPath);
            }
        }),
    );

    setImmediate(async () => {
        traceVerbose(`Python extension loading`);
        await initializePython(context.subscriptions);
        traceVerbose(`Python extension loaded`);
    });
}
