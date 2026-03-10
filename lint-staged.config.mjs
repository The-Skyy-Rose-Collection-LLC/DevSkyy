/** @type {import('lint-staged').Configuration} */
export default {
  // Python: file-level lint checks (lint-staged appends staged file paths)
  '*.py': [
    'ruff check',
    'black --check',
    'isort --check-only --diff',
  ],

  // Frontend JS/TS: ESLint on staged files only
  // Do NOT use --max-warnings 0 (242 existing warnings would block every commit)
  // ESLint exits non-zero on errors, zero on warnings-only -- this is correct behavior
  // Must run from frontend/ dir -- root node_modules/eslint has ajv crash (ESLint v9 + @eslint/eslintrc)
  // lint-staged uses execa (no shell) so we use bash -c to enable cd && chain
  'frontend/**/*.{ts,tsx,js,jsx,mjs}': (files) => {
    const relPaths = files.map((f) => f.replace(/^.*\/frontend\//, '').replace(/'/g, "'\\''"));
    const quoted = relPaths.map((p) => `'${p}'`).join(' ');
    return `bash -c 'cd frontend && npx eslint ${quoted}'`;
  },

  // Frontend TypeScript type check: whole-project (function prevents file arg appending)
  // tsc ignores tsconfig.json when given individual file arguments on CLI
  'frontend/**/*.{ts,tsx}': () => 'tsc --noEmit --project frontend/tsconfig.json',

  // PHP syntax check via wrapper (php -l only accepts one file at a time)
  'wordpress-theme/**/*.php': 'bash scripts/php-lint.sh',
};
