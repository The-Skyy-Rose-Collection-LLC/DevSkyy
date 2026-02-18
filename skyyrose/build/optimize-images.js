/**
 * SkyyRose - Image Optimization Pipeline
 * Converts source images to WebP and JPEG formats with mobile versions
 * Target: 48% file size reduction (350KB → 180KB per image)
 */

const sharp = require('sharp');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
  quality: {
    webp: 85,
    jpeg: 85
  },
  mobileScale: 0.5, // 50% size for mobile
  scenes: [
    {
      id: 'black-rose',
      source: 'assets/images/scenes/source/black-rose-source.jpg',
      outputs: {
        desktop: {
          webp: 'assets/images/scenes/black-rose.webp',
          jpeg: 'assets/images/scenes/black-rose.jpg'
        },
        mobile: {
          webp: 'assets/images/scenes/black-rose-mobile.webp',
          jpeg: 'assets/images/scenes/black-rose-mobile.jpg'
        }
      }
    },
    {
      id: 'love-hurts',
      source: 'assets/images/scenes/source/love-hurts-source.jpg',
      outputs: {
        desktop: {
          webp: 'assets/images/scenes/love-hurts.webp',
          jpeg: 'assets/images/scenes/love-hurts.jpg'
        },
        mobile: {
          webp: 'assets/images/scenes/love-hurts-mobile.webp',
          jpeg: 'assets/images/scenes/love-hurts-mobile.jpg'
        }
      }
    },
    {
      id: 'signature',
      source: 'assets/images/scenes/source/signature-source.jpg',
      outputs: {
        desktop: {
          webp: 'assets/images/scenes/signature.webp',
          jpeg: 'assets/images/scenes/signature.jpg'
        },
        mobile: {
          webp: 'assets/images/scenes/signature-mobile.webp',
          jpeg: 'assets/images/scenes/signature-mobile.jpg'
        }
      }
    }
  ]
};

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get file size
 */
async function getFileSize(filepath) {
  try {
    const stats = await fs.stat(filepath);
    return stats.size;
  } catch (error) {
    return 0;
  }
}

/**
 * Optimize a single image
 */
async function optimizeImage(sourcePath, outputPath, options = {}) {
  const { format = 'jpeg', quality = 85, resize = null } = options;

  console.log(`  Processing: ${path.basename(outputPath)}`);

  try {
    let pipeline = sharp(sourcePath);

    // Resize if specified
    if (resize) {
      const metadata = await pipeline.metadata();
      const newWidth = Math.round(metadata.width * resize);
      const newHeight = Math.round(metadata.height * resize);
      pipeline = pipeline.resize(newWidth, newHeight, {
        fit: 'cover',
        position: 'center'
      });
    }

    // Format-specific options
    if (format === 'webp') {
      pipeline = pipeline.webp({
        quality,
        effort: 6 // Higher effort = better compression (0-6)
      });
    } else if (format === 'jpeg') {
      pipeline = pipeline.jpeg({
        quality,
        progressive: true,
        mozjpeg: true // Better compression
      });
    }

    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    await fs.mkdir(outputDir, { recursive: true });

    // Save
    await pipeline.toFile(outputPath);

    // Get size
    const size = await getFileSize(outputPath);
    console.log(`    ✓ Saved: ${formatBytes(size)}`);

    return size;
  } catch (error) {
    console.error(`    ✗ Error: ${error.message}`);
    throw error;
  }
}

/**
 * Process all scene images
 */
async function processAllImages() {
  console.log('🌹 SkyyRose Image Optimization Pipeline\n');

  let totalSourceSize = 0;
  let totalOutputSize = 0;

  for (const scene of CONFIG.scenes) {
    console.log(`\n📸 Processing: ${scene.id.toUpperCase()}`);

    try {
      // Check if source exists
      const sourceExists = await fs.access(scene.source)
        .then(() => true)
        .catch(() => false);

      if (!sourceExists) {
        console.log(`  ⚠️  Source image not found: ${scene.source}`);
        console.log(`  ℹ️  Please add source images to assets/images/scenes/source/`);
        continue;
      }

      const sourceSize = await getFileSize(scene.source);
      totalSourceSize += sourceSize;
      console.log(`  Source: ${formatBytes(sourceSize)}`);

      // Desktop WebP
      console.log('\n  Desktop versions:');
      const desktopWebpSize = await optimizeImage(scene.source, scene.outputs.desktop.webp, {
        format: 'webp',
        quality: CONFIG.quality.webp
      });
      totalOutputSize += desktopWebpSize;

      // Desktop JPEG
      const desktopJpegSize = await optimizeImage(scene.source, scene.outputs.desktop.jpeg, {
        format: 'jpeg',
        quality: CONFIG.quality.jpeg
      });
      totalOutputSize += desktopJpegSize;

      // Mobile WebP
      console.log('\n  Mobile versions (50% scale):');
      const mobileWebpSize = await optimizeImage(scene.source, scene.outputs.mobile.webp, {
        format: 'webp',
        quality: CONFIG.quality.webp,
        resize: CONFIG.mobileScale
      });
      totalOutputSize += mobileWebpSize;

      // Mobile JPEG
      const mobileJpegSize = await optimizeImage(scene.source, scene.outputs.mobile.jpeg, {
        format: 'jpeg',
        quality: CONFIG.quality.jpeg,
        resize: CONFIG.mobileScale
      });
      totalOutputSize += mobileJpegSize;

      const reduction = ((sourceSize - desktopWebpSize) / sourceSize * 100).toFixed(1);
      console.log(`\n  Desktop WebP reduction: ${reduction}% (${formatBytes(sourceSize)} → ${formatBytes(desktopWebpSize)})`);

    } catch (error) {
      console.error(`  ✗ Failed to process ${scene.id}: ${error.message}`);
    }
  }

  // Summary
  if (totalSourceSize > 0) {
    console.log('\n' + '='.repeat(60));
    console.log('📊 OPTIMIZATION SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total source size:  ${formatBytes(totalSourceSize)}`);
    console.log(`Total output size:  ${formatBytes(totalOutputSize)}`);
    console.log(`Space saved:        ${formatBytes(totalSourceSize - totalOutputSize)}`);
    console.log(`Reduction:          ${((totalSourceSize - totalOutputSize) / totalSourceSize * 100).toFixed(1)}%`);
    console.log('='.repeat(60));
    console.log('\n✨ Optimization complete!\n');
  } else {
    console.log('\n⚠️  No source images found to process.');
    console.log('ℹ️  Please add high-quality scene images to:');
    console.log('    assets/images/scenes/source/black-rose-source.jpg');
    console.log('    assets/images/scenes/source/love-hurts-source.jpg');
    console.log('    assets/images/scenes/source/signature-source.jpg\n');
  }
}

/**
 * Create directory structure
 */
async function createDirectories() {
  const dirs = [
    'assets/images/scenes',
    'assets/images/scenes/source',
    'assets/images/products'
  ];

  for (const dir of dirs) {
    await fs.mkdir(dir, { recursive: true });
  }
}

// Main execution
(async function main() {
  try {
    await createDirectories();
    await processAllImages();
  } catch (error) {
    console.error('\n❌ Build failed:', error.message);
    process.exit(1);
  }
})();
