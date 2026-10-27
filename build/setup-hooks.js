// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { execFileSync, spawnSync } = require('node:child_process');
const { chmodSync, existsSync } = require('node:fs');
const path = require('node:path');

function setupHooks(cwd = path.resolve(__dirname, '..')) {
    const git = (args) => execFileSync('git', args, { cwd, encoding: 'utf8' }).trim();
    const existing = spawnSync('git', ['config', '--get', 'core.hooksPath'], { cwd, encoding: 'utf8' });
    if (existing.error) {
        throw existing.error;
    }
    if (![0, 1].includes(existing.status)) {
        throw new Error(`Cannot inspect Git hooks configuration: ${existing.stderr}`);
    }
    if (existing.status === 0 && existing.stdout.trim() !== '.githooks') {
        throw new Error('An existing core.hooksPath is configured. Integrate the normalizer into your hook manually.');
    }
    if (
        existing.status === 1 &&
        existsSync(git(['rev-parse', '--path-format=absolute', '--git-path', 'hooks/pre-commit']))
    ) {
        throw new Error('An existing pre-commit hook is installed. Integrate the normalizer into your hook manually.');
    }
    chmodSync(path.join(cwd, '.githooks', 'pre-commit'), 0o755);
    git(['config', '--local', 'core.hooksPath', '.githooks']);
    console.log('Enabled the local lockfile normalization hook (applies to all worktrees of this clone).');
}

if (require.main === module) {
    try {
        setupHooks();
    } catch (error) {
        console.error(`Hook setup failed: ${error.message}`);
        process.exitCode = 1;
    }
}

module.exports = { setupHooks };
