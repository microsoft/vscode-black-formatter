// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { execFileSync, spawnSync } = require('node:child_process');
const { lstatSync, readFileSync, writeFileSync } = require('node:fs');
const path = require('node:path');
const { URL } = require('node:url');

const mirrorPrefix =
    /^https:\/\/(?:(?:devdiv\.pkgs\.visualstudio\.com\/DevDiv|pkgs\.dev\.azure\.com\/devdiv\/DevDiv)\/_packaging\/Pylance_PublicPackages\/npm\/registry\/|packagefeedproxy\.microsoft\.io\/npm\/|ms-feed-\d+\.pkgs\.visualstudio\.com\/1es-public\/_packaging\/npm-public\/npm\/registry\/)/i;

function normalizePackageLock(source) {
    const lockfile = JSON.parse(source);
    if (
        ![2, 3].includes(lockfile.lockfileVersion) ||
        !lockfile.packages ||
        typeof lockfile.packages !== 'object' ||
        Array.isArray(lockfile.packages)
    ) {
        throw new Error('Expected an npm lockfile with lockfileVersion 2 or 3 and a packages section.');
    }

    const replacements = new Map();
    function visit(value) {
        if (!value || typeof value !== 'object') {
            return;
        }
        if (typeof value.resolved === 'string' && mirrorPrefix.test(value.resolved)) {
            const publicUrl = value.resolved.replace(mirrorPrefix, 'https://registry.npmjs.org/');
            const url = new URL(publicUrl);
            if (url.search || url.hash || !url.pathname.endsWith('.tgz')) {
                throw new Error('Unexpected npm mirror tarball URL; refusing to rewrite it.');
            }
            if (typeof value.integrity !== 'string' || !value.integrity.trim()) {
                throw new Error('Cannot normalize a mirrored package without an integrity hash.');
            }
            replacements.set(value.resolved, publicUrl);
        }
        for (const child of Object.values(value)) {
            visit(child);
        }
    }
    visit(lockfile.packages);
    visit(lockfile.dependencies);

    // Preserve formatting, dependency versions, and integrity hashes.
    return source.replace(/("resolved"\s*:\s*)("(?:\\.|[^"\\])*")/g, (match, prefix, encodedUrl) => {
        const replacement = replacements.get(JSON.parse(encodedUrl));
        return replacement ? prefix + JSON.stringify(replacement) : match;
    });
}

function normalizeStagedLockfile(cwd = process.cwd()) {
    const git = (args) => execFileSync('git', args, { cwd, encoding: 'utf8' });
    const staged = git(['diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z', '--', 'package-lock.json']);
    if (!staged.split('\0').includes('package-lock.json')) {
        return false;
    }
    const source = git(['show', ':package-lock.json']);
    if (normalizePackageLock(source) === source) {
        return false;
    }

    const unstaged = spawnSync('git', ['diff', '--quiet', '--', 'package-lock.json'], { cwd, encoding: 'utf8' });
    if (unstaged.error) {
        throw unstaged.error;
    }
    if (unstaged.status === 1) {
        throw new Error(
            'package-lock.json has unstaged changes. Stage or stash them before committing; no changes were made.',
        );
    }
    if (unstaged.status !== 0) {
        throw new Error(`Unable to check unstaged lockfile changes: ${unstaged.stderr}`);
    }

    const file = path.join(cwd, 'package-lock.json');
    if (!lstatSync(file).isFile()) {
        throw new Error('Refusing to normalize a package-lock.json that is not a regular file.');
    }
    const workingSource = readFileSync(file, 'utf8');
    writeFileSync(file, normalizePackageLock(workingSource), 'utf8');
    git(['add', '--', 'package-lock.json']);
    return true;
}

if (require.main === module) {
    try {
        const args = process.argv.slice(2);
        if (args.length === 1 && args[0] === '--staged') {
            if (normalizeStagedLockfile()) {
                console.log('Normalized and re-staged package-lock.json registry URLs.');
            }
        } else if (args.length === 0) {
            const source = readFileSync('package-lock.json', 'utf8');
            const normalized = normalizePackageLock(source);
            if (normalized !== source) {
                writeFileSync('package-lock.json', normalized, 'utf8');
                console.log('Normalized package-lock.json registry URLs. Stage the file before committing.');
            } else {
                console.log('package-lock.json registry URLs are already normalized.');
            }
        } else {
            throw new Error('Usage: node build/normalize-package-lock.js [--staged]');
        }
    } catch (error) {
        console.error(`Lockfile normalization failed: ${error.message}`);
        process.exitCode = 1;
    }
}

module.exports = { normalizePackageLock, normalizeStagedLockfile };
