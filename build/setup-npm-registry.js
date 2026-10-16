// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { spawnSync } = require('node:child_process');
const { readFileSync, writeFileSync } = require('node:fs');
const path = require('node:path');
const { microsoft } = require('./package-feeds.json');

function rewritePackageLock(source) {
    const lockfile = JSON.parse(source);
    if (
        ![2, 3].includes(lockfile.lockfileVersion) ||
        !lockfile.packages ||
        typeof lockfile.packages !== 'object' ||
        Array.isArray(lockfile.packages)
    ) {
        throw new Error('Expected an npm lockfile with lockfileVersion 2 or 3 and a packages section.');
    }

    return source.replace(/("resolved"\s*:\s*)("(?:\\.|[^"\\])*")/g, (match, prefix, encodedUrl) => {
        const url = JSON.parse(encodedUrl);
        const rewritten = url.replace(/^https:\/\/registry\.(?:npmjs\.org|yarnpkg\.com)\//, microsoft.npm);
        return rewritten === url ? match : prefix + JSON.stringify(rewritten);
    });
}

function rewritePackageLocks(root = path.resolve(__dirname, '..')) {
    const files = [path.join(root, 'package-lock.json')];
    const updates = files.map((file) => {
        const source = readFileSync(file, 'utf8');
        return { file, source, rewritten: rewritePackageLock(source) };
    });
    for (const { file, source, rewritten } of updates) {
        if (rewritten !== source) {
            writeFileSync(file, rewritten, 'utf8');
            console.log(`[setup] Rewrote npm registry URLs: ${file}`);
        }
    }
}

if (require.main === module) {
    try {
        const args = process.argv.slice(2);
        const install = args.length === 1 && args[0] === '--ci';
        if (args.length && !install) {
            throw new Error('Usage: node build/setup-npm-registry.js [--ci]');
        }
        if (install && !process.env.npm_execpath) {
            throw new Error('Run npm install using npm run ci:msft.');
        }
        rewritePackageLocks();
        if (install) {
            const result = spawnSync(
                process.execPath,
                [process.env.npm_execpath, 'ci', `--registry=${microsoft.npm}`],
                { cwd: path.resolve(__dirname, '..'), stdio: 'inherit' },
            );
            if (result.error || result.signal || result.status !== 0) {
                const reason = result.error?.message || result.signal || `exit code ${result.status}`;
                const error = new Error(`npm ci failed: ${reason}`);
                error.exitCode = result.status || 1;
                throw error;
            }
        }
    } catch (error) {
        console.error(`[setup] Npm registry setup failed: ${error.message}`);
        process.exitCode = error.exitCode || 1;
    }
}

module.exports = { rewritePackageLock, rewritePackageLocks };
