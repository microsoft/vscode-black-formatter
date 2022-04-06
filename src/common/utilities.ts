// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { Trace } from 'vscode-jsonrpc/node';

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
