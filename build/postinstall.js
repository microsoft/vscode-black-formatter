// Builds the shared package that lives in the git submodule after install.
//
// The build is skipped (with guidance) when the submodule has not been
// checked out, so a clone made without `--recurse-submodules` does not fail
// `npm install`/`npm ci` at the postinstall step with a confusing error.
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
