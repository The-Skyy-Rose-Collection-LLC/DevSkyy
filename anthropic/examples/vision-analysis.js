/**
 * Vision analysis with Claude (Sonnet/Opus support images)
 */
const { AnthropicClient } = require('../clients/node/anthropic-client');
const path = require('path');

async function main() {
  const client = new AnthropicClient();

  console.log('\n👁 Claude Vision Analysis\n');

  const imagePath = path.join(
    __dirname,
    '../../../skyyrose/assets/images/products/br-001/br-001.jpg'
  );

  try {
    const res = await client.analyzeImage({
      imagePath,
      prompt: 'Describe this luxury fashion product in detail. Include style, materials, and target audience.',
      model: 'claude-sonnet-4-5-20250929'
    });

    console.log('Product Analysis:\n');
    console.log(res.text);
    console.log('\nTokens used:', res.usage?.input_tokens + res.usage?.output_tokens);
  } catch (e) {
    console.log('Local file not found, using URL example...\n');
    const res = await client.analyzeImage({
      imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/240px-PNG_transparency_demonstration_1.png',
      prompt: 'What do you see in this image?',
      model: 'claude-sonnet-4-5-20250929'
    });
    console.log(res.text);
  }
}

main().catch(console.error);
