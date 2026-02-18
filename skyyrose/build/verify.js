#!/usr/bin/env node
'use strict';

/**
 * SkyyRose — Production Verification Script
 * Verifies the entire production setup is correct and ready for deployment.
 * No external test frameworks. No API keys required.
 */

const fs   = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ---------------------------------------------------------------------------
// ANSI color helpers
// ---------------------------------------------------------------------------
const C = {
  reset:   '\x1b[0m',
  bold:    '\x1b[1m',
  dim:     '\x1b[2m',
  red:     '\x1b[31m',
  green:   '\x1b[32m',
  yellow:  '\x1b[33m',
  blue:    '\x1b[34m',
  magenta: '\x1b[35m',
  cyan:    '\x1b[36m',
  white:   '\x1b[37m',
  bgBlue:  '\x1b[44m',
};
const fmt = (color, str) => `${C[color]}${str}${C.reset}`;
const bold    = (s) => `${C.bold}${s}${C.reset}`;
const dim     = (s) => `${C.dim}${s}${C.reset}`;
const pass    = (s) => `  ${fmt('green', '✅')} ${s}`;
const fail    = (s) => `  ${fmt('red',   '❌')} ${s}`;
const warn    = (s) => `  ${fmt('yellow','⚠️ ')} ${s}`;
const info    = (s) => `  ${fmt('cyan',  'ℹ️ ')} ${s}`;

// ---------------------------------------------------------------------------
// Root of the project (two levels up from build/)
// ---------------------------------------------------------------------------
const ROOT = path.resolve(__dirname, '..');

const rel = (...parts) => path.join(ROOT, ...parts);

// ---------------------------------------------------------------------------
// Result tracking
// ---------------------------------------------------------------------------
let totalPass    = 0;
let totalFail    = 0;
let totalWarn    = 0;
const failures   = [];
const warnings   = [];
const lines      = [];           // buffered output lines for each section

// section-level tracking
let criticalFail = false;        // set true if Section 1 or 3 fails anything

function record(ok, label, isCritical = false, message = null) {
  if (ok === true) {
    totalPass++;
    lines.push(pass(label));
  } else if (ok === 'warn') {
    totalWarn++;
    const msg = message ? `${label} — ${message}` : label;
    warnings.push(msg);
    lines.push(warn(label + (message ? ` — ${dim(message)}` : '')));
  } else {
    totalFail++;
    const msg = message ? `${label} — ${message}` : label;
    failures.push(msg);
    lines.push(fail(label + (message ? ` — ${dim(message)}` : '')));
    if (isCritical) criticalFail = true;
  }
}

function sectionHeader(num, total, title) {
  lines.push('');
  lines.push(`  ${bold(`[${num}/${total}]`)} ${fmt('cyan', title)}`);
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function fileExists(relPath) {
  return fs.existsSync(rel(relPath));
}

function readJSON(relPath) {
  const full = rel(relPath);
  if (!fs.existsSync(full)) return null;
  try { return JSON.parse(fs.readFileSync(full, 'utf8')); }
  catch { return null; }
}

function readText(relPath) {
  const full = rel(relPath);
  if (!fs.existsSync(full)) return null;
  return fs.readFileSync(full, 'utf8');
}

function countFilesInDir(dir) {
  if (!fs.existsSync(dir)) return 0;
  let count = 0;
  const walk = (d) => {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      if (entry.isDirectory()) walk(path.join(d, entry.name));
      else count++;
    }
  };
  walk(dir);
  return count;
}

function countFilesMatching(dir, pattern) {
  if (!fs.existsSync(dir)) return 0;
  let count = 0;
  const walk = (d) => {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      if (entry.isDirectory()) walk(path.join(d, entry.name));
      else if (pattern.test(entry.name)) count++;
    }
  };
  walk(dir);
  return count;
}

