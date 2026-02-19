/**
 * Vision analysis with Grok 2 Vision
 * Supports local files (base64) or URLs
 */
const { GrokClient } = require('../clients/node/grok-client');
const path = require('path');

async function main() {
  const client = new GrokClient();

  console.log('\n👁 Grok Vision Analysis\n');

  // Analyze a product image from SkyyRose
  const imagePath = path.join(
    __dirname,
    '../../../skyyrose/assets/images/products/br-001/br-001.jpg'
  );

  try {
    const res = await client.analyzeImage({
      imagePath,
      prompt: 'Describe this luxury fashion product in detail. Include style, materials, and target audience.',
      model: 'grok-2-vision-1212'
    });

    console.log('Product Analysis:\n');
    console.log(res.text);
    console.log('\nTokens used:', res.usage?.total_tokens);
  } catch (e) {
    // Fallback to URL if local file not found
    console.log('Local file not found, using URL example...\n');
    const res = await client.analyzeImage({
      imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/240px-PNG_transparency_demonstration_1.png',
      prompt: 'What do you see in this image?',
      model: 'grok-2-vision-1212'
    });
    console.log(res.text);
  }
}

main().catch(console.error);
