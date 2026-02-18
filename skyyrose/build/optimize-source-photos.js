/**
 * SkyyRose — Source Photo Enhancement & Optimization
 * Processes all product, promo, and logo photography
 *
 * Usage: node build/optimize-source-photos.js
 */

const path = require('path');
const fs   = require('fs').promises;
const sharp = require('sharp');

const SOURCE_DIR = path.join(__dirname, '../assets/images/source-products');
const OUTPUT_DIR = path.join(__dirname, '../assets/images/products');

// ── Product catalog (matches assets/data/products-catalog.html) ───────────
const PRODUCT_PHOTOS = [
  // ── BLACK ROSE ────────────────────────────────────────────────────────────
  {
    productId: 'br-001', name: 'BLACK Rose Crewneck', collection: 'black-rose',
    sources: [
      'black-rose/PhotoRoom_011_20230616_170635.png',
      'black-rose/PhotoRoom_001_20230616_170635.PNG',
    ]
  },
  {
    productId: 'br-002', name: 'BLACK Rose Joggers', collection: 'black-rose',
    sources: [
      'black-rose/PhotoRoom_010_20231221_160237.jpeg',
    ]
  },
  {
    productId: 'br-003', name: 'BLACK is Beautiful Jersey', collection: 'black-rose',
    sources: [
      'black-rose/5A8946B1-B51F-4144-BCBB-F028462077A0.jpg',   // Last Oakland Front
      'black-rose/266AD7B0-88A6-4489-AA58-AB72A575BD33 3.JPG', // Last Oakland Back
      'black-rose/The BLACK Jersey (BLACK Rose Collection).jpg', // Front
      'black-rose/BLACK is Beautiful Giants Front.jpg',          // Giants Front
      'black-rose/PhotoRoom_003_20230616_170635 (1).png',        // Giants Back
      'black-rose/PhotoRoom_000_20230616_170635.png',
    ]
  },
  {
    productId: 'br-004', name: 'BLACK Rose Hoodie', collection: 'black-rose',
    sources: [
      'black-rose/PhotoRoom_001_20230523_204834.PNG',
    ]
  },
  {
    productId: 'br-005', name: 'BLACK Rose Hoodie — Signature Edition', collection: 'black-rose',
    sources: [
      'black-rose/PhotoRoom_008_20221210_093149.PNG',
    ]
  },
  {
    productId: 'br-006', name: 'BLACK Rose Sherpa Jacket', collection: 'black-rose',
    sources: [
      'black-rose/The BLACK Rose Sherpa Front.jpg',
      'black-rose/The BLACK Rose Sherpa Back.jpg',
    ]
  },
  {
    productId: 'br-007', name: 'BLACK Rose x Love Hurts Basketball Shorts', collection: 'black-rose',
    sources: [
      'black-rose/PhotoRoom_20221110_201933.PNG',
      'black-rose/PhotoRoom_20221110_202133.PNG',
      'black-rose/IMG_1733.jpeg',
    ]
  },
  {
    productId: 'br-008', name: "Women's BLACK Rose Hooded Dress", collection: 'black-rose',
    sources: [
      'black-rose/Womens Black Rose Hooded Dress.jpeg',
    ]
  },

  // ── LOVE HURTS ───────────────────────────────────────────────────────────
  {
    productId: 'lh-001', name: 'The Fannie', collection: 'love-hurts',
    sources: [
      'love-hurts/IMG_0117.jpeg',
      'love-hurts/4074E988-4DAF-4221-8446-4B93422AF437.jpg',
    ]
  },
  {
    productId: 'lh-002', name: 'Love Hurts Joggers (Black)', collection: 'love-hurts',
    sources: [
      'love-hurts/IMG_2102.png',
    ]
  },
  {
    productId: 'lh-002b', name: 'Love Hurts Joggers (White)', collection: 'love-hurts',
    sources: [
      'love-hurts/IMG_2103.png',
      'love-hurts/IMG_2105.png',
    ]
  },
  {
    productId: 'lh-003', name: 'Love Hurts Basketball Shorts', collection: 'love-hurts',
    sources: [
      'love-hurts/PhotoRoom_004_20221110_200039.png',
      'love-hurts/PhotoRoom_003_20221110_200039.png',
      'love-hurts/PhotoRoom_018_20231221_160237.jpeg',
    ]
  },

  // ── SIGNATURE ────────────────────────────────────────────────────────────
  {
    productId: 'sg-001', name: 'The Bay Set', collection: 'signature',
    sources: [
      'signature/0F85F48C-364B-43CB-8297-E90BB7B8BB51 2.jpg',
      'signature/24661692-0F81-43F4-AA69-7E026552914A.jpg',
    ]
  },
  {
    productId: 'sg-002', name: 'Stay Golden Set', collection: 'signature',
    sources: [
      'signature/562143CF-4A77-42B8-A58C-C77ED21E9B5E.jpg',
    ]
  },
  {
    productId: 'sg-003', name: 'The Signature Tee — Orchid', collection: 'signature',
    sources: [
      'signature/IMG_0553.JPG',
      'signature/Signature T \u201cOrchard\u201d.jpeg',
    ]
  },
  {
    productId: 'sg-004', name: 'The Signature Tee — White', collection: 'signature',
    sources: [
      'signature/IMG_0554.JPG',
      'signature/Signature T \u201cWhite\u201d.jpeg',
    ]
  },
  {
    productId: 'sg-005', name: 'Stay Golden Tee', collection: 'signature',
    sources: [
      'signature/Photo Dec 18 2023, 6 09 21 PM.jpg',
    ]
  },
  {
    productId: 'sg-006', name: 'Mint & Lavender Hoodie', collection: 'signature',
    sources: [
      'signature/PhotoRoom_004_20231221_160237.jpeg',
      'signature/Mint & Lavender Set (Sold Separately) .jpeg',
      'signature/MINT & Lavender Set 2 .jpeg',
    ]
  },
  {
    productId: 'sg-007', name: 'The Signature Beanie — Red', collection: 'signature',
    sources: [
      'signature/Photoroom_010_20240926_104051.jpg',
    ]
  },
  {
    productId: 'sg-008', name: 'The Signature Beanie', collection: 'signature',
    sources: [
      'signature/PhotoRoom_000_20221210_093149.png',
    ]
  },
  {
    productId: 'sg-009', name: 'The Sherpa Jacket', collection: 'signature',
    sources: [
      'signature/PhotoRoom_002_20231221_072338.jpg',
      'signature/PhotoRoom_003_20231221_072338.jpg',
    ]
  },
];