// Simple CSV parser — handles quoted fields
function parseCSV(text) {
  const rows = [];
  const lines = text.split(/\r?\n/);
  for (const line of lines) {
    if (!line.trim()) continue;
    const cols = [];
    let cur = '';
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQuote && line[i+1] === '"') { cur += '"'; i++; }
        else inQuote = !inQuote;
      } else if (ch === ',' && !inQuote) {
        cols.push(cur); cur = '';
      } else {
        cur += ch;
      }
    }
    cols.push(cur);
    rows.push(cols);
  }
  return rows;
}

// ---------------------------------------------------------------------------
// ============================================================
// MAIN
// ============================================================
// ---------------------------------------------------------------------------

console.log('');
console.log(bold(fmt('magenta', ' SkyyRose — Production Verification')));
console.log(fmt('dim', '========================================================'));
console.log('');

const TOTAL_SECTIONS = 9;

// ===========================================================================
// SECTION 1: File Existence
// ===========================================================================
sectionHeader(1, TOTAL_SECTIONS, 'File Existence');

const REQUIRED_FILES = [
  // Root
  'sw.js',
  'index.html',
  'package.json',
  'requirements.txt',
  // assets/js
  'assets/js/app.js',
  'assets/js/config.js',
  'assets/js/accessibility.js',
  'assets/js/gestures.js',
  'assets/js/wishlist.js',
  'assets/js/analytics.js',
  'assets/js/sharing.js',
  'assets/js/wordpress-client.js',
  'assets/js/avatar-assistant.js',
  // assets/data
  'assets/data/alt-text.json',
  'assets/data/product-content.json',
  'assets/data/woocommerce-import.csv',
  // build/
  'build/ecommerce-process.py',
  'build/composite-with-bgs.py',
  'build/watch-pipeline.py',
  'build/sharp-exports.js',
  'build/gemini-content.js',
  'build/generate-woocommerce-csv.js',
  'build/tool-calling.js',
  // api/
  'api/assistant.js',
];

for (const f of REQUIRED_FILES) {
  record(fileExists(f), f, /* critical */ true);
}

// ===========================================================================
// SECTION 2: Package.json Dependencies
// ===========================================================================
sectionHeader(2, TOTAL_SECTIONS, 'Package.json Dependencies');

const pkgJson = readJSON('package.json');
const REQUIRED_PKGS = [
  '@anthropic-ai/sdk',
  '@ai-sdk/anthropic',
  '@ai-sdk/openai',
  '@ai-sdk/google',
  'openai',
  'ai',
  '@google/genai',
  'zod',
  'react',
  'framer-motion',
  'gsap',
  'three',
  'hono',
  '@supabase/supabase-js',
  'stripe',
  'better-auth',
  'drizzle-orm',
  'sharp',
];

if (!pkgJson) {
  record(false, 'package.json — could not parse', true);
} else {
  const allDeps = {
    ...pkgJson.dependencies,
    ...pkgJson.devDependencies,
    ...pkgJson.peerDependencies,
  };
  for (const pkg of REQUIRED_PKGS) {
    const found = pkg in allDeps;
    record(found, pkg, false, found ? null : 'not listed in package.json');
  }
}

// ===========================================================================
// SECTION 3: Node Module Resolution
// ===========================================================================
sectionHeader(3, TOTAL_SECTIONS, 'Node Module Resolution');

const REQUIRE_PKGS = [
  '@anthropic-ai/sdk',
  '@ai-sdk/anthropic',
  '@ai-sdk/openai',
  '@ai-sdk/google',
  'openai',
  'ai',
  '@google/genai',
  'zod',
  'sharp',
];

for (const pkg of REQUIRE_PKGS) {
  try {
    require(path.join(ROOT, 'node_modules', pkg));
    record(true, `require('${pkg}')`, true);
  } catch (e) {
    record(false, `require('${pkg}')`, /* critical */ true, e.message.split('\n')[0]);
  }
}

// ===========================================================================
// SECTION 4: Data Integrity
// ===========================================================================
sectionHeader(4, TOTAL_SECTIONS, 'Data Integrity');

