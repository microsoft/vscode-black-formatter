// Builds the shared package that lives in the git submodule after install.
//
// Note: a clone made without `--recurse-submodules` actually fails earlier,
// when npm resolves the `file:` dependency during the install phase, before
// this postinstall script runs. The guard below only adds a friendlier message
// on the rarer paths that still reach postinstall (e.g. the submodule was
// removed after a prior install); it is not a substitute for initializing the
// submodule.
const { existsSync } = require("fs");
const { execSync } = require("child_process");

const pkgDir = "external/vscode-common-python-lsp/typescript";

if (!existsSync(`${pkgDir}/package.json`)) {
  console.warn(
    `[postinstall] Shared package submodule not found at "${pkgDir}". ` +
      "Run `git submodule update --init --recursive` and reinstall to build it.",
  );
  process.exit(0);
}

// Already built (e.g. by a prior install or the packaging pipeline); nothing to do.
if (existsSync(`${pkgDir}/dist/index.js`)) {
  process.exit(0);
}

// The build runs the submodule's `tsc`, which is a devDependency of the shared
// package. A dev-pruned install (`npm ci --omit=dev`, `NODE_ENV=production`, or
// a VSIX packager that prunes) may not have it available. Skip with guidance
// rather than hard-failing the whole install; build/packaging jobs run a full
// install and produce `dist/` there.
if (
  !existsSync(`${pkgDir}/node_modules/.bin/tsc`) &&
  !existsSync(`${pkgDir}/node_modules/.bin/tsc.cmd`) &&
  !existsSync(`${pkgDir}/node_modules/typescript`)
) {
  console.warn(
    `[postinstall] TypeScript toolchain not installed in "${pkgDir}"; ` +
      "skipping the shared package build. Run " +
      `\`npm --prefix ${pkgDir} install && npm --prefix ${pkgDir} run build\` ` +
      "if you need dist/ locally.",
  );
  process.exit(0);
}

execSync(`npm --prefix ${pkgDir} run build`, { stdio: "inherit" });
