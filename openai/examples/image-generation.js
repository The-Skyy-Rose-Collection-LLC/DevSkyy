/**
 * Image generation with gpt-image-1 / DALL·E
 */
const { OpenAIClient } = require('../clients/node/openai-client');
const fs = require('fs');
const path = require('path');

async function main() {
  const client = new OpenAIClient();

  console.log('\n🌹 Image Generation\n');

  const results = await client.generateImage({
    prompt: 'Luxury streetwear flat lay — black satin varsity jacket with red "Love Hurts" script, ' +
            'gothic rose interior lining, editorial product photography on dark marble surface',
    model: 'dall-e-3',
    size: '1024x1024',
    quality: 'hd',
    n: 1
  });

  for (const img of results) {
    if (img.url) {
      console.log('Generated image URL:', img.url);
    }
    if (img.b64) {
      const outPath = path.join(__dirname, 'generated-image.png');
      fs.writeFileSync(outPath, Buffer.from(img.b64, 'base64'));
      console.log('Saved to:', outPath);
    }
  }
}

main().catch(console.error);