// alt-text.json
const altText = readJSON('assets/data/alt-text.json');
if (!altText) {
  record(false, 'alt-text.json — could not parse');
} else {
  // Schema: { productId: { imageKey: "alt text string" } }
  const productIds = Array.isArray(altText) ? altText.map(e => e.id) : Object.keys(altText);
  const hasEntries = productIds.length > 0;
  record(hasEntries, `alt-text.json — has entries (${productIds.length} found)`, false,
         hasEntries ? null : 'empty file');
  // Verify each product has at least one image with a non-empty alt string
  const allHaveAlts = productIds.every(id => {
    const val = altText[id];
    if (typeof val === 'string') return val.length > 0;
    if (typeof val === 'object' && val !== null) return Object.values(val).some(v => typeof v === 'string' && v.length > 0);
    return false;
  });
  record(allHaveAlts, 'alt-text.json — all products have alt text strings', false,
         allHaveAlts ? null : 'some products missing alt text');
}

// product-content.json
const productContent = readJSON('assets/data/product-content.json');
if (!productContent) {
  record(false, 'product-content.json — could not parse');
} else {
  const entries = Array.isArray(productContent)
    ? productContent
    : Object.values(productContent);
  const hasEntries = entries.length > 0;
  record(hasEntries, `product-content.json — has entries (${entries.length} found)`, false,
         hasEntries ? null : 'empty file');
  const allHaveDesc = entries.every(e => e && typeof e === 'object' && 'description' in e);
  record(allHaveDesc, 'product-content.json — all entries have "description" field', false,
         allHaveDesc ? null : 'some entries missing "description"');
}

// woocommerce-import.csv
const csvText = readText('assets/data/woocommerce-import.csv');
if (!csvText) {
  record(false, 'woocommerce-import.csv — could not read');
} else {
  const csvRows = parseCSV(csvText);
  const rowCount = csvRows.length - 1; // exclude header
  record(rowCount > 0, `woocommerce-import.csv — has rows (${rowCount} data rows)`, false,
         rowCount > 0 ? null : 'no data rows found');

  // Check for $0 price products (Regular price column)
  if (csvRows.length > 1) {
    const headers    = csvRows[0];
    const priceIdx   = headers.indexOf('Regular price');
    const typeIdx    = headers.indexOf('Type');
    if (priceIdx !== -1 && typeIdx !== -1) {
      const zeroPriceProducts = csvRows.slice(1).filter(row => {
        const type  = (row[typeIdx]  || '').trim().toLowerCase();
        const price = (row[priceIdx] || '').trim();
        // variable parent rows intentionally have no price; skip them
        return type !== 'variable' && type !== 'grouped' && price === '0';
      });
      record(zeroPriceProducts.length === 0,
             `woocommerce-import.csv — no $0 price products`, false,
             zeroPriceProducts.length > 0
               ? `${zeroPriceProducts.length} product(s) have $0 price`
               : null);
    }
  }
}

// Minimum 20 products across data files
const altCount  = altText
  ? (Array.isArray(altText) ? altText : Object.values(altText)).length
  : 0;
const prodCount = productContent
  ? (Array.isArray(productContent) ? productContent : Object.values(productContent)).length
  : 0;
const maxCount  = Math.max(altCount, prodCount);
record(maxCount >= 20,
       `Minimum 20 products in data files (found ${maxCount})`, false,
       maxCount < 20 ? `only ${maxCount} products found` : null);

// ===========================================================================
// SECTION 5: Python Environment
// ===========================================================================
sectionHeader(5, TOTAL_SECTIONS, 'Python Environment');

try {
  execSync('python3 -c "import rembg, PIL, watchdog, numpy; print(\'ok\')"',
           { stdio: 'pipe', timeout: 30000 });
  record(true, 'python3 — rembg, PIL, watchdog, numpy all importable');
} catch (e) {
  const stderr = e.stderr ? e.stderr.toString() : e.message;
  record(false, 'python3 — required packages not available',
         false, stderr.split('\n')[0]);
}

