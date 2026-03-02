// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

/* eslint-disable @typescript-eslint/naming-convention */
import { Event, Uri } from 'vscode';

export interface PythonCommandRunConfiguration {
    executable: string;
    args?: string[];
}

export interface PythonEnvironmentExecutionInfo {
    run: PythonCommandRunConfiguration;
    activatedRun?: PythonCommandRunConfiguration;
    activation?: PythonCommandRunConfiguration[];
}

export interface PythonEnvironmentInfo {
    name: string;
    displayName: string;
    version: string;
    environmentPath: Uri;
    execInfo: PythonEnvironmentExecutionInfo;
    sysPrefix: string;
}

export interface PythonEnvironmentId {
    id: string;
    managerId: string;
}

export interface PythonEnvironment extends PythonEnvironmentInfo {
    envId: PythonEnvironmentId;
}

export type GetEnvironmentScope = undefined | Uri;

export interface DidChangeEnvironmentEventArgs {
    uri: Uri | undefined;
    old: PythonEnvironment | undefined;
    new: PythonEnvironment | undefined;
}

export type ResolveEnvironmentContext = Uri;

export interface PythonEnvironmentsAPI {
    getEnvironment(scope: GetEnvironmentScope): Promise<PythonEnvironment | undefined>;
    resolveEnvironment(context: ResolveEnvironmentContext): Promise<PythonEnvironment | undefined>;
    onDidChangeEnvironment: Event<DidChangeEnvironmentEventArgs>;
}
