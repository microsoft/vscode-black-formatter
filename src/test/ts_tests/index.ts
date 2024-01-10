import * as glob from 'glob';
import Mocha from 'mocha';
import * as path from 'path';
import { env } from 'process';

export function run(): Promise<void> {
    // Create the mocha test
    const mocha = new Mocha({
        ui: 'tdd',
        color: true,
    });

    const testsRoot = path.resolve(__dirname, './tests');

    return new Promise((c, e) => {
        let files = [];
        if (env.SMOKE_TESTS) {
            files = glob.globSync('**/**.smoke.test.js', { cwd: testsRoot });
        } else {
            files = glob.globSync('**/**.unit.test.js', { cwd: testsRoot });
        }

        // Add files to the test suite
        files.forEach((f) => mocha.addFile(path.resolve(testsRoot, f)));

        try {
            // Run the mocha test
            mocha.run((failures) => {
                if (failures > 0) {
                    e(new Error(`${failures} tests failed.`));
                } else {
                    c();
                }
            });
        } catch (err) {
            console.error(err);
            e(err);
        }
    });
}
