Please see [our wiki](https://github.com/microsoft/vscode-black-formatter/wiki/Contributing-Guide) on how to contribute to this project.

## Building the pinned shared runtime

Use the Node.js version in `.nvmrc` and initialize the shared submodule:

```powershell
git submodule update --init --recursive
npm run setup
npm run typecheck
npm run compile
npm run test:runtime
npm run vsce-package
```

`npm run setup` creates a project-local Python environment and installs the
bundled Python libraries through `nox --session install_bundled_libs`. The shared
Python library is installed from `external/vscode-common-python-lsp/python`, not
a registry distribution. Use `npm run setup:msft` instead when working with the
Microsoft package feeds.

`npm ci` also installs the pinned checkout's own locked TypeScript dependencies.
The typecheck, compile, test-compilation, watch and package scripts always rebuild
its public `typescript/dist` entry before consuming it. Webpack bundles that
entry and its dependencies; the checkout itself is not shipped in the VSIX.
After changing the gitlink, rerun `npm ci` and the Python bundling session so both
languages use the same source revision. Do not add a shared-runtime registry
dependency or import individual shared implementation files.

Black retains its formatter policy and extension-specific settings logging;
the shared activation runtime owns common subscriptions and shutdown.
Activation is deferred and does not indicate that the language client is ready.
