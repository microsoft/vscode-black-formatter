// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const { test } = require('node:test');
const { URL } = require('node:url');
const vm = require('node:vm');
const { rewritePackageLock, rewritePackageLocks } = require('./setup-npm-registry');
const { normalizePackageLock } = require('./normalize-package-lock');

function configureGitHubFeeds(t, token) {
    const root = mkdtempSync(path.join(__dirname, 'black-formatter feed auth-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    const environmentFile = path.join(root, 'github-env');
    writeFileSync(environmentFile, 'EXISTING=value\n');
    const result = spawnSync(process.execPath, [path.join(__dirname, 'setup-github-feeds.js')], {
        encoding: 'utf8',
        env: { ...process.env, RUNNER_TEMP: root, GITHUB_ENV: environmentFile, NODE_AUTH_TOKEN: token },
    });
    return { root, environmentFile, result };
}

test('GitHub feed authentication configures both feeds without storing npm credentials in npmrc', (t) => {
    const token = 'test-token.+/=';
    const { root, environmentFile, result } = configureGitHubFeeds(t, token);
    assert.equal(result.status, 0, result.stderr);
    const npmrc = path.join(root, 'black-formatter-feeds.npmrc');
    const config = readFileSync(npmrc, 'utf8');
    assert.ok(config.includes(`registry=${microsoftRegistry}\n`));
    assert.ok(config.includes('/npm/registry/:_authToken=${NODE_AUTH_TOKEN}\n'));
    assert.ok(config.includes('/npm/:_authToken=${NODE_AUTH_TOKEN}\n'));
    assert.ok(!config.includes(token));
    const environment = readFileSync(environmentFile, 'utf8');
    assert.ok(environment.startsWith('EXISTING=value\n'));
    assert.ok(environment.includes(`NPM_CONFIG_USERCONFIG=${npmrc}\n`));
    assert.ok(environment.includes(`NODE_AUTH_TOKEN=${token}\n`));
    assert.ok(environment.includes('PIP_NO_INPUT=1\n'));
    const index = new URL(
        environment
            .split('\n')
            .find((line) => line.startsWith('PIP_INDEX_URL='))
            .slice(14),
    );
    assert.equal(index.hostname, 'pkgs.dev.azure.com');
    assert.equal(index.pathname, '/devdiv/DevDiv/_packaging/Pylance_PublicPackages/pypi/simple/');
    assert.equal(index.username, 'build');
    assert.equal(decodeURIComponent(index.password), token);
    assert.ok(result.stdout.includes(`::add-mask::${token}\n`));
    assert.ok(result.stdout.includes(`::add-mask::${index.href}\n`));
});

test('GitHub feed authentication rejects missing or multiline tokens without modifying configuration', (t) => {
    for (const token of ['', 'null', 'token\nINJECTED=value']) {
        const { root, environmentFile, result } = configureGitHubFeeds(t, token);
        assert.equal(result.status, 1);
        assert.match(result.stderr, /single-line Azure DevOps token is required/);
        assert.equal(readFileSync(environmentFile, 'utf8'), 'EXISTING=value\n');
        assert.throws(() => readFileSync(path.join(root, 'black-formatter-feeds.npmrc')), /ENOENT/);
        assert.ok(!result.stderr.includes('INJECTED'));
    }
});

const publicRegistry = 'https://registry.npmjs.org/';
const microsoftRegistry = 'https://devdiv.pkgs.visualstudio.com/DevDiv/_packaging/Pylance_PublicPackages/npm/registry/';
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
        .replaceAll(publicRegistry, microsoftRegistry)
        .replace('https://registry.yarnpkg.com/', microsoftRegistry);
    assert.equal(rewritePackageLock(source), expected);
    assert.equal(rewritePackageLock(expected), expected);
    assert.equal(normalizePackageLock(expected), source.replace('https://registry.yarnpkg.com/', publicRegistry));
});

test('normalizes slashless registry overrides before rewriting resolved URLs', () => {
    for (const registry of [publicRegistry, microsoftRegistry]) {
        const expected = source.replaceAll(publicRegistry, registry).replace('https://registry.yarnpkg.com/', registry);
        assert.equal(rewritePackageLock(source, registry.slice(0, -1)), expected);
    }
});

test('supports version 2 legacy dependencies as well as packages', () => {
    const legacy = JSON.stringify({
        lockfileVersion: 2,
        packages: {},
        dependencies: { example: { resolved: `${publicRegistry}example/-/example.tgz` } },
    });
    assert.equal(rewritePackageLock(legacy), legacy.replace(publicRegistry, microsoftRegistry));
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

function runCli({ args = ['--ci'], npmCli = 'npm-cli.js', result = { status: 0 }, env = {} } = {}) {
    const calls = [];
    const errors = [];
    const process = {
        argv: ['node', 'setup-npm-registry.js', ...args],
        env: { npm_execpath: npmCli, ...env },
        execPath: 'node',
    };
    const module = { exports: {} };
    const mockedRequire = (name) => {
        if (name === 'node:fs') {
            return {
                readFileSync: () => source,
                writeFileSync: (file, source) => calls.push({ file, source }),
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

test('ci:msft rewrites the root lockfile before installing with the Microsoft registry', () => {
    const context = runCli();
    assert.equal(context.calls.length, 2);
    assert.ok(context.calls[0].file.endsWith('package-lock.json'));
    assert.equal(context.calls[1].command, 'node');
    assert.deepEqual(context.calls[1].args, ['npm-cli.js', 'ci', `--registry=${microsoftRegistry}`]);
    assert.equal(context.calls[1].cwd, path.resolve(__dirname, '..'));
    assert.equal(context.calls[1].stdio, 'inherit');
    assert.equal(context.errors.length, 0);
    const scripts = JSON.parse(readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8')).scripts;
    assert.equal(scripts['ci:msft'], 'node ./build/setup-npm-registry.js --ci');
});

test('ci:msft preserves template authentication for the configured internal registry', () => {
    const registry = 'https://devdiv.pkgs.visualstudio.com/DevDiv/_packaging/Pylance_PublicPackages/npm/registry/';
    for (const settings of [
        { NPM_CONFIG_REGISTRY: registry },
        { npm_config_registry: registry },
        { NPM_CONFIG_REGISTRY: registry.slice(0, -1) },
        { npm_config_registry: registry.slice(0, -1) },
        { NPM_CONFIG_REGISTRY: 'https://stale.example/npm/', npm_config_registry: registry },
    ]) {
        const env = {
            ...settings,
            NPM_CONFIG_USERCONFIG: path.join(tmpdir(), 'authenticated.npmrc'),
            NODE_AUTH_TOKEN: 'test-token',
        };
        const context = runCli({ env });
        const install = context.calls.at(-1);
        assert.deepEqual(install.args, ['npm-cli.js', 'ci', `--registry=${registry}`]);
        assert.equal(install.env, undefined);
        assert.equal(context.process.env.NPM_CONFIG_USERCONFIG, env.NPM_CONFIG_USERCONFIG);
        assert.equal(context.process.env.NODE_AUTH_TOKEN, env.NODE_AUTH_TOKEN);
        for (const write of context.calls.slice(0, -1)) {
            assert.equal(write.source, rewritePackageLock(source, registry));
        }
        assert.equal(context.errors.length, 0);
    }
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
