/**
 * SkyyRose — Logo Optimization Pipeline
 *
 * Processes official branding assets:
 * 1. Background removal (ImageMagick — white/dark bg → transparent)
 * 2. Resize to 5 sizes: favicon (64), icon (200), nav (400), hero (1024), og (1200)
 * 3. Export WebP + PNG dual format (PNG for transparency, WebP for performance)
 * 4. Generate favicon set from SR Monogram
 *
 * Usage:
 *   node build/optimize-logos.js           # Process all logos
 *   node build/optimize-logos.js --dry-run # Preview only
 */

const path = require('path');
const fs = require('fs').promises;
const sharp = require('sharp');
const { execSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const BRANDING_DIR = path.join(ROOT, 'assets', 'images', 'branding');
const OUTPUT_DIR = path.join(BRANDING_DIR, 'optimized');
const DRY_RUN = process.argv.includes('--dry-run');

// ─── Official Logo Registry (owner-confirmed) ─────────────────────

const LOGOS = [
  // PRIMARY BRAND
  {
    source: 'primary/sr-monogram.jpeg',
    slug: 'sr-monogram',
    collection: 'primary',
    bgType: 'light',
    description: 'SR calligraphy monogram with rose bloom',
  },

  // SIGNATURE COLLECTION
  {
    source: 'signature/sr-rose-geometric.png',
    slug: 'sr-rose-geometric',
    collection: 'signature',
    bgType: 'light',
    description: 'Rose gold geometric cutout rose',
  },
  {
    source: 'signature/signature-3d-wordmark.png',
    slug: 'signature-3d-wordmark',
    collection: 'signature',
    bgType: 'light',
    description: '"The Skyy Rose COLLECTION" glass/crystal text',
  },

  // LOVE HURTS COLLECTION
  {
    source: 'love-hurts/love-hurts-enamel-pin.jpeg',
    slug: 'love-hurts-enamel-pin',
    collection: 'love-hurts',
    bgType: 'light',
    description: 'Cracked heart + thorns enamel pin, crimson script',
  },
  {
    source: 'love-hurts/love-hurts-neon-star.jpeg',
    slug: 'love-hurts-neon-star',
    collection: 'love-hurts',
    bgType: 'dark',
    description: 'Red neon star frame with rose + cracked heart',
  },
  {
    source: 'love-hurts/love-hurts-heart-roses.png',
    slug: 'love-hurts-heart-roses',
    collection: 'love-hurts',
    bgType: 'light',
    description: 'Full illustration — cracked heart, thorns, roses',
  },

  // BLACK ROSE COLLECTION
  {
    source: 'black-rose/black-rose-crystal-star.jpeg',
    slug: 'black-rose-crystal-star',
    collection: 'black-rose',
    bgType: 'dark',
    description: 'Crystal star trophy with black rose, walnut heart base',
  },
  {
    source: 'black-rose/black-rose-letter-logo.png',
    slug: 'black-rose-letter-logo',
    collection: 'black-rose',
    bgType: 'light',
    description: '"The Black Rose Collection" glossy 3D script',
  },
];

// ─── Size Variants ─────────────────────────────────────────────────

const SIZES = [
  { name: 'favicon', width: 64 },
  { name: 'icon', width: 200 },
  { name: 'nav', width: 400 },
  { name: 'hero', width: 1024 },
  { name: 'og', width: 1200 },
];

// ─── Sharp Config ──────────────────────────────────────────────────

const PNG_OPTS = { quality: 95, compressionLevel: 9, adaptiveFiltering: true };
const WEBP_OPTS = { quality: 90, alphaQuality: 100 };

// ─── Background Removal (ImageMagick) ──────────────────────────────

function removeBg(inputPath, outputPath, bgType) {
  const fuzz = bgType === 'dark' ? 20 : 15;
  const targetColor = bgType === 'dark' ? 'black' : 'white';

  const cmd = [
    'convert', `"${inputPath}"`,
    '-fuzz', `${fuzz}%`,
    '-transparent', targetColor,
    '-trim', '+repage',
    '-channel', 'A', '-blur', '0x0.5', '-level', '50%,100%', '+channel',
    `"${outputPath}"`,
  ].join(' ');

  if (DRY_RUN) {
    console.log(`    [dry-run] bg-remove (${targetColor}, fuzz ${fuzz}%)`);
    return false;
  }

  try {
    execSync(cmd, { stdio: 'pipe' });
    return true;
  } catch (err) {
    console.error(`    [error] ImageMagick: ${err.stderr?.toString().trim() || err.message}`);
    return false;
  }
}

// ─── Resize + Export ───────────────────────────────────────────────

async function resizeAndExport(inputPath, outputBase) {
  const results = [];

  for (const { name, width } of SIZES) {
    const pngOut = `${outputBase}-${name}.png`;
    const webpOut = `${outputBase}-${name}.webp`;

    if (DRY_RUN) {
      console.log(`    [dry-run] ${name} → ${width}px (PNG + WebP)`);
      results.push({ name, width });
      continue;
    }

    try {
      await sharp(inputPath)
        .resize({ width, fit: 'inside', withoutEnlargement: true, kernel: sharp.kernel.lanczos3 })
        .sharpen({ sigma: 0.5 })
        .png(PNG_OPTS)
        .toFile(pngOut);

      await sharp(inputPath)
        .resize({ width, fit: 'inside', withoutEnlargement: true, kernel: sharp.kernel.lanczos3 })
        .webp(WEBP_OPTS)
        .toFile(webpOut);

      const pngKB = ((await fs.stat(pngOut)).size / 1024).toFixed(1);
      const webpKB = ((await fs.stat(webpOut)).size / 1024).toFixed(1);
      console.log(`    ${name} (${width}px): PNG ${pngKB}KB | WebP ${webpKB}KB`);
      results.push({ name, width, pngKB, webpKB });
    } catch (err) {
      console.error(`    [error] ${name}: ${err.message}`);
    }
  }

  return results;
}

// ─── Favicon Generation ────────────────────────────────────────────

async function generateFavicons(sourcePath) {
  console.log('\n  Generating favicons from SR Monogram...');

  const faviconDir = path.join(OUTPUT_DIR, 'favicons');
  if (!DRY_RUN) await fs.mkdir(faviconDir, { recursive: true });

  const sizes = [16, 32, 48, 64, 128, 180, 192, 512];

  for (const size of sizes) {
    const outPath = path.join(faviconDir, `favicon-${size}x${size}.png`);

    if (DRY_RUN) {
      console.log(`    [dry-run] favicon ${size}x${size}`);
      continue;
    }

    await sharp(sourcePath)
      .resize(size, size, {
        kernel: sharp.kernel.lanczos3,
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 },
      })
      .png({ quality: 100 })
      .toFile(outPath);

    const kb = ((await fs.stat(outPath)).size / 1024).toFixed(1);
    console.log(`    favicon ${size}x${size}: ${kb}KB`);
  }
}

