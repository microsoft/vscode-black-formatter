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

execSync(`npm --prefix ${pkgDir} run build`, { stdio: "inherit" });