// Numpy version ceiling (≤ 2.3.x for numba compatibility)
try {
  const numpyVer = execSync(
    'python3 -c "import numpy; print(numpy.__version__)"',
    { stdio: 'pipe', timeout: 10000 }
  ).toString().trim();

  const parts = numpyVer.split('.').map(Number);
  const major = parts[0] || 0;
  const minor = parts[1] || 0;
  const withinCeiling = major < 2 || (major === 2 && minor <= 3);
  record(withinCeiling,
         `numpy version ${numpyVer} — within ≤2.3.x ceiling`, false,
         withinCeiling ? null : `version ${numpyVer} exceeds numba ceiling 2.3.x`);
} catch (e) {
  record('warn', 'numpy version check — could not determine version', false,
         e.message.split('\n')[0]);
}

// ===========================================================================
// SECTION 6: Image Assets
// ===========================================================================
sectionHeader(6, TOTAL_SECTIONS, 'Image Assets');

const ecomDir = rel('assets/images/products-ecom');

// Total files inside products-ecom/*/ subdirectories
const totalEcomFiles = countFilesInDir(ecomDir);
record(totalEcomFiles > 0,
       `assets/images/products-ecom — total image files (${totalEcomFiles} found)`, false,
       totalEcomFiles === 0 ? 'no image files found' : null);

// .avif files
const avifCount = countFilesMatching(ecomDir, /\.avif$/i);
record(avifCount > 0,
       `*.avif files in products-ecom (${avifCount} found)`, false,
       avifCount === 0 ? 'no .avif files found' : null);

// srcset/*400w* files
const srcsetDir = rel('assets/images/products-ecom');
const srcset400wCount = (() => {
  if (!fs.existsSync(srcsetDir)) return 0;
  let count = 0;
  const walk = (d) => {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        if (entry.name === 'srcset') {
          // count matching files inside srcset/
          const srcsetPath = path.join(d, entry.name);
          for (const f of fs.readdirSync(srcsetPath, { withFileTypes: true })) {
            if (!f.isDirectory() && /400w/i.test(f.name)) count++;
          }
        } else {
          walk(path.join(d, entry.name));
        }
      }
    }
  };
  walk(srcsetDir);
  return count;
})();
record(srcset400wCount > 0,
       `srcset/*400w* files in products-ecom (${srcset400wCount} found)`, false,
       srcset400wCount === 0 ? 'no srcset/400w files found' : null);

// social/*square* files
const socialSquareCount = (() => {
  if (!fs.existsSync(ecomDir)) return 0;
  let count = 0;
  const walk = (d) => {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        if (entry.name === 'social') {
          const socialPath = path.join(d, entry.name);
          for (const f of fs.readdirSync(socialPath, { withFileTypes: true })) {
            if (!f.isDirectory() && /square/i.test(f.name)) count++;
          }
        } else {
          walk(path.join(d, entry.name));
        }
      }
    }
  };
  walk(ecomDir);
  return count;
})();
record(socialSquareCount > 0,
       `social/*square* files in products-ecom (${socialSquareCount} found)`, false,
       socialSquareCount === 0 ? 'no social/square files found' : null);

// ===========================================================================
// SECTION 7: Service Worker
// ===========================================================================
sectionHeader(7, TOTAL_SECTIONS, 'Service Worker');

const swText = readText('sw.js');
if (!swText) {
  record(false, 'sw.js — could not read', false, 'file missing or unreadable');
} else {
  const SW_TOKENS = ['install', 'activate', 'fetch', 'sync', 'SKIP_WAITING'];
  for (const token of SW_TOKENS) {
    const found = swText.includes(token);
    record(found, `sw.js contains '${token}'`, false,
           found ? null : `'${token}' not found in sw.js`);
  }
}

// ===========================================================================
// SECTION 8: WooCommerce CSV Deep Check
// ===========================================================================
sectionHeader(8, TOTAL_SECTIONS, 'WooCommerce CSV');