// ─── Process Single Logo ───────────────────────────────────────────

async function processLogo(logo) {
  const inputPath = path.join(BRANDING_DIR, logo.source);
  const collectionDir = path.join(OUTPUT_DIR, logo.collection);

  try {
    await fs.access(inputPath);
  } catch {
    console.log(`  [skip] Not found: ${logo.source}`);
    return null;
  }

  if (!DRY_RUN) await fs.mkdir(collectionDir, { recursive: true });

  console.log(`\n  ${logo.slug}`);
  console.log(`  ${logo.description}`);

  // Step 1: Remove background
  const transparentPath = path.join(collectionDir, `${logo.slug}-transparent.png`);
  console.log(`    Removing ${logo.bgType} background...`);
  const bgOk = removeBg(inputPath, transparentPath, logo.bgType);

  // Step 2: Resize from transparent version (or original if bg removal failed)
  const resizeSource = bgOk ? transparentPath : inputPath;
  const outputBase = path.join(collectionDir, logo.slug);
  const results = await resizeAndExport(resizeSource, outputBase);

  return { ...logo, results, bgRemoved: bgOk };
}

// ─── Main ──────────────────────────────────────────────────────────

async function main() {
  console.log('');
  console.log('  SkyyRose Logo Optimization Pipeline');
  console.log(`  Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}`);
  console.log(`  Source: ${BRANDING_DIR}`);
  console.log(`  Output: ${OUTPUT_DIR}`);
  console.log('');

  if (!DRY_RUN) await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const results = [];

  for (const logo of LOGOS) {
    const result = await processLogo(logo);
    if (result) results.push(result);
  }

  // Generate favicons from SR Monogram transparent version
  const monogramTransparent = path.join(OUTPUT_DIR, 'primary', 'sr-monogram-transparent.png');
  const monogramOriginal = path.join(BRANDING_DIR, 'primary', 'sr-monogram.jpeg');
  try {
    const faviconSource = !DRY_RUN
      ? (await fs.access(monogramTransparent).then(() => monogramTransparent).catch(() => monogramOriginal))
      : monogramOriginal;
    await generateFavicons(faviconSource);
  } catch (err) {
    console.error(`  [error] Favicons: ${err.message}`);
  }

  // Summary
  console.log('\n');
  console.log(`  ${results.length}/${LOGOS.length} logos processed`);
  console.log(`  ${results.filter(r => r.bgRemoved).length} backgrounds removed`);

  if (!DRY_RUN) {
    let totalFiles = 0;
    let totalBytes = 0;
    const walk = async (dir) => {
      try {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        for (const e of entries) {
          const p = path.join(dir, e.name);
          if (e.isDirectory()) { await walk(p); }
          else { totalFiles++; totalBytes += (await fs.stat(p)).size; }
        }
      } catch { /* empty */ }
    };
    await walk(OUTPUT_DIR);
    console.log(`  ${totalFiles} files | ${(totalBytes / 1024).toFixed(0)}KB total`);
  }

  console.log(`  Output: ${OUTPUT_DIR}/`);
  console.log('');
}

if (require.main === module) {
  main().catch(err => {
    console.error(`Fatal: ${err.message}`);
    process.exit(1);
  });
}

module.exports = { main, processLogo, generateFavicons, LOGOS };
