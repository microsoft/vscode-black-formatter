// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { Disposable } from 'vscode';
import {
    traceLog,
    registerDocumentFormattingEditProvider,
    getDocumentSelector,
    ToolExtensionContext,
    PythonEnvironmentsProvider,
} from '@vscode/common-python-lsp';
import { State } from 'vscode-languageclient/node';

let disposables: Disposable[] = [];
export function registerEmptyFormatter(): void {
    disposables.push(
        registerDocumentFormattingEditProvider(getDocumentSelector(), {
            provideDocumentFormattingEdits: function () {
                traceLog('Formatting requested before server has started.');
                return Promise.resolve(undefined);
            },
        }),
    );
}

export function unregisterEmptyFormatter(): void {
    if (disposables.length > 0) {
        disposables.forEach((d) => d.dispose());
        disposables = [];
    }
}

// How often (ms) to check whether the language client object has been created.
// The client is created asynchronously by the shared activation library, so the
// extension cannot hook into its creation directly. 500ms keeps the placeholder
// removal responsive without adding meaningful overhead during the brief startup
// window.
const SERVER_POLL_INTERVAL = 500;
// Stop a polling burst after this many attempts (120 * 500ms ≈ 60s). Polling
// only needs to run until the language client object exists; once attached, a
// state listener takes over and catches the transition to `Running` whenever it
// happens. If the budget is exhausted (e.g. no interpreter is configured), the
// placeholder formatter intentionally stays registered — there is no second
// formatter yet, so no duplicate — and a fresh burst is started on the next
// interpreter change.
const SERVER_POLL_MAX_ATTEMPTS = 120;

/**
 * Dispose the placeholder formatter once the real language server formatter is
 * registered.
 *
 * The placeholder formatter (see {@link registerEmptyFormatter}) exists only to
 * bridge the gap before the language server starts. Once the server is running
 * it registers its own document formatting provider, so the placeholder must be
 * removed; otherwise VS Code sees two formatters from the same extension and
 * prompts the user to pick a default formatter (see issue #752).
 *
 * The language client is owned by the shared activation library and recreated
 * on every restart, so this watches `toolContext.lsClient` for the first client
 * to reach the `Running` state and unregisters the placeholder at that point.
 */
export function unregisterEmptyFormatterOnServerStart(
    toolContext: ToolExtensionContext,
    pythonProvider: PythonEnvironmentsProvider,
): Disposable {
    let unregistered = false;
    let watchedClient: ToolExtensionContext['lsClient'];
    let stateListener: Disposable | undefined;
    let pollTimer: ReturnType<typeof setInterval> | undefined;

    const stopPolling = (): void => {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = undefined;
        }
    };

    const finish = (): void => {
        unregistered = true;
        unregisterEmptyFormatter();
        stateListener?.dispose();
        stateListener = undefined;
        stopPolling();
    };

    // Attach to the current language client (if any) and unregister the
    // placeholder once it is running.
    const bind = (): void => {
        if (unregistered) {
            return;
        }
        const client = toolContext.lsClient;
        if (!client || client === watchedClient) {
            return;
        }
        watchedClient = client;
        stateListener?.dispose();
        stateListener = client.onDidChangeState((e) => {
            if (e.newState === State.Running) {
                finish();
            }
        });
        if (client.state === State.Running) {
            finish();
        }
    };

    // The language client is created asynchronously after a start is triggered
    // (initial activation, interpreter change, restart, etc.), so poll briefly
    // to catch the client once it exists. Polling stops as soon as the
    // placeholder is unregistered, a client is attached (the state listener then
    // takes over), or the attempt budget is exhausted.
    const startPolling = (): void => {
        if (unregistered || pollTimer) {
            return;
        }
        let attempts = 0;
        pollTimer = setInterval(() => {
            bind();
            attempts += 1;
            if (unregistered || watchedClient || attempts >= SERVER_POLL_MAX_ATTEMPTS) {
                stopPolling();
            }
        }, SERVER_POLL_INTERVAL);
    };

    // Restart polling whenever the interpreter changes — that triggers a server
    // (re)start and is the path used when no interpreter is configured up front.
    const interpreterListener = pythonProvider.onDidChangeInterpreter(() => {
        bind();
        startPolling();
    });

    bind();
    startPolling();

    return {
        dispose: () => {
            interpreterListener.dispose();
            stateListener?.dispose();
            stopPolling();
        },
    };
}
