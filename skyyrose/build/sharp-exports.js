/**
 * SkyyRose — Sharp Multi-Format Export Pipeline
 * =============================================
 * Takes processed product master PNGs and generates:
 *   - AVIF (30-50% smaller than WebP)
 *   - Responsive srcset: 400w / 800w / 1200w WebP
 *   - Blur placeholder: tiny 40px blurred JPEG for lazy load
 *   - Social crops: 1:1 Square, 4:5 Portrait, 9:16 Story, 16:9 Wide
 *     with SkyyRose watermark on social exports
 *   - Color normalized (sRGB) + EXIF/GPS metadata stripped
 *
 * Usage:
 *   node build/sharp-exports.js            # all products
 *   node build/sharp-exports.js br-001     # single product
 *   node build/sharp-exports.js --social   # social crops only
 *   node build/sharp-exports.js --srcset   # srcset only
 */

const sharp = require('sharp');
const path  = require('path');
const fs    = require('fs').promises;

const ROOT      = path.join(__dirname, '..');
const ECOM_DIR  = path.join(ROOT, 'assets/images/products-ecom');
const LOGO_PATH = path.join(ROOT, 'assets/images/source-products/logos/PhotoRoom_20230130_001050.png');

const SOCIAL_SIZES = [
  { name: 'square',   w: 1080, h: 1080, label: '1:1 Instagram' },
  { name: 'portrait', w: 1080, h: 1350, label: '4:5 Instagram Feed' },
  { name: 'story',    w: 1080, h: 1920, label: '9:16 Stories/TikTok' },
  { name: 'wide',     w: 1920, h: 1080, label: '16:9 Banner/YouTube' },
];

const SRCSET_WIDTHS = [400, 800, 1200];

const args       = process.argv.slice(2);
const targetId   = args.find(a => !a.startsWith('--'));
const doSocial   = args.includes('--social') || !args.some(a => a.startsWith('--'));
const doSrcset   = args.includes('--srcset') || !args.some(a => a.startsWith('--'));
const doAvif     = args.includes('--avif')   || !args.some(a => a.startsWith('--'));

async function prepareLogo(targetSize) {
  try {
    const logoSize = Math.round(targetSize * 0.12); // 12% of canvas width
    return await sharp(LOGO_PATH)
      .resize(logoSize, logoSize, { fit: 'inside' })
      .composite([{
        input: Buffer.from([0,0,0,0].concat(new Array(logoSize * logoSize * 4).fill(0))),
        raw: { width: 1, height: 1, channels: 4 },
        tile: true, blend: 'dest-in'
      }])
      .png()
      .toBuffer()
      .catch(() => null);
  } catch { return null; }
}

async function addWatermark(sharpInst, canvasW, canvasH) {
  try {
    const logoSize = Math.round(canvasW * 0.10);
    const logoBuffer = await sharp(LOGO_PATH)
      .resize(logoSize, logoSize, { fit: 'inside' })
      .png()
      .toBuffer();
    const padding = Math.round(canvasW * 0.03);
    return sharpInst.composite([{
      input: logoBuffer,
      gravity: 'southeast',
      blend: 'over',
    }]);
  } catch {
    return sharpInst;
  }
}

