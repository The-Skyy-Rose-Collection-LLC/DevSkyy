/**
 * Basic chat completion with Grok
 */
const { GrokClient } = require('../clients/node/grok-client');

async function main() {
  const client = new GrokClient();

  const res = await client.generateContent({
    prompt: 'Describe the SkyyRose brand in 2 sentences.',
    systemPrompt: 'You are a luxury fashion copywriter for SkyyRose.',
    model: 'grok-3-mini'
  });

  console.log('\n🤖 Grok Response:\n');
  console.log(res.text);
  console.log('\nTokens used:', res.usage?.total_tokens);
}

main().catch(console.error);
