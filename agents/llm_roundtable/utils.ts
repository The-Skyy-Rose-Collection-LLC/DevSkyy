/**
 * LLM Roundtable — Shared Persistence Utilities
 *
 * Single source of truth for data directory and JSON I/O.
 * Uses atomic writes (write to .tmp, then rename) to prevent corruption.
 *
 * @package DevSkyy
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Shared data directory for all roundtable persistence. */
export const DATA_DIR = path.resolve(__dirname, "data");

/**
 * Load a JSON file, returning fallback if missing or corrupted.
 */
export function loadJSON<T>(file: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(file, "utf-8"));
  } catch {
    return fallback;
  }
}

/**
 * Save data as JSON with atomic write (temp file + rename).
 */
export function saveJSON(file: string, data: unknown): void {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
    fs.renameSync(tmp, file);
  } catch {
    // Atomic write failed — fall back to direct write
    fs.writeFileSync(file, JSON.stringify(data, null, 2));
  }
}

/**
 * Backup current file before writing new data.
 * Self-healing: preserves last-known-good state for recovery.
 */
export function backupAndSave(file: string, data: unknown): void {
  try {
    if (fs.existsSync(file)) {
      fs.copyFileSync(file, `${file}.bak`);
    }
  } catch {
    // Non-critical — proceed without backup
  }
  saveJSON(file, data);
}