// ── Enhancement presets ───────────────────────────────────────────────────
const PRESETS = {
  product: {
    maxSize: 2400,
    quality: 92,
    brightness: 1.05,
    saturation: 1.2,
    sharpenSigma: 1.5,
  },
  promo: {
    maxSize: 3000,
    quality: 94,
    brightness: 1.03,
    saturation: 1.15,
    sharpenSigma: 1.2,
  },
  logo: {
    maxSize: 2000,
    quality: 95,
    brightness: 1.0,
    saturation: 1.0,
    sharpenSigma: 0.8,
  },
};

async function enhancePhoto(sourcePath, outputPath, preset = 'product') {
  const s = PRESETS[preset];
  const img = sharp(sourcePath, { failOn: 'none' });
  const meta = await img.metadata();

  const longEdge = Math.max(meta.width || 1, meta.height || 1);
  const scale = longEdge > s.maxSize ? s.maxSize / longEdge : 1;
  const w = Math.round((meta.width || 1000) * scale);
  const h = Math.round((meta.height || 1000) * scale);

  let pipeline = img
    .resize(w, h, { kernel: sharp.kernel.lanczos3 })
    .modulate({ brightness: s.brightness, saturation: s.saturation })
    .sharpen({ sigma: s.sharpenSigma, m1: 0.6, m2: 0.6 });

  const ext = path.extname(outputPath).toLowerCase();
  if (ext === '.png') {
    await pipeline.png({ compressionLevel: 8 }).toFile(outputPath);
  } else {
    await pipeline.jpeg({ quality: s.quality, progressive: true, mozjpeg: true }).toFile(outputPath);
  }

  const stats = await fs.stat(outputPath);
  return { w, h, size: stats.size };
}

