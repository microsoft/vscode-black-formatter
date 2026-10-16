// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const assert = require('node:assert/strict');
const { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');
const { rewritePackageLock, rewritePackageLocks } = require('./setup-npm-registry');
const { normalizePackageLock } = require('./normalize-package-lock');

const publicRegistry = 'https://registry.npmjs.org/';
const proxyRegistry = 'https://packagefeedproxy.microsoft.io/npm/';
const source = `${JSON.stringify(
    {
        lockfileVersion: 3,
        packages: {
            '': { name: 'black-formatter' },
            'node_modules/example': {
                version: '1.2.3',
                resolved: `${publicRegistry}example/-/example-1.2.3.tgz`,
                integrity: 'sha512-example',
            },
            'node_modules/@scope/example': {
                resolved: 'https://registry.yarnpkg.com/@scope/example/-/example-1.0.0.tgz',
                integrity: 'sha512-scoped',
            },
        },
    },
    null,
    4,
)}\n`;

test('rewrites public resolved URLs without changing versions, integrity or formatting', () => {
    const expected = source
        .replaceAll(publicRegistry, proxyRegistry)
        .replace('https://registry.yarnpkg.com/', proxyRegistry);
    assert.equal(rewritePackageLock(source), expected);
    assert.equal(rewritePackageLock(expected), expected);
    assert.equal(normalizePackageLock(expected), source.replace('https://registry.yarnpkg.com/', publicRegistry));
});

test('supports version 2 legacy dependencies as well as packages', () => {
    const legacy = JSON.stringify({
        lockfileVersion: 2,
        packages: {},
        dependencies: { example: { resolved: `${publicRegistry}example/-/example.tgz` } },
    });
    assert.equal(rewritePackageLock(legacy), legacy.replace(publicRegistry, proxyRegistry));
});

test('preserves other fields, private feeds, Git dependencies and lookalike hosts', () => {
    const unchanged = JSON.stringify({
        lockfileVersion: 3,
        packages: {
            '': { description: `${publicRegistry}example` },
            private: {
                resolved: 'https://pkgs.dev.azure.com/azure-public/vside/_packaging/msft_consumption/example.tgz',
            },
            git: { resolved: 'git+https://github.com/example/example.git#123' },
            lookalike: { resolved: 'https://registry.npmjs.org.example.com/example.tgz' },
            local: { resolved: 'file:../example' },
        },
    });
    assert.equal(rewritePackageLock(unchanged), unchanged);
});

test('rejects malformed or unsupported lockfiles', () => {
    for (const invalid of ['{', '{}', '{"lockfileVersion":1}', '{"lockfileVersion":3,"packages":[]}']) {
        assert.throws(() => rewritePackageLock(invalid));
    }
});

test('rewrites only the root lockfile without requiring a submodule', (t) => {
    const root = mkdtempSync(path.join(tmpdir(), 'black-formatter-registry-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    const shared = path.join(root, 'external', 'vscode-common-python-lsp', 'typescript');
    mkdirSync(shared, { recursive: true });
    const files = [path.join(root, 'package-lock.json')];
    writeFileSync(path.join(shared, 'package-lock.json'), source);
    for (const file of files) {
        writeFileSync(file, source);
    }
    const npmrc = path.join(root, '.npmrc');
    writeFileSync(npmrc, 'registry=https://registry.npmjs.org/\n');
    rewritePackageLocks(root);
    for (const file of files) {
        assert.equal(readFileSync(file, 'utf8'), rewritePackageLock(source));
    }
    assert.equal(readFileSync(npmrc, 'utf8'), 'registry=https://registry.npmjs.org/\n');
    assert.equal(readFileSync(path.join(shared, 'package-lock.json'), 'utf8'), source);
});

test('missing or invalid root lockfile fails explicitly', (t) => {
    const root = mkdtempSync(path.join(tmpdir(), 'registry-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    assert.throws(() => rewritePackageLocks(root), /ENOENT/);
    writeFileSync(path.join(root, 'package-lock.json'), '{}');
    assert.throws(() => rewritePackageLocks(root), /Expected an npm lockfile/);
});

function runCli({ args = ['--ci'], npmCli = 'npm-cli.js', result = { status: 0 } } = {}) {
    const calls = [];
    const errors = [];
    const process = {
        argv: ['node', 'setup-npm-registry.js', ...args],
        env: { npm_execpath: npmCli },
        execPath: 'node',
    };
    const module = { exports: {} };
    const mockedRequire = (name) => {
        if (name === 'node:fs') {
            return {
                readFileSync: () => source,
                writeFileSync: (file) => calls.push({ file }),
            };
        }
        if (name === 'node:child_process') {
            return {
                spawnSync(command, args, options) {
                    calls.push({ command, args: Array.from(args), ...options });
                    return result;
                },
            };
        }
        return require(name);
    };
    mockedRequire.main = module;
    vm.runInNewContext(readFileSync(path.join(__dirname, 'setup-npm-registry.js'), 'utf8'), {
        require: mockedRequire,
        module,
        process,
        __dirname,
        console: { log() {}, error: (message) => errors.push(message) },
    });
    return { calls, errors, process };
}

test('ci:msft rewrites the root lockfile before installing with the shared proxy registry', () => {
    const context = runCli();
    assert.equal(context.calls.length, 2);
    assert.ok(context.calls[0].file.endsWith('package-lock.json'));
    assert.equal(context.calls[1].command, 'node');
    assert.deepEqual(context.calls[1].args, ['npm-cli.js', 'ci', `--registry=${proxyRegistry}`]);
    assert.equal(context.calls[1].cwd, path.resolve(__dirname, '..'));
    assert.equal(context.calls[1].stdio, 'inherit');
    assert.equal(context.errors.length, 0);
    const scripts = JSON.parse(readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8')).scripts;
    assert.equal(scripts['ci:msft'], 'node ./build/setup-npm-registry.js --ci');
});

for (const result of [{ status: 7 }, { status: null, signal: 'SIGTERM' }, { error: new Error('not found') }]) {
    test(`ci:msft reports npm failure: ${result.signal || result.error?.message || result.status}`, () => {
        const context = runCli({ result });
        assert.equal(context.process.exitCode, result.status || 1);
        assert.match(context.errors[0], /npm ci failed/);
    });
}

test('registry CLI rejects unsupported arguments or missing npm before rewriting files', () => {
    for (const options of [{ args: ['--unknown'] }, { args: ['--ci', '--unknown'] }, { npmCli: '' }]) {
        const context = runCli(options);
        assert.equal(context.process.exitCode, 1);
        assert.equal(context.calls.length, 0);
        assert.equal(context.errors.length, 1);
    }
});

test('standalone registry rewrite does not install dependencies or require npm', () => {
    const context = runCli({ args: [], npmCli: '' });
    assert.equal(context.calls.length, 1);
    assert.ok(context.calls.every((call) => call.file));
    assert.equal(context.errors.length, 0);
});