async function processProduct(productDir, productId) {
  const masters = [];
  try {
    const files = await fs.readdir(productDir);
    for (const f of files) {
      if (f.endsWith('-master.png')) masters.push(f);
    }
  } catch { return 0; }

  if (masters.length === 0) return 0;

  let total = 0;
  const srcsetDir = path.join(productDir, 'srcset');
  const socialDir = path.join(productDir, 'social');

  if (doSrcset || doAvif) await fs.mkdir(srcsetDir, { recursive: true });
  if (doSocial)           await fs.mkdir(socialDir, { recursive: true });

  for (const masterFile of masters) {
    const stem      = masterFile.replace('-master.png', '');
    const masterPath = path.join(productDir, masterFile);
    const webJpg    = path.join(productDir, `${stem}-web.jpg`);

    // Use web.jpg as source if available (white bg), else master PNG
    const srcPath = await fs.access(webJpg).then(() => webJpg).catch(() => masterPath);

    // ── AVIF ────────────────────────────────────────────────────────────────
    if (doAvif) {
      const avifOut = path.join(productDir, `${stem}-web.avif`);
      try {
        await fs.access(avifOut);
        // skip existing
      } catch {
        await sharp(srcPath)
          .avif({ quality: 75, effort: 4 })
          .withMetadata({ icc: 'srgb' })  // normalize to sRGB, strip GPS/EXIF
          .toFile(avifOut);
        const sz = Math.round((await fs.stat(avifOut)).size / 1024);
        console.log(`    ✅ avif   ${stem} (${sz}KB)`);
        total++;
      }
    }

    // ── SRCSET ───────────────────────────────────────────────────────────────
    if (doSrcset) {
      for (const w of SRCSET_WIDTHS) {
        const out = path.join(srcsetDir, `${stem}-${w}w.webp`);
        try {
          await fs.access(out);
        } catch {
          await sharp(srcPath)
            .resize(w, w, { fit: 'inside', withoutEnlargement: true })
            .webp({ quality: 85, effort: 4 })
            .withMetadata({ icc: 'srgb' })
            .toFile(out);
          const sz = Math.round((await fs.stat(out)).size / 1024);
          console.log(`    ✅ ${w}w    ${stem} (${sz}KB)`);
          total++;
        }
      }

      // Blur placeholder — tiny 40px blurred JPEG
      const blurOut = path.join(srcsetDir, `${stem}-blur.jpg`);
      try {
        await fs.access(blurOut);
      } catch {
        await sharp(srcPath)
          .resize(40, 40, { fit: 'inside' })
          .blur(3)
          .jpeg({ quality: 40 })
          .toFile(blurOut);
        console.log(`    ✅ blur   ${stem}`);
        total++;
      }
    }

    // ── SOCIAL CROPS ─────────────────────────────────────────────────────────
    if (doSocial) {
      for (const size of SOCIAL_SIZES) {
        const out = path.join(socialDir, `${stem}-${size.name}.jpg`);
        try {
          await fs.access(out);
          continue;
        } catch {}

        // Create canvas and center product
        let inst = sharp(srcPath)
          .resize(size.w, size.h, {
            fit: 'contain',
            background: { r: 255, g: 255, b: 255, alpha: 1 }
          });

        // Add watermark
        inst = await addWatermark(inst, size.w, size.h);

        await inst
          .jpeg({ quality: 90, mozjpeg: true })
          .withMetadata({ icc: 'srgb' })
          .toFile(out);

        const sz = Math.round((await fs.stat(out)).size / 1024);
        console.log(`    ✅ ${size.name.padEnd(8)} ${stem} (${sz}KB)`);
        total++;
      }
    }
  }

  return total;
}

async function main() {
  const mode = [doAvif && 'AVIF', doSrcset && 'srcset+blur', doSocial && 'social crops']
    .filter(Boolean).join(' + ');

  console.log('\n SkyyRose — Sharp Multi-Format Export Pipeline');
  console.log('='.repeat(56));
  console.log(`  Mode: ${mode}`);
  console.log(`  Watermark: ${LOGO_PATH.split('/').pop()}\n`);

  // Verify sharp and logo
  try { await fs.access(LOGO_PATH); } catch {
    console.log('  ⚠️  Logo not found — social exports will skip watermark');
  }

  const dirs = await fs.readdir(ECOM_DIR);
  let grandTotal = 0;

  for (const dir of dirs.sort()) {
    if (dir.startsWith('_')) continue;
    if (targetId && dir !== targetId) continue;

    const productDir = path.join(ECOM_DIR, dir);
    const stat = await fs.stat(productDir);
    if (!stat.isDirectory()) continue;

    console.log(`\n  [${dir.toUpperCase()}]`);
    const n = await processProduct(productDir, dir);
    grandTotal += n;
    if (n === 0) console.log('    — already exported or no masters found');
  }

  console.log('\n' + '='.repeat(56));
  console.log(`  Done — ${grandTotal} files exported`);
  console.log(`  Outputs: products-ecom/{id}/srcset/ + social/\n`);
}

main().catch(e => { console.error('\nFatal:', e.message); process.exit(1); });
