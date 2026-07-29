#!/usr/bin/env node

/**
 * CSS Build Script for SkyyRose Flagship Theme
 * Discovers and minifies all CSS source files with source maps.
 *
 * Handles:
 * - assets/css/**\/*.css (recursive, catches system/animations.css)
 * - Root style.css (preserves WordPress theme header comment)
 *
 * Usage: node scripts/build-css.js            (write .min.css + .map)
 *        node scripts/build-css.js --check    (verify only, write nothing)
 *
 * --check exits 1 if any .min.css differs from what a build would produce, or
 * is missing. It lives here rather than in the verify harness so the staleness
 * check uses this file's exact CleanCSS options and style.css header handling
 * -- a second copy of that config would drift and report false staleness.
 */

'use strict';

const CleanCSS = require('clean-css');
const fs = require('fs');
const path = require('path');
const glob = require('glob');

const rootDir = path.resolve(__dirname, '..');
const CHECK_ONLY = process.argv.includes('--check');

// Discover all CSS source files (exclude already-minified)
const assetFiles = glob.sync('assets/css/**/*.css', {
  cwd: rootDir,
  ignore: 'assets/css/**/*.min.css',
});

// Include root style.css
const cssFiles = [...assetFiles, 'style.css'];

let processed = 0;
let failed = 0;
const results = [];
const stale = [];
// relPath -> minified content, for the bundle phase below. Bundles are built
// from these in-memory results so --check verifies them without writing.
const minByRel = {};

cssFiles.forEach(relPath => {
  const srcPath = path.resolve(rootDir, relPath);
  const minPath = srcPath.replace(/\.css$/, '.min.css');
  const mapPath = minPath + '.map';

  try {
    const source = fs.readFileSync(srcPath, 'utf8');

    // For root style.css: preserve the WordPress theme header comment.
    // The header uses /* (no bang), so CleanCSS strips it by default.
    // Strategy: extract header, minify body, prepend header to output.
    const isRootStyle = relPath === 'style.css';
    let headerComment = '';
    let cssBody = source;

    if (isRootStyle) {
      // Extract the first block comment (WordPress theme header)
      const headerMatch = source.match(/^(\/\*[\s\S]*?\*\/)/);
      if (headerMatch) {
        headerComment = headerMatch[1] + '\n';
        cssBody = source.slice(headerMatch[0].length);
      }
    }

    const output = new CleanCSS({
      sourceMap: true,
      level: { 1: { specialComments: 0 } }, // Strip all comments (header handled separately)
    }).minify(cssBody);

    if (output.errors && output.errors.length > 0) {
      console.error(`  FAIL: ${relPath} -- ${output.errors.join(', ')}`);
      failed++;
      return;
    }

    // Minified CSS (prepend header for root style.css)
    const minContent = headerComment + output.styles;
    minByRel[relPath] = minContent;

    if (CHECK_ONLY) {
      // Compare against what is on disk. Content, not mtime: git checkouts and
      // `touch` reorder mtimes without changing bytes, which made an
      // mtime-based staleness check report false positives.
      if (!fs.existsSync(minPath)) {
        stale.push(`${relPath} -- .min.css missing`);
      } else if (fs.readFileSync(minPath, 'utf8') !== minContent) {
        stale.push(`${relPath} -- .min.css differs from source`);
      }
      processed++;
      return;
    }

    fs.writeFileSync(minPath, minContent);

    // Write source map
    if (output.sourceMap) {
      fs.writeFileSync(mapPath, output.sourceMap.toString());
    }

    const srcSize = Buffer.byteLength(source, 'utf8');
    const minSize = Buffer.byteLength(minContent, 'utf8');
    const savings = srcSize > 0 ? Math.round((1 - minSize / srcSize) * 100) : 0;
    results.push({ file: relPath, srcSize, minSize, savings });
    processed++;
  } catch (err) {
    console.error(`  FAIL: ${relPath} -- ${err.message}`);
    failed++;
  }
});

// Bundle phase: concatenate the minified outputs listed in bundles.config.js,
// in order. A bundle is exactly its parts' .min contents joined with '\n', so
// cascade order inside a bundle is the config's list order. Fails closed: a
// part missing from the build (renamed/deleted source) is a hard error, never
// a silently smaller bundle.
const bundles = require('./bundles.config.js').css;
Object.entries(bundles).forEach(([bundleRel, parts]) => {
  const missing = parts.filter(p => !(p in minByRel));
  if (missing.length > 0) {
    console.error(`  FAIL: ${bundleRel} -- missing part(s): ${missing.join(', ')}`);
    failed++;
    return;
  }
  const content = parts.map(p => minByRel[p]).join('\n');
  const bundlePath = path.resolve(rootDir, bundleRel);

  if (CHECK_ONLY) {
    if (!fs.existsSync(bundlePath)) {
      stale.push(`${bundleRel} -- bundle missing`);
    } else if (fs.readFileSync(bundlePath, 'utf8') !== content) {
      stale.push(`${bundleRel} -- bundle differs from fresh concat`);
    }
    return;
  }

  fs.mkdirSync(path.dirname(bundlePath), { recursive: true });
  fs.writeFileSync(bundlePath, content);
  results.push({
    file: bundleRel,
    srcSize: content.length,
    minSize: content.length,
    savings: 0,
  });
});

if (CHECK_ONLY) {
  if (failed > 0) {
    console.error(`[build:css --check] ${failed} file(s) failed to minify`);
    process.exit(1);
  }
  if (stale.length > 0) {
    console.error(`[build:css --check] ${stale.length} stale .min.css file(s):`);
    stale.forEach(s => console.error(`  ${s}`));
    console.error('[build:css --check] Run: npm run build:css');
    process.exit(1);
  }
  console.log(`[build:css --check] ${processed} file(s) in sync with source.`);
  process.exit(0);
}

// Print summary
console.log(`[build:css] Minified ${processed} files:`);
results.forEach(r => {
  console.log(`  ${r.file} (${r.srcSize}B -> ${r.minSize}B, ${r.savings}% smaller)`);
});

if (failed > 0) {
  console.error(`[build:css] ${failed} file(s) failed`);
  process.exit(1);
}

console.log(`[build:css] Done -- ${processed} files processed, 0 failures`);
