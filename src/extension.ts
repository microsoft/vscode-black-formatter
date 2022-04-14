// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { restartFormatServer } from './common/formatLS';
import { initializeFileLogging, registerLogger, setLoggingLevel, traceLog, traceVerbose } from './common/logging';
import { OutputChannelLogger } from './common/outputChannelLogger';
import { getInterpreterDetails, initializePython, onDidChangePythonInterpreter } from './common/python';
import { checkIfConfigurationChanged, getFormatterExtensionSettings, ISettings } from './common/settings';
import { loadFormatterDefaults } from './common/setup';
import { createOutputChannel, onDidChangeConfiguration, registerCommand } from './common/vscodeapi';

function setupLogging(settings: ISettings[], outputChannel: vscode.OutputChannel, disposables: vscode.Disposable[]) {
    // let error: unknown;
    if (settings.length > 0) {
        setLoggingLevel(settings[0].trace);

        // if (settings.logPath && settings.logPath.length > 0) {
        //     error = initializeFileLogging(settings.logPath, disposables);
        // }
    }

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

    const settings = await getFormatterExtensionSettings(formatter.module);

    const formatterName = `${formatter.name} Formatter`;
    const formatterId = `${formatter.module}-formatter`;

    // Setup logging
    const outputChannel = createOutputChannel(formatterName);
    context.subscriptions.push(outputChannel);
    setupLogging(settings, outputChannel, context.subscriptions);

    traceLog(`Formatter Name: ${formatter.name}`);
    traceLog(`Formatter Module: ${formatter.module}`);
    traceVerbose(`Formatter configuration: ${JSON.stringify(formatter)}`);

    const runServer = async () => {
        const interpreter = await getInterpreterDetails();
        if (interpreter.path) {
            lsClient = await restartFormatServer(
                interpreter.path,
                formatterId,
                formatterName,
                outputChannel,
                {
                    settings: await getFormatterExtensionSettings(formatter.module, true),
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
        registerCommand(`${formatter.module}-formatter.restart`, async () => {
            await runServer();
        }),
    );

    context.subscriptions.push(
        onDidChangeConfiguration(async (e: vscode.ConfigurationChangeEvent) => {
            if (checkIfConfigurationChanged(e, formatter.module)) {
                const newSettings = await getFormatterExtensionSettings(formatter.module);
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