async function processFolder(sourceFolder, outputFolder, preset, label) {
  console.log(`\n${label}`);
  const files = await fs.readdir(sourceFolder).catch(() => []);
  let processed = 0, failed = 0;

  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    if (!['.jpg', '.jpeg', '.png', '.webp'].includes(ext)) continue;
    const sourcePath = path.join(sourceFolder, file);
    const outExt = ext === '.png' ? '.png' : '.jpg';
    const outputPath = path.join(outputFolder, path.basename(file, ext) + outExt);

    try {
      const srcStat = await fs.stat(sourcePath);
      const result = await enhancePhoto(sourcePath, outputPath, preset);
      const savings = srcStat.size - result.size;
      const pct = ((savings / srcStat.size) * 100).toFixed(0);
      console.log(`  ✅ ${file} → ${result.w}×${result.h} | ${(result.size/1024).toFixed(0)}KB (${pct > 0 ? '-'+pct : '+'+Math.abs(pct)}%)`);
      processed++;
    } catch (err) {
      console.log(`  ❌ ${file} — ${err.message}`);
      failed++;
    }
  }
  return { processed, failed };
}

async function main() {
  console.log('\n SkyyRose — Photo Enhancement & Optimization');
  console.log('='.repeat(60));

  let total = 0, totalFailed = 0;

  // ── 1. Products ──────────────────────────────────────────────────────────
  console.log('\n[ PRODUCTS ]');
  for (const product of PRODUCT_PHOTOS) {
    const outDir = path.join(OUTPUT_DIR, product.productId);
    await fs.mkdir(outDir, { recursive: true });
    console.log(`\n  ${product.productId} — ${product.name}`);

    for (let i = 0; i < product.sources.length; i++) {
      const srcPath = path.join(SOURCE_DIR, product.sources[i]);
      const suffix = i === 0 ? 'product' : `product-${i + 1}`;
      const outPath = path.join(outDir, `${product.productId}-${suffix}.jpg`);

      try {
        await fs.access(srcPath);
        const srcStat = await fs.stat(srcPath);
        const result = await enhancePhoto(srcPath, outPath, 'product');
        const savings = srcStat.size - result.size;
        const pct = ((savings / srcStat.size) * 100).toFixed(0);
        console.log(`    ✅ ${path.basename(product.sources[i])} → ${result.w}×${result.h} | ${(result.size/1024).toFixed(0)}KB (${pct > 0 ? '-'+pct : '+'+Math.abs(pct)}%)`);
        total++;
      } catch (err) {
        if (err.code === 'ENOENT') {
          console.log(`    ⚠️  Not found: ${path.basename(product.sources[i])}`);
        } else {
          console.log(`    ❌ ${path.basename(product.sources[i])} — ${err.message}`);
          totalFailed++;
        }
      }
    }
  }

  // ── 2. Promos ────────────────────────────────────────────────────────────
  const promosOut = path.join(OUTPUT_DIR, '_promos');
  await fs.mkdir(promosOut, { recursive: true });
  const promoResult = await processFolder(
    path.join(SOURCE_DIR, 'promos'), promosOut, 'promo',
    '[ PROMOS / ADS / WEB COPY ]'
  );
  total += promoResult.processed;
  totalFailed += promoResult.failed;

  // ── 3. Logos ─────────────────────────────────────────────────────────────
  const logosOut = path.join(OUTPUT_DIR, '_logos');
  await fs.mkdir(logosOut, { recursive: true });
  const logoResult = await processFolder(
    path.join(SOURCE_DIR, 'logos'), logosOut, 'logo',
    '[ LOGOS ]'
  );
  total += logoResult.processed;
  totalFailed += logoResult.failed;

  console.log('\n' + '='.repeat(60));
  console.log(` Done — ${total} enhanced, ${totalFailed} failed`);
  console.log(` Output: ${path.relative(process.cwd(), OUTPUT_DIR)}/\n`);
}

if (require.main === module) {
  main().catch(err => { console.error('\nFatal:', err); process.exit(1); });
}

module.exports = { PRODUCT_PHOTOS, enhancePhoto };
