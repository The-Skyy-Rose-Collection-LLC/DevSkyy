/**
 * Vision analysis example with Gemini
 * Requires an image file to analyze
 */

const { GeminiClient } = require('../clients/node/gemini-client');
const path = require('path');

async function main() {
  console.log('👁️  Gemini Vision Example\n');

  const client = new GeminiClient();

  // Check if image path is provided
  const imagePath = process.argv[2];

  if (!imagePath) {
    console.log('Usage: node vision-analysis.js <path-to-image>');
    console.log('\nExample:');
    console.log('  node vision-analysis.js ~/Pictures/photo.jpg');
    console.log('\nSupported formats: JPG, PNG, WEBP, HEIC, HEIF');
    return;
  }

  console.log('Analyzing image:', imagePath);
  console.log('---\n');

  try {
    // Describe the image
    console.log('Task: Describe this image\n');
    const description = await client.analyzeImage({
      imagePath,
      prompt: 'Describe this image in detail. What do you see?'
    });

    console.log('Description:', description.text);
    console.log('\n---\n');

    // Extract specific information
    console.log('Task: Extract text (if any)\n');
    const ocr = await client.analyzeImage({
      imagePath,
      prompt: 'Extract any text visible in this image. If there is no text, say "No text found".'
    });

    console.log('Text:', ocr.text);
    console.log('\n---\n');

    // Analyze composition
    console.log('Task: Analyze image composition\n');
    const composition = await client.analyzeImage({
      imagePath,
      prompt: 'Analyze the composition, colors, and style of this image.'
    });

    console.log('Analysis:', composition.text);

    console.log('\n✅ Vision analysis completed!');
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('\nMake sure the image path is correct and the file format is supported.');
  }
}

main().catch(console.error);
