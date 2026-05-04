/**
 * scripts/_lib/script-utils.js — shared utilities for the per-edit toolchain.
 *
 * Consumed by:
 *   - scripts/verify-impl.js (Step 2 of 6-step workflow)
 *   - scripts/post-simplify-verify.js (Step 4)
 *
 * Zero npm dependencies — Node stdlib only. ESM (package.json type=module).
 */

import path from 'path';
import cp from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// scripts/_lib/ → scripts/ → repo root (two levels up from this file)
export const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

/**
 * UTC compact timestamp suitable for filenames: YYYYMMDD-HHMMSS.
 */
export function utcTimestamp() {
  const d = new Date();
  const p = (n, w = 2) => String(n).padStart(w, '0');
  return `${d.getUTCFullYear()}${p(d.getUTCMonth() + 1)}${p(d.getUTCDate())}-${p(d.getUTCHours())}${p(d.getUTCMinutes())}${p(d.getUTCSeconds())}`;
}

/**
 * Convert an arbitrary file path to a filename-safe slug.
 * Lowercases, collapses non-alphanumeric runs to a single hyphen, strips trailing hyphens.
 */
export function pathToSlug(filePath) {
  return filePath
    .replace(/^\/+/, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/-+$/g, '')
    .toLowerCase();
}

/**
 * Stable per-task identifier combining a path slug with a UTC timestamp.
 */
export function deriveTaskId(filePath) {
  return `${pathToSlug(filePath)}-${utcTimestamp()}`;
}

/**
 * Run a shell command in the project root. Returns { stdout, status }.
 * Stderr is folded into stdout on failure so callers see the full diagnostic.
 */
export function run(cmd, opts = {}) {
  try {
    const out = cp.execSync(cmd, { cwd: PROJECT_ROOT, encoding: 'utf8', ...opts });
    return { stdout: out || '', status: 0 };
  } catch (e) {
    return { stdout: (e.stdout || '') + (e.stderr || ''), status: e.status || 1 };
  }
}