if (!csvText) {
  record(false, 'woocommerce-import.csv — skipped (file not readable)');
} else {
  const csvRows = parseCSV(csvText);
  const headers = csvRows[0] || [];
  const dataRows = csvRows.slice(1);

  // Required columns
  const REQUIRED_COLS = ['Type', 'SKU', 'Name', 'Regular price', 'Images'];
  for (const col of REQUIRED_COLS) {
    const found = headers.includes(col);
    record(found, `CSV column "${col}" present`, false,
           found ? null : `column "${col}" missing from CSV`);
  }

  // Count row types
  const typeIdx = headers.indexOf('Type');
  const skuIdx  = headers.indexOf('SKU');

  let variationCount = 0;
  let groupedCount   = 0;
  let badSKUCount    = 0;
  const SKU_PATTERN  = /^SR-[A-Z]{2,}-[A-Z0-9]{3,}/;

  for (const row of dataRows) {
    const type = (row[typeIdx] || '').trim().toLowerCase();
    const sku  = (row[skuIdx]  || '').trim();

    if (type === 'variation') variationCount++;
    if (type === 'grouped')   groupedCount++;

    if (sku && !SKU_PATTERN.test(sku)) badSKUCount++;
  }

  record(variationCount > 0,
         `CSV variation rows (${variationCount} found)`, false,
         variationCount === 0 ? 'no variation rows found' : null);

  record(groupedCount >= 0,   // informational — grouped products are optional
         `CSV grouped rows (${groupedCount} found)`);

  record(badSKUCount === 0,
         'CSV SKUs follow SR-XX-XXX pattern', false,
         badSKUCount > 0 ? `${badSKUCount} SKU(s) do not match SR-XX-XXX pattern` : null);
}

// ===========================================================================
// SECTION 9: Environment Variables
// ===========================================================================
sectionHeader(9, TOTAL_SECTIONS, 'Environment Variables');

const ENV_KEYS = [
  'OPENAI_API_KEY',
  'GEMINI_API_KEY',
  'ANTHROPIC_API_KEY',
  'WORDPRESS_URL',
  'WC_CONSUMER_KEY',
];

for (const key of ENV_KEYS) {
  const isSet = !!(process.env[key] && process.env[key].trim());
  if (isSet) {
    record(true, `${key} — set`);
  } else {
    record('warn', `${key} — not set`, false, 'API key missing (non-blocking)');
  }
}

// ===========================================================================
// SUMMARY
// ===========================================================================
console.log(lines.join('\n'));
console.log('');
console.log(fmt('dim', '========================================================'));
console.log('');
console.log(bold('  [Results]'));
console.log(`    ${fmt('green', 'Passed:')}   ${bold(totalPass)} / ${totalPass + totalFail + totalWarn}`);
console.log(`    ${fmt('red',   'Failed:')}   ${bold(totalFail)}`);
console.log(`    ${fmt('yellow','Warnings:')} ${bold(totalWarn)}`);

if (failures.length > 0) {
  console.log('');
  console.log(`  ${fmt('red', bold('FAILURES:'))}`);
  for (const f of failures) {
    console.log(`    ${fmt('red', '-')} ${f}`);
  }
}

if (warnings.length > 0) {
  console.log('');
  console.log(`  ${fmt('yellow', bold('WARNINGS:'))}`);
  for (const w of warnings) {
    console.log(`    ${fmt('yellow', '-')} ${w}`);
  }
}

console.log('');
if (criticalFail) {
  console.log(`  ${fmt('red', bold('❌ Critical failures detected — fix before deploying'))}`);
  console.log('');
  process.exit(1);
} else if (totalFail > 0) {
  console.log(`  ${fmt('yellow', bold('⚠️  Non-critical failures — review before deploying'))}`);
  console.log('');
  process.exit(0);
} else {
  console.log(`  ${fmt('green', bold('✅ Core build verified — ready for deployment'))}`);
  console.log('');
  process.exit(0);
}
