// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { spawnSync } = require('node:child_process');
const { existsSync } = require('node:fs');
const path = require('node:path');
const feeds = require('./package-feeds.json');

function setup({ microsoft = false } = {}) {
    const npmCli = process.env.npm_execpath;
    if (!npmCli) {
        throw new Error('Run setup using npm run setup or npm run setup:msft.');
    }

    const root = path.resolve(__dirname, '..');
    const env = { ...process.env };
    for (const key of Object.keys(env)) {
        if (['npm_config_registry', 'pip_index_url'].includes(key.toLowerCase())) {
            delete env[key];
        }
    }
    const feed = microsoft ? feeds.microsoft : feeds.public;
    env.npm_config_registry = feed.npm;
    env.PIP_INDEX_URL = feed.pip;

    function run(command, args, cwd = root) {
        console.log(`[setup] ${command} ${args.join(' ')}`);
        const result = spawnSync(command, args, { cwd, env, stdio: 'inherit' });
        if (result.error || result.signal || result.status !== 0) {
            const reason = result.error?.message || result.signal || `exit code ${result.status}`;
            const error = new Error(`Setup failed running ${command}: ${reason}`);
            error.exitCode = result.status || 1;
            throw error;
        }
    }

    run('git', ['submodule', 'update', '--init', '--recursive']);
    if (microsoft) {
        run(process.execPath, [path.join(root, 'build', 'setup-npm-registry.js')]);
    }

    const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts\\python.exe' : 'bin/python');
    if (!existsSync(python)) {
        run(process.platform === 'win32' ? 'python' : 'python3', ['-m', 'venv', '.venv']);
    }
    run(python, [
        '-c',
        'import sys; sys.exit("Setup requires Python 3.10 or later.") if sys.version_info < (3, 10) else None',
    ]);
    run(python, ['-m', 'pip', 'install', '--upgrade', 'pip', 'wheel', 'nox']);

    run(process.execPath, [npmCli, 'ci', '--include=dev']);
    run(python, ['-m', 'nox', '--session', 'install_bundled_libs']);
    console.log('[setup] Complete. Python tools are installed in .venv; run npm run compile to build the extension.');
}

function runCli(options) {
    try {
        if (process.argv.length > 2) {
            throw new Error('Setup takes no arguments. Use npm run setup or npm run setup:msft.');
        }
        setup(options);
    } catch (error) {
        console.error(`[setup] ${error.message}`);
        process.exitCode = error.exitCode || 1;
    }
}

if (require.main === module) {
    runCli();
}

module.exports = { setup, runCli };
