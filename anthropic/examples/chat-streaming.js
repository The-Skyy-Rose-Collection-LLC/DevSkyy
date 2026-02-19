/**
 * Streaming chat completion with Claude
 */
const { AnthropicClient } = require('../clients/node/anthropic-client');

async function main() {
  const client = new AnthropicClient();

  console.log('\n🤖 Claude Streaming Response:\n');

  for await (const chunk of client.generateContentStream({
    prompt: 'Write a short poem about the Love Hurts collection.',
    systemPrompt: 'You are a luxury fashion poet for SkyyRose.',
    model: 'claude-sonnet-4-5-20250929'
  })) {
    if (!chunk.done) process.stdout.write(chunk.text);
  }

  console.log('\n');
}

main().catch(console.error);
