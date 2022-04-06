// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as path from 'path';
import * as fs from 'fs-extra';
import { EXTENSION_ROOT_DIR } from './constants';

export interface IFormatter {
    name: string;
    module: string;
}

export function loadFormatterDefaults(): IFormatter {
    const formatterJson = path.join(EXTENSION_ROOT_DIR, 'package.json');
    const content = fs.readFileSync(formatterJson).toString();
    const config = JSON.parse(content);
    return config.formatter as IFormatter;
}
