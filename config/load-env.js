/**
 * Universal environment loader for DevSkyy (Node.js).
 *
 * Usage:
 *   require('./config/load-env');
 *   // or from any subdirectory:
 *   require('../config/load-env');
 *
 * Loads .env files in priority order (last wins):
 *   1. Root .env (all keys)
 *   2. gemini/.env (real API keys, overrides placeholders)
 *
 * Works from any subdirectory in the project.
 */

const path = require('path');
const fs = require('fs');

function findProjectRoot() {
  let dir = __dirname;
  while (dir !== path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, '.git'))) return dir;
    dir = path.dirname(dir);
  }
  // Fallback: config/ is one level below root
  return path.dirname(__dirname);
}

function loadEnv() {
  let dotenv;
  try {
    dotenv = require('dotenv');
  } catch {
    // dotenv not installed — skip silently
    return findProjectRoot();
  }

  const root = findProjectRoot();
  const rootEnv = path.join(root, '.env');
  const geminiEnv = path.join(root, 'gemini', '.env');

  if (fs.existsSync(rootEnv)) {
    dotenv.config({ path: rootEnv });
  }

  if (fs.existsSync(geminiEnv)) {
    dotenv.config({ path: geminiEnv, override: true });
  }

  return root;
}

const PROJECT_ROOT = loadEnv();
module.exports = { PROJECT_ROOT, findProjectRoot, loadEnv };
