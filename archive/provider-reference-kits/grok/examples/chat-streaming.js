/**
 * Streaming chat completion with Grok
 */
const { GrokClient } = require('../clients/node/grok-client');

async function main() {
  const client = new GrokClient();

  console.log('\n🤖 Grok Streaming Response:\n');

  for await (const chunk of client.generateContentStream({
    prompt: 'Write a short poem about the Love Hurts collection.',
    systemPrompt: 'You are a luxury fashion poet for SkyyRose.',
    model: 'grok-3-mini'
  })) {
    if (!chunk.done) process.stdout.write(chunk.text);
  }

  console.log('\n');
}

main().catch(console.error);
