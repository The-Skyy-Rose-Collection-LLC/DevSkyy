/**
 * Basic chat completion with Claude
 */
const { AnthropicClient } = require('../clients/node/anthropic-client');

async function main() {
  const client = new AnthropicClient();

  const res = await client.generateContent({
    prompt: 'Describe the SkyyRose brand in 2 sentences.',
    systemPrompt: 'You are a luxury fashion copywriter for SkyyRose.',
    model: 'claude-sonnet-4-5-20250929'
  });

  console.log('\n🤖 Claude Response:\n');
  console.log(res.text);
  console.log('\nTokens used:', res.usage?.input_tokens + res.usage?.output_tokens);
}

main().catch(console.error);
