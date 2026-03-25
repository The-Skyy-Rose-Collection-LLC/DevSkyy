/**
 * Streaming chat example with Gemini
 */

const { GeminiClient } = require('../clients/node/gemini-client');

async function main() {
  console.log('🌊 Gemini Streaming Example\n');

  const client = new GeminiClient();

  console.log('Generating a creative story...\n');
  console.log('Story: ');

  const stream = client.generateContentStream({
    prompt: 'Write a short creative story about an AI assistant helping a developer. Keep it to 3 paragraphs.',
    temperature: 0.9
  });

  let totalText = '';
  for await (const chunk of stream) {
    if (!chunk.done) {
      process.stdout.write(chunk.text);
      totalText += chunk.text;
    } else {
      console.log('\n\n---');
      console.log('Tokens used:', chunk.usageMetadata.totalTokenCount);
      console.log('Total characters:', totalText.length);
    }
  }

  console.log('\n✅ Streaming completed!');
}

main().catch(console.error);
