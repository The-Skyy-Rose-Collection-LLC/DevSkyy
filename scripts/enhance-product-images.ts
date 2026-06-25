#!/usr/bin/env npx tsx
/**
 * Non-Destructive Product Image Enhancement
 *
 * Processes product images through the LuxuryImageProcessor.applyLuxuryGrading
 * pipeline and writes enhanced derivatives to a parallel directory.
 *
 * Usage:
 *   npx tsx scripts/enhance-product-images.ts [--input <dir>] [--output <dir>] [--dry-run]
 *
 * Defaults:
 *   --input  wordpress-theme/skyyrose-flagship/assets/images/products
 *   --output wordpress-theme/skyyrose-flagship/assets/images/products-enhanced
 *
 * Original files are NEVER modified. Enhanced derivatives are written with
 * the same filename structure to the output directory.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

import { existsSync, mkdirSync, readdirSync, statSync } from 'fs';
import { readFile, writeFile } from 'fs/promises';
import { basename, extname, join, relative } from 'path';
import sharp from 'sharp';

// ── Config ─────────────────────────────────────────────────────────────
const DEFAULTS = {
  input: 'wordpress-theme/skyyrose-flagship/assets/images/products',
  output: 'wordpress-theme/skyyrose-flagship/assets/images/products-enhanced',
};

const SUPPORTED_EXTS = new Set(['.jpg', '.jpeg', '.png', '.webp', '.avif']);

// ── SkyyRose Luxury Color Grade (mirrors LuxuryImageProcessor) ────────
async function applyLuxuryGrading(buffer: Buffer): Promise<Buffer> {
  // Step 1: SkyyRose signature color grading
  const graded = await sharp(buffer)
    .modulate({
      brightness: 1.05,   // Slightly brighter
      saturation: 1.15,   // More saturated
      hue: -5,            // Shift towards rose/pink
    })
    .linear(1.1, -(128 * 0.1))  // Increase contrast
    .tint({ r: 183, g: 110, b: 121 })  // #B76E79 tint
    .toBuffer();

  // Step 2: Luxury curves
  return sharp(graded)
    .gamma(1.2)        // Lift shadows
    .normalize()       // Stretch histogram
    .sharpen({ sigma: 1 })  // Slight sharpening
    .webp({ quality: 92 })
    .toBuffer();
}

// ── CLI ────────────────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');

  let inputDir = DEFAULTS.input;
  let outputDir = DEFAULTS.output;

  const inputIdx = args.indexOf('--input');
  if (inputIdx !== -1 && args[inputIdx + 1]) inputDir = args[inputIdx + 1];

  const outputIdx = args.indexOf('--output');
  if (outputIdx !== -1 && args[outputIdx + 1]) outputDir = args[outputIdx + 1];

  if (!existsSync(inputDir)) {
    console.error(`Input directory not found: ${inputDir}`);
    process.exit(1);
  }

  // Collect image files recursively
  const files: string[] = [];
  function walk(dir: string) {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        walk(full);
      } else if (SUPPORTED_EXTS.has(extname(entry).toLowerCase())) {
        files.push(full);
      }
    }
  }
  walk(inputDir);

  console.log(`Found ${files.length} product images in ${inputDir}`);
  if (dryRun) {
    console.log('Dry run — no files will be written.');
    files.forEach((f) => console.log(`  Would enhance: ${relative(inputDir, f)}`));
    return;
  }

  mkdirSync(outputDir, { recursive: true });

  let processed = 0;
  let failed = 0;

  for (const file of files) {
    const rel = relative(inputDir, file);
    const outPath = join(outputDir, rel.replace(extname(rel), '.webp'));
    const outSubDir = join(outputDir, relative(inputDir, join(file, '..')));

    mkdirSync(outSubDir, { recursive: true });

    try {
      const inputBuffer = await readFile(file);
      const enhanced = await applyLuxuryGrading(inputBuffer);
      await writeFile(outPath, enhanced);
      processed++;
      console.log(`  ✓ ${rel} → ${basename(outPath)}`);
    } catch (err) {
      failed++;
      console.error(`  ✗ ${rel}: ${(err as Error).message}`);
    }
  }

  console.log(`\nDone: ${processed} enhanced, ${failed} failed.`);
  console.log(`Originals untouched in: ${inputDir}`);
  console.log(`Enhanced derivatives in: ${outputDir}`);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
