/**
 * SkyyRose - Production-Quality Scene Optimization
 * drakerelated.com-level performance and quality
 *
 * Goals:
 * - Ultra-high quality while maintaining fast load times
 * - Progressive enhancement (blur-up placeholder → full quality)
 * - WebP with AVIF fallback for cutting-edge browsers
 * - Responsive images for all device sizes
 * - Preload hints for critical scenes
 */

const path = require('path');
const fs = require('fs').promises;
const sharp = require('sharp');

const CONFIG = {
  sourceDir: 'assets/images/scenes/source',
  outputDir: 'assets/images/scenes',

  // Production-quality image settings
  quality: {
    webp: {
      quality: 92,           // High quality for luxury brand
      effort: 6,             // Max compression effort
      alphaQuality: 100
    },
    jpeg: {
      quality: 90,           // Premium JPEG quality
      progressive: true,     // Progressive loading
      mozjpeg: true,         // Better compression
      chromaSubsampling: '4:4:4'  // No color downsampling
    },
    avif: {
      quality: 85,           // AVIF for modern browsers
      effort: 6,
      chromaSubsampling: '4:4:4'
    }
  },

  // Responsive breakpoints (mobile-first)
  sizes: {
    mobile: { width: 768, suffix: '-mobile' },      // Phone portrait
    tablet: { width: 1024, suffix: '-tablet' },     // iPad/tablet
    desktop: { width: 1920, suffix: '-desktop' },   // Standard desktop
    '4k': { width: 3840, suffix: '-4k' },           // 4K displays
    placeholder: { width: 32, suffix: '-placeholder', blur: 10 }  // Blur-up
  },

  scenes: [
    // SIGNATURE Collection
    {
      source: 'signature-runway-light.png',
      name: 'signature-runway-light',
      collection: 'signature',
      primary: false
    },
    {
      source: 'signature-runway-dark.png',
      name: 'signature-runway-dark',
      collection: 'signature',
      primary: true  // Primary scene for this collection
    },

    // BLACK ROSE Collection
    {
      source: 'black-rose-garden-night.png',
      name: 'black-rose-garden',
      collection: 'black-rose',
      primary: true  // Primary scene
    },
    {
      source: 'black-rose-interior.png',
      name: 'black-rose-interior',
      collection: 'black-rose',
      primary: false
    },

    // LOVE HURTS Collection
    {
      source: 'love-hurts-ballroom-dramatic.png',
      name: 'love-hurts-ballroom',
      collection: 'love-hurts',
      primary: true  // Primary scene
    },
    {
      source: 'love-hurts-ballroom-romantic.png',
      name: 'love-hurts-romantic',
      collection: 'love-hurts',
      primary: false
    }
  ]
};

/**
 * Generate responsive image at specific width
 */
async function generateResponsiveImage(inputPath, outputPath, width, format, quality) {
  const image = sharp(inputPath);
  const metadata = await image.metadata();

  // Calculate proportional height
  const aspectRatio = metadata.height / metadata.width;
  const height = Math.round(width * aspectRatio);

  let pipeline = image.resize(width, height, {
    kernel: sharp.kernel.lanczos3,
    fit: 'cover',
    position: 'center'
  });

  // Apply format-specific optimizations
  switch (format) {
    case 'webp':
      pipeline = pipeline.webp({
        quality: quality.webp.quality,
        effort: quality.webp.effort,
        alphaQuality: quality.webp.alphaQuality
      });
      break;

    case 'avif':
      pipeline = pipeline.avif({
        quality: quality.avif.quality,
        effort: quality.avif.effort,
        chromaSubsampling: quality.avif.chromaSubsampling
      });
      break;

    case 'jpeg':
      pipeline = pipeline.jpeg({
        quality: quality.jpeg.quality,
        progressive: quality.jpeg.progressive,
        mozjpeg: quality.jpeg.mozjpeg,
        chromaSubsampling: quality.jpeg.chromaSubsampling
      });
      break;
  }

  await pipeline.toFile(outputPath);

  const stats = await fs.stat(outputPath);
  return {
    size: stats.size,
    width,
    height,
    format
  };
}

/**
 * Generate blur-up placeholder (tiny, blurred image for instant load)
 */
