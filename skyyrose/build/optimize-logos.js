/**
 * SkyyRose - Logo Optimization Pipeline
 * Enhances logos to 4K quality and generates web-optimized versions
 *
 * Process:
 * 1. Upscale to 4K resolution (3840x2160 or proportional)
 * 2. Generate multiple sizes for responsive usage
 * 3. Create WebP versions with transparency
 * 4. Maintain PNG fallbacks with alpha channel
 * 5. Optimize for web delivery
 */

const path = require('path');
const fs = require('fs').promises;
const sharp = require('sharp');

// Configuration
const CONFIG = {
  sourceDir: 'assets/images/logos/source',
  outputDir: 'assets/images/logos',

  // Logo sizes for different contexts
  sizes: {
    '4k': { width: 3840, suffix: '-4k' },        // Ultra-high resolution
    'hero': { width: 2400, suffix: '-hero' },    // Homepage hero section
    'nav': { width: 400, suffix: '-nav' },       // Navigation bar
    'icon': { width: 200, suffix: '-icon' },     // Small icons/favicons
    'og': { width: 1200, suffix: '-og' }         // Open Graph social sharing
  },

  // Logos to process (add your actual logo filenames here)
  logos: [
    {
      source: 'sr-primary-logo.png',          // Main SkyyRose logo
      name: 'skyyrose-logo',
      type: 'primary'
    },
    {
      source: 'black-rose-logo.png',          // BLACK ROSE collection
      name: 'black-rose-logo',
      type: 'collection'
    },
    {
      source: 'love-hurts-logo.png',          // LOVE HURTS collection
      name: 'love-hurts-logo',
      type: 'collection'
    },
    {
      source: 'signature-logo.png',           // SIGNATURE collection
      name: 'signature-logo',
      type: 'collection'
    },
    {
      source: 'rose-icon.png',                // Standalone rose icon
      name: 'rose-icon',
      type: 'icon'
    }
  ],

  // Optimization settings
  webp: {
    quality: 90,
    alphaQuality: 100,
    lossless: false
  },
  png: {
    quality: 95,
    compressionLevel: 9,
    adaptiveFiltering: true
  }
};

/**
 * Enhance and upscale logo to 4K quality
 */
