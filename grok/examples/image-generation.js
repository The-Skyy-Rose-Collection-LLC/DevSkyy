/**
 * Image generation with Aurora (xAI's image model)
 */
const { GrokClient } = require('../clients/node/grok-client');
const fs = require('fs');
const path = require('path');

async function main() {
  const client = new GrokClient();

  console.log('\n🎨 Aurora Image Generation\n');

  const results = await client.generateImage({
    prompt: 'Luxury streetwear flat lay — black satin varsity jacket with red "Love Hurts" script, ' +
            'gothic rose interior lining, editorial product photography on dark marble surface',
    model: 'aurora',
    n: 1,
    responseFormat: 'b64_json'
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