async function generatePlaceholder(inputPath, outputPath) {
  const image = sharp(inputPath);

  await image
    .resize(32, null, { fit: 'cover' })
    .blur(10)
    .jpeg({ quality: 50, progressive: false })
    .toFile(outputPath);

  const stats = await fs.stat(outputPath);
  const base64 = await fs.readFile(outputPath, 'base64');

  return {
    size: stats.size,
    base64: `data:image/jpeg;base64,${base64}`
  };
}

/**
 * Process a single scene through all responsive sizes and formats
 */
async function processScene(scene) {
  console.log(`\n🎬 Processing: ${scene.name}`);
  console.log('─'.repeat(70));

  const sourcePath = path.join(CONFIG.sourceDir, scene.source);

  // Check source exists
  try {
    await fs.access(sourcePath);
  } catch {
    console.log(`  ⚠️  Source not found: ${sourcePath}`);
    return;
  }

  const results = {
    name: scene.name,
    collection: scene.collection,
    primary: scene.primary,
    formats: {}
  };

  // Generate blur-up placeholder first (critical for performance)
  console.log('\n  📦 Generating blur-up placeholder...');
  const placeholderPath = path.join(CONFIG.outputDir, `${scene.name}-placeholder.jpg`);
  const placeholder = await generatePlaceholder(sourcePath, placeholderPath);
  results.placeholder = placeholder;
  console.log(`    ✓ ${(placeholder.size / 1024).toFixed(1)}KB (inline base64)`);

  // Process each responsive size
  for (const [sizeName, sizeConfig] of Object.entries(CONFIG.sizes)) {
    if (sizeName === 'placeholder') continue;

    console.log(`\n  📐 ${sizeName.toUpperCase()} (${sizeConfig.width}px):`);

    // Generate AVIF (best compression, modern browsers)
    const avifPath = path.join(CONFIG.outputDir, `${scene.name}${sizeConfig.suffix}.avif`);
    const avifResult = await generateResponsiveImage(
      sourcePath,
      avifPath,
      sizeConfig.width,
      'avif',
      CONFIG.quality
    );
    console.log(`    ✓ AVIF: ${(avifResult.size / 1024).toFixed(1)}KB`);

    // Generate WebP (great compression, wide support)
    const webpPath = path.join(CONFIG.outputDir, `${scene.name}${sizeConfig.suffix}.webp`);
    const webpResult = await generateResponsiveImage(
      sourcePath,
      webpPath,
      sizeConfig.width,
      'webp',
      CONFIG.quality
    );
    console.log(`    ✓ WebP: ${(webpResult.size / 1024).toFixed(1)}KB`);

    // Generate JPEG (universal fallback)
    const jpegPath = path.join(CONFIG.outputDir, `${scene.name}${sizeConfig.suffix}.jpg`);
    const jpegResult = await generateResponsiveImage(
      sourcePath,
      jpegPath,
      sizeConfig.width,
      'jpeg',
      CONFIG.quality
    );
    console.log(`    ✓ JPEG: ${(jpegResult.size / 1024).toFixed(1)}KB`);

    results.formats[sizeName] = {
      avif: { ...avifResult, path: avifPath },
      webp: { ...webpResult, path: webpPath },
      jpeg: { ...jpegResult, path: jpegPath }
    };
  }

  console.log(`\n  ✨ ${scene.name} complete!`);
  return results;
}

/**
 * Generate production-ready HTML picture element
 */
function generatePictureHTML(scene) {
  return `
<!-- ${scene.collection.toUpperCase()} - ${scene.name} -->
<picture class="scene-image">
  <!-- Preload hint for primary scene -->
  ${scene.primary ? `<link rel="preload" as="image" href="assets/images/scenes/${scene.name}-desktop.avif" type="image/avif">` : ''}

  <!-- Blur-up placeholder (instant load) -->
  <img
    src="${scene.placeholder.base64}"
    class="scene-placeholder"
    aria-hidden="true"
    alt=""
  />

  <!-- Progressive enhancement: AVIF → WebP → JPEG -->

  <!-- 4K displays -->
  <source
    media="(min-width: 2560px)"
    srcset="assets/images/scenes/${scene.name}-4k.avif"
    type="image/avif"
  />
  <source
    media="(min-width: 2560px)"
    srcset="assets/images/scenes/${scene.name}-4k.webp"
    type="image/webp"
  />

  <!-- Desktop -->
  <source
    media="(min-width: 1280px)"
    srcset="assets/images/scenes/${scene.name}-desktop.avif"
    type="image/avif"
  />
  <source
    media="(min-width: 1280px)"
    srcset="assets/images/scenes/${scene.name}-desktop.webp"
    type="image/webp"
  />

  <!-- Tablet -->
  <source
    media="(min-width: 768px)"
    srcset="assets/images/scenes/${scene.name}-tablet.avif"
    type="image/avif"
  />
  <source
    media="(min-width: 768px)"
    srcset="assets/images/scenes/${scene.name}-tablet.webp"
    type="image/webp"
  />

  <!-- Mobile (default) -->
  <source
    srcset="assets/images/scenes/${scene.name}-mobile.avif"
    type="image/avif"
  />
  <source
    srcset="assets/images/scenes/${scene.name}-mobile.webp"
    type="image/webp"
  />

  <!-- Fallback -->
  <img
    src="assets/images/scenes/${scene.name}-desktop.jpg"
    alt="${scene.collection} collection immersive scene"
    class="scene-main"
    loading="${scene.primary ? 'eager' : 'lazy'}"
    decoding="async"
  />
</picture>
`.trim();
}

