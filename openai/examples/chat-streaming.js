/**
 * Streaming chat completion example
 */
const { OpenAIClient } = require('../clients/node/openai-client');

async function main() {
  const client = new OpenAIClient();

  console.log('\n🌹 Streaming Response:\n');

  for await (const chunk of client.generateContentStream({
    prompt: 'Write a short poem about the Love Hurts collection.',
    systemPrompt: 'You are a luxury fashion poet for SkyyRose.',
    model: 'gpt-4o-mini'
  })) {
    if (!chunk.done) process.stdout.write(chunk.text);
  }

  console.log('\n');
}

main().catch(console.error);
