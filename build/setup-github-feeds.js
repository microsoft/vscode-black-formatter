// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { appendFileSync, writeFileSync } = require('node:fs');
const path = require('node:path');
const { URL } = require('node:url');
const { microsoft } = require('./package-feeds.json');

try {
    const { NODE_AUTH_TOKEN: token, RUNNER_TEMP: temp, GITHUB_ENV: environmentFile } = process.env;
    if (!token || token === 'null' || /[\r\n]/.test(token)) {
        throw new Error('A nonempty, single-line Azure DevOps token is required.');
    }
    if (!temp || !environmentFile) {
        throw new Error('RUNNER_TEMP and GITHUB_ENV are required.');
    }

    console.log(`::add-mask::${token}`);
    const pipIndex = new URL(microsoft.pip);
    pipIndex.username = 'build';
    pipIndex.password = token;
    console.log(`::add-mask::${pipIndex.href}`);

    const registry = new URL(microsoft.npm);
    const registryScope = `//${registry.host}${registry.pathname}`;
    const feedScope = registryScope.replace(/registry\/$/, '');
    const npmrc = path.join(temp, 'black-formatter-feeds.npmrc');
    writeFileSync(
        npmrc,
        [
            `registry=${registry.href}`,
            `${registryScope}:_authToken=\${NODE_AUTH_TOKEN}`,
            `${feedScope}:_authToken=\${NODE_AUTH_TOKEN}`,
            '',
        ].join('\n'),
        'utf8',
    );
    appendFileSync(
        environmentFile,
        [
            `NODE_AUTH_TOKEN=${token}`,
            `NPM_CONFIG_USERCONFIG=${npmrc}`,
            `PIP_INDEX_URL=${pipIndex.href}`,
            'PIP_NO_INPUT=1',
            '',
        ].join('\n'),
        'utf8',
    );
} catch (error) {
    console.error(`[setup] GitHub feed authentication failed: ${error.message}`);
    process.exitCode = 1;
}