async function enhance4K(inputPath, outputPath, targetWidth) {
  console.log(`  🔬 Enhancing to ${targetWidth}px width...`);

  try {
    const image = sharp(inputPath);
    const metadata = await image.metadata();

    // Calculate proportional height
    const aspectRatio = metadata.height / metadata.width;
    const targetHeight = Math.round(targetWidth * aspectRatio);

    // Upscale with high-quality algorithm
    await image
      .resize(targetWidth, targetHeight, {
        kernel: sharp.kernel.lanczos3,  // Best quality for upscaling
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .sharpen()  // Enhance edges after upscaling
      .png({
        quality: CONFIG.png.quality,
        compressionLevel: CONFIG.png.compressionLevel,
        adaptiveFiltering: CONFIG.png.adaptiveFiltering
      })
      .toFile(outputPath);

    const stats = await fs.stat(outputPath);
    console.log(`  ✓ Enhanced: ${(stats.size / 1024).toFixed(1)}KB`);

    return outputPath;
  } catch (error) {
    console.error(`  ✗ Error enhancing: ${error.message}`);
    return null;
  }
}

/**
 * Generate WebP version with transparency
 */
async function generateWebP(pngPath, webpPath) {
  try {
    await sharp(pngPath)
      .webp({
        quality: CONFIG.webp.quality,
        alphaQuality: CONFIG.webp.alphaQuality,
        lossless: CONFIG.webp.lossless
      })
      .toFile(webpPath);

    const stats = await fs.stat(webpPath);
    console.log(`  ✓ WebP: ${(stats.size / 1024).toFixed(1)}KB`);

    return webpPath;
  } catch (error) {
    console.error(`  ✗ Error generating WebP: ${error.message}`);
    return null;
  }
}

/**
 * Process a single logo through all sizes
 */
async function processLogo(logo) {
  console.log(`\n📸 Processing: ${logo.name}`);
  console.log('─'.repeat(60));

  const sourcePath = path.join(CONFIG.sourceDir, logo.source);

  // Check if source exists
  try {
    await fs.access(sourcePath);
  } catch {
    console.log(`  ⚠️  Source not found: ${sourcePath}`);
    console.log(`  ℹ️  Please add ${logo.source} to ${CONFIG.sourceDir}/`);
    return;
  }

  // Ensure output directory exists
  await fs.mkdir(CONFIG.outputDir, { recursive: true });

  // Process each size variant
  for (const [sizeName, sizeConfig] of Object.entries(CONFIG.sizes)) {
    console.log(`\n  ${sizeName.toUpperCase()} (${sizeConfig.width}px):`);

    const pngFilename = `${logo.name}${sizeConfig.suffix}.png`;
    const webpFilename = `${logo.name}${sizeConfig.suffix}.webp`;

    const pngPath = path.join(CONFIG.outputDir, pngFilename);
    const webpPath = path.join(CONFIG.outputDir, webpFilename);

    // Generate enhanced PNG
    await enhance4K(sourcePath, pngPath, sizeConfig.width);

    // Generate WebP version
    if (fs.access(pngPath)) {
      await generateWebP(pngPath, webpPath);
    }
  }

  console.log(`\n✓ ${logo.name} complete!`);
}

/**
 * Generate favicon set from primary logo
 */
async function generateFavicons() {
  console.log('\n🌟 Generating favicons...');
  console.log('─'.repeat(60));

  const primaryLogo = CONFIG.logos.find(l => l.type === 'primary');
  if (!primaryLogo) {
    console.log('⚠️  No primary logo found');
    return;
  }

  const sourcePath = path.join(CONFIG.sourceDir, primaryLogo.source);

  try {
    await fs.access(sourcePath);
  } catch {
    console.log(`⚠️  Primary logo source not found`);
    return;
  }

  const faviconSizes = [16, 32, 48, 64, 128, 192, 256, 512];
  const faviconDir = path.join(CONFIG.outputDir, 'favicons');
  await fs.mkdir(faviconDir, { recursive: true });

  for (const size of faviconSizes) {
    const filename = `favicon-${size}x${size}.png`;
    const outputPath = path.join(faviconDir, filename);

    await sharp(sourcePath)
      .resize(size, size, {
        kernel: sharp.kernel.lanczos3,
        fit: 'contain',
        background: { r: 0, g: 0, b: 0, alpha: 0 }
      })
      .png({ quality: 100 })
      .toFile(outputPath);

    const stats = await fs.stat(outputPath);
    console.log(`  ✓ ${size}x${size}: ${(stats.size / 1024).toFixed(1)}KB`);
  }

  // Generate favicon.ico (multi-resolution)
  const icoPath = path.join('public', 'favicon.ico');
  await fs.mkdir('public', { recursive: true });

  await sharp(sourcePath)
    .resize(32, 32)
    .toFile(icoPath);

  console.log(`\n✓ Favicons generated in ${faviconDir}/`);
}

/**
 * Generate HTML snippets for logo usage
 */
async function generateUsageGuide() {
  console.log('\n📚 Generating usage guide...');

  const guide = `
<!-- SkyyRose Logo Usage Guide -->

<!-- PRIMARY LOGO (Navigation) -->
<picture>
  <source srcset="assets/images/logos/skyyrose-logo-nav.webp" type="image/webp">
  <img src="assets/images/logos/skyyrose-logo-nav.png" alt="SkyyRose Luxury Fashion" width="200" height="auto">
</picture>

<!-- HERO LOGO (Homepage) -->
<picture>
  <source srcset="assets/images/logos/skyyrose-logo-hero.webp" type="image/webp">
  <img src="assets/images/logos/skyyrose-logo-hero.png" alt="SkyyRose" width="400" height="auto">
</picture>

<!-- COLLECTION LOGOS (Collection Pages) -->
<picture>
  <source srcset="assets/images/logos/black-rose-logo-hero.webp" type="image/webp">
  <img src="assets/images/logos/black-rose-logo-hero.png" alt="BLACK ROSE Collection" width="300" height="auto">
</picture>

<!-- FAVICON (Head) -->
<link rel="icon" type="image/png" sizes="32x32" href="assets/images/logos/favicons/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/images/logos/favicons/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="192x192" href="assets/images/logos/favicons/favicon-192x192.png">

<!-- OPEN GRAPH (Social Sharing) -->
<meta property="og:image" content="assets/images/logos/skyyrose-logo-og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
`;

  await fs.writeFile('assets/images/logos/USAGE.html', guide);
  console.log('✓ Usage guide saved to assets/images/logos/USAGE.html');
}

/**
 * Main execution
 */
async function optimizeAllLogos() {
  console.log('\n🌹 SkyyRose Logo Optimization Pipeline\n');
  console.log('='.repeat(60));
  console.log('Enhancing logos to 4K quality for luxury web experience');
  console.log('='.repeat(60));

  // Create output directories
  await fs.mkdir(CONFIG.sourceDir, { recursive: true });
  await fs.mkdir(CONFIG.outputDir, { recursive: true });

  console.log(`\nSource: ${CONFIG.sourceDir}/`);
  console.log(`Output: ${CONFIG.outputDir}/\n`);

  // Process each logo
  for (const logo of CONFIG.logos) {
    await processLogo(logo);
  }

  // Generate favicons
  await generateFavicons();

  // Generate usage guide
  await generateUsageGuide();

  console.log('\n' + '='.repeat(60));
  console.log('✨ Logo optimization complete!');
  console.log('='.repeat(60));
  console.log('\nGenerated sizes:');
  console.log('  - 4K (3840px): Ultra-high resolution displays');
  console.log('  - Hero (2400px): Homepage hero sections');
  console.log('  - Nav (400px): Navigation bars');
  console.log('  - Icon (200px): Small UI elements');
  console.log('  - OG (1200px): Social media sharing');
  console.log('\nNext steps:');
  console.log('1. Add source logos to assets/images/logos/source/');
  console.log('2. Run: npm run build:logos');
  console.log('3. Update HTML with optimized logo paths');
  console.log('4. Test responsive logo loading\n');
}

// Main execution
if (require.main === module) {
  optimizeAllLogos().catch(error => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = {
  optimizeAllLogos,
  processLogo,
  generateFavicons
};
