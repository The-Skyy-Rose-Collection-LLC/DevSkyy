#!/usr/bin/env node

/**
 * CSS Build Script for SkyyRose Flagship Theme
 * Discovers and minifies all CSS source files with source maps.
 *
 * Handles:
 * - assets/css/**\/*.css (recursive, catches system/animations.css)
 * - Root style.css (preserves WordPress theme header comment)
 *
 * Usage: node scripts/build-css.js
 */

'use strict';

const CleanCSS = require('clean-css');
const fs = require('fs');
const path = require('path');
const glob = require('glob');

const rootDir = path.resolve(__dirname, '..');

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

    // Write minified CSS (prepend header for root style.css)
    const minContent = headerComment + output.styles;
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