/**
 * Generate performance manifest
 */
async function generateManifest(results) {
  const manifest = {
    generated: new Date().toISOString(),
    scenes: results.map(r => ({
      name: r.name,
      collection: r.collection,
      primary: r.primary,
      placeholder: r.placeholder.size,
      sizes: Object.entries(r.formats).map(([size, formats]) => ({
        size,
        avif: formats.avif.size,
        webp: formats.webp.size,
        jpeg: formats.jpeg.size,
        savings: Math.round((1 - formats.avif.size / formats.jpeg.size) * 100)
      }))
    })),
    totalSavings: results.reduce((acc, r) => {
      const savings = Object.values(r.formats).reduce((s, f) =>
        s + (f.jpeg.size - f.avif.size), 0
      );
      return acc + savings;
    }, 0)
  };

  await fs.writeFile(
    path.join(CONFIG.outputDir, 'manifest.json'),
    JSON.stringify(manifest, null, 2)
  );

  return manifest;
}

/**
 * Main execution
 */
async function optimizeProductionScenes() {
  console.log('\n🎬 SkyyRose Production Scene Optimization');
  console.log('🎯 Target: drakerelated.com-level performance\n');
  console.log('='.repeat(70));

  const startTime = Date.now();

  // Ensure directories exist
  await fs.mkdir(CONFIG.outputDir, { recursive: true });

  const results = [];

  // Process each scene
  for (const scene of CONFIG.scenes) {
    const result = await processScene(scene);
    if (result) results.push(result);
  }

  // Generate manifest
  console.log('\n📊 Generating performance manifest...');
  const manifest = await generateManifest(results);

  // Generate HTML snippets
  console.log('\n📝 Generating HTML snippets...');
  const htmlSnippets = results.map(r => generatePictureHTML(r)).join('\n\n');
  await fs.writeFile(
    path.join(CONFIG.outputDir, 'picture-elements.html'),
    htmlSnippets
  );

  const duration = ((Date.now() - startTime) / 1000).toFixed(1);

  console.log('\n' + '='.repeat(70));
  console.log('✨ Production optimization complete!');
  console.log('='.repeat(70));
  console.log(`\n⏱️  Duration: ${duration}s`);
  console.log(`💾 Total savings: ${(manifest.totalSavings / 1024 / 1024).toFixed(1)}MB`);
  console.log(`📦 Scenes processed: ${results.length}`);
  console.log(`🎯 Primary scenes: ${results.filter(r => r.primary).length}`);
  console.log(`\n📁 Output: ${CONFIG.outputDir}/`);
  console.log(`📄 Manifest: ${CONFIG.outputDir}/manifest.json`);
  console.log(`📝 HTML: ${CONFIG.outputDir}/picture-elements.html`);

  console.log('\n🚀 Performance Features:');
  console.log('  ✓ Blur-up placeholders (instant perceived load)');
  console.log('  ✓ AVIF format (60-70% smaller than JPEG)');
  console.log('  ✓ WebP fallback (50-60% smaller than JPEG)');
  console.log('  ✓ Responsive images (mobile-first)');
  console.log('  ✓ Progressive JPEG (fallback)');
  console.log('  ✓ Preload hints for primary scenes');
  console.log('  ✓ Lazy loading for non-critical scenes\n');
}

// Execute
if (require.main === module) {
  optimizeProductionScenes().catch(error => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = {
  optimizeProductionScenes,
  processScene,
  generatePictureHTML
};
