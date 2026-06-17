// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import { assert } from 'chai';
import * as sinon from 'sinon';
import { Disposable, EventEmitter, languages } from 'vscode';
import { State } from 'vscode-languageclient/node';
import {
    registerEmptyFormatter,
    unregisterEmptyFormatter,
    unregisterEmptyFormatterOnServerStart,
} from '../../../../common/nullFormatter';

// Minimal fakes for the shared activation library types. We only exercise the
// members touched by `unregisterEmptyFormatterOnServerStart`.
interface FakeClient {
    state: State;
    onDidChangeState: EventEmitter<{ newState: State }>['event'];
}

suite('Empty (placeholder) formatter Tests', () => {
    let registerStub: sinon.SinonStub;
    let formatterDispose: sinon.SinonSpy;
    let stateEmitter: EventEmitter<{ newState: State }>;
    let interpreterEmitter: EventEmitter<void>;
    const watchers: Disposable[] = [];

    setup(() => {
        formatterDispose = sinon.spy();
        registerStub = sinon
            .stub(languages, 'registerDocumentFormattingEditProvider')
            .returns({ dispose: formatterDispose });
        stateEmitter = new EventEmitter<{ newState: State }>();
        interpreterEmitter = new EventEmitter<void>();
    });

    teardown(() => {
        watchers.forEach((w) => w.dispose());
        watchers.length = 0;
        // Reset module-level state so tests stay isolated.
        unregisterEmptyFormatter();
        stateEmitter.dispose();
        interpreterEmitter.dispose();
        sinon.restore();
    });

    function makeToolContext(client: FakeClient | undefined): {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        toolContext: any;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        pythonProvider: any;
    } {
        return {
            toolContext: { lsClient: client },
            pythonProvider: { onDidChangeInterpreter: interpreterEmitter.event },
        };
    }

    test('registers a document formatting provider', () => {
        registerEmptyFormatter();
        assert.ok(registerStub.calledOnce, 'placeholder formatter should be registered once');
    });

    test('unregisters placeholder when client is already running', () => {
        registerEmptyFormatter();
        const client: FakeClient = { state: State.Running, onDidChangeState: stateEmitter.event };
        const { toolContext, pythonProvider } = makeToolContext(client);

        watchers.push(unregisterEmptyFormatterOnServerStart(toolContext, pythonProvider));

        assert.ok(formatterDispose.calledOnce, 'placeholder formatter should be disposed when server already running');
    });

    test('unregisters placeholder once client transitions to running', () => {
        registerEmptyFormatter();
        const client: FakeClient = { state: State.Starting, onDidChangeState: stateEmitter.event };
        const { toolContext, pythonProvider } = makeToolContext(client);

        watchers.push(unregisterEmptyFormatterOnServerStart(toolContext, pythonProvider));
        assert.ok(formatterDispose.notCalled, 'placeholder formatter should remain until server is running');

        stateEmitter.fire({ newState: State.Starting });
        assert.ok(formatterDispose.notCalled, 'placeholder formatter should remain while starting');

        stateEmitter.fire({ newState: State.Running });
        assert.ok(formatterDispose.calledOnce, 'placeholder formatter should be disposed when server reaches running');
    });

    test('does not unregister placeholder while no client exists', () => {
        registerEmptyFormatter();
        const { toolContext, pythonProvider } = makeToolContext(undefined);

        watchers.push(unregisterEmptyFormatterOnServerStart(toolContext, pythonProvider));

        assert.ok(formatterDispose.notCalled, 'placeholder formatter should remain when server has not started');
    });
});
