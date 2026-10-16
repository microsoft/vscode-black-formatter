// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const assert = require('node:assert/strict');
const { execFileSync, spawnSync } = require('node:child_process');
const { chmodSync, copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { test } = require('node:test');
const { normalizePackageLock, normalizeStagedLockfile } = require('./normalize-package-lock');
const { setupHooks } = require('./setup-hooks');

const mirrors = [
    'https://devdiv.pkgs.visualstudio.com/DevDiv/_packaging/Pylance_PublicPackages/npm/registry/',
    'https://pkgs.dev.azure.com/devdiv/DevDiv/_packaging/Pylance_PublicPackages/npm/registry/',
    'https://packagefeedproxy.microsoft.io/npm/',
    'https://ms-feed-25.pkgs.visualstudio.com/1es-public/_packaging/npm-public/npm/registry/',
];
const publicRegistry = 'https://registry.npmjs.org/';
const entry = {
    version: '1.0.0',
    resolved: `${mirrors[0]}@example/package/-/package-1.0.0.tgz`,
    integrity: 'sha512-preserved',
};

function lockfile(packages = { 'node_modules/@example/package': entry }, extra = {}) {
    return JSON.stringify({ name: 'black-formatter', lockfileVersion: 3, packages, ...extra }, null, 4) + '\n';
}

function fixture(t) {
    const cwd = mkdtempSync(join(tmpdir(), 'black-formatter hook with spaces-'));
    t.after(() => rmSync(cwd, { recursive: true, force: true }));
    const git = (args) => execFileSync('git', args, { cwd, encoding: 'utf8' }).replace(/\r\n/g, '\n');
    git(['init', '--quiet']);
    git(['config', 'user.name', 'Hook Test']);
    git(['config', 'user.email', 'hook-test@example.invalid']);
    git(['config', 'core.autocrlf', 'false']);
    git(['config', 'commit.gpgsign', 'false']);
    git(['config', '--local', 'core.hooksPath', '.githooks']);
    mkdirSync(join(cwd, '.githooks'));
    mkdirSync(join(cwd, 'build'));
    copyFileSync(join(__dirname, '..', '.githooks', 'pre-commit'), join(cwd, '.githooks', 'pre-commit'));
    copyFileSync(join(__dirname, 'normalize-package-lock.js'), join(cwd, 'build', 'normalize-package-lock.js'));
    chmodSync(join(cwd, '.githooks', 'pre-commit'), 0o755);
    return { cwd, git };
}

for (const mirror of mirrors) {
    test(`normalizes ${mirror} preserving bytes outside resolved URLs`, () => {
        const source = lockfile().replaceAll(mirrors[0], mirror).replace(/\n/g, '\r\n');
        const normalized = normalizePackageLock(source);
        assert.equal(normalized, source.replace(mirror, publicRegistry));
        assert.equal(normalizePackageLock(normalized), normalized);
    });
}

test('normalizes v2 nested legacy dependencies and unscoped packages', () => {
    const unscoped = { ...entry, resolved: `${mirrors[2]}example/-/example-1.0.0.tgz` };
    const source = lockfile(
        { 'node_modules/example': unscoped },
        { lockfileVersion: 2, dependencies: { parent: { dependencies: { example: entry } } } },
    );
    assert.equal(
        normalizePackageLock(source),
        source.replaceAll(mirrors[0], publicRegistry).replaceAll(mirrors[2], publicRegistry),
    );
});

test('preserves intentional Azure, unknown feeds, public, git and local sources', () => {
    const source = lockfile({
        '': { name: 'black-formatter' },
        public: { resolved: `${publicRegistry}example/-/example-1.0.0.tgz` },
        azure: {
            resolved:
                'https://pkgs.dev.azure.com/azure-public/vside/_packaging/msft_consumption/npm/registry/example.tgz',
        },
        private: { resolved: `${mirrors[0].replace('Pylance_PublicPackages', 'OtherFeed')}example.tgz` },
        git: { resolved: 'git+https://github.com/example/example.git#abc' },
        file: { resolved: 'file:external/example' },
        link: { resolved: 'external/example', link: true },
    });
    assert.equal(normalizePackageLock(source), source);
});

test('rejects invalid lockfiles and mirror entries without integrity or with query strings', () => {
    assert.throws(() => normalizePackageLock('{'), SyntaxError);
    assert.throws(() => normalizePackageLock('{"lockfileVersion":1}'), /Expected an npm lockfile/);
    assert.throws(() => normalizePackageLock(lockfile([])), /Expected an npm lockfile/);
    assert.throws(
        () => normalizePackageLock(lockfile({ example: { ...entry, integrity: undefined } })),
        /without an integrity hash/,
    );
    assert.throws(
        () => normalizePackageLock(lockfile({ example: { ...entry, resolved: entry.resolved + '?token=example' } })),
        /Unexpected npm mirror/,
    );
});

test('normalizes and re-stages only the lockfile for an initial commit', (t) => {
    const { cwd, git } = fixture(t);
    const source = lockfile();
    writeFileSync(join(cwd, 'package-lock.json'), source);
    writeFileSync(join(cwd, 'unstaged.txt'), 'keep unstaged');
    git(['add', '--', 'package-lock.json']);
    assert.equal(normalizeStagedLockfile(cwd), true);
    assert.equal(readFileSync(join(cwd, 'package-lock.json'), 'utf8'), source.replace(mirrors[0], publicRegistry));
    assert.equal(git(['show', ':package-lock.json']), source.replace(mirrors[0], publicRegistry));
    assert.equal(git(['diff', '--cached', '--name-only']).trim(), 'package-lock.json');
    assert.equal(normalizeStagedLockfile(cwd), false);
});

test('does not touch an unstaged lockfile or a staged deletion', (t) => {
    const { cwd, git } = fixture(t);
    const source = lockfile();
    writeFileSync(join(cwd, 'package-lock.json'), source);
    assert.equal(normalizeStagedLockfile(cwd), false);
    git(['add', '--', 'package-lock.json']);
    git(['commit', '--quiet', '-m', 'fixture']);
    git(['rm', '--quiet', '--', 'package-lock.json']);
    assert.equal(normalizeStagedLockfile(cwd), false);
});

test('refuses partial staging without modifying worktree or index', (t) => {
    const { cwd, git } = fixture(t);
    const source = lockfile();
    writeFileSync(join(cwd, 'package-lock.json'), source);
    git(['add', '--', 'package-lock.json']);
    const unstaged = source.replace('"name": "black-formatter"', '"name": "unstaged"');
    writeFileSync(join(cwd, 'package-lock.json'), unstaged);
    assert.throws(() => normalizeStagedLockfile(cwd), /has unstaged changes/);
    assert.equal(readFileSync(join(cwd, 'package-lock.json'), 'utf8'), unstaged);
    assert.equal(git(['show', ':package-lock.json']), source);
});

test('installed hook normalizes actual commits and blocks partial staging', (t) => {
    const { cwd, git } = fixture(t);
    setupHooks(cwd);
    const source = lockfile();
    writeFileSync(join(cwd, 'package-lock.json'), source);
    git(['add', '--', 'package-lock.json']);
    git(['commit', '--quiet', '-m', 'test normalization']);
    assert.equal(git(['show', 'HEAD:package-lock.json']), source.replace(mirrors[0], publicRegistry));
    writeFileSync(join(cwd, 'package-lock.json'), source);
    git(['add', '--', 'package-lock.json']);
    writeFileSync(join(cwd, 'package-lock.json'), source.replace('"name": "black-formatter"', '"name": "unstaged"'));
    const refused = spawnSync('git', ['commit', '--quiet', '-m', 'must refuse partial staging'], {
        cwd,
        encoding: 'utf8',
    });
    assert.notEqual(refused.status, 0);
    assert.match(refused.stderr, /has unstaged changes/);
    assert.equal(git(['show', 'HEAD:package-lock.json']), source.replace(mirrors[0], publicRegistry));
});

test('hook installer refuses to replace existing hook configuration or a hook file', (t) => {
    const { cwd, git } = fixture(t);
    git(['config', '--local', 'core.hooksPath', 'custom-hooks']);
    assert.throws(() => setupHooks(cwd), /existing core.hooksPath/);
    assert.equal(git(['config', '--get', 'core.hooksPath']).trim(), 'custom-hooks');
    git(['config', '--local', '--unset', 'core.hooksPath']);
    const hooks = git(['rev-parse', '--path-format=absolute', '--git-path', 'hooks']).trim();
    mkdirSync(hooks, { recursive: true });
    writeFileSync(join(hooks, 'pre-commit'), '# keep existing hook\n');
    assert.throws(() => setupHooks(cwd), /existing pre-commit hook/);
    assert.equal(readFileSync(join(hooks, 'pre-commit'), 'utf8'), '# keep existing hook\n');
});

test('hook installer enables an unconfigured clone and can be rerun', (t) => {
    const { cwd, git } = fixture(t);
    git(['config', '--local', '--unset', 'core.hooksPath']);
    setupHooks(cwd);
    assert.equal(git(['config', '--local', '--get', 'core.hooksPath']).trim(), '.githooks');
    setupHooks(cwd);
    assert.equal(git(['config', '--local', '--get', 'core.hooksPath']).trim(), '.githooks');
});
