/**
 * Basic chat completion example
 */
const { OpenAIClient } = require('../clients/node/openai-client');

async function main() {
  const client = new OpenAIClient();

  const res = await client.generateContent({
    prompt: 'Describe the SkyyRose brand in 2 sentences.',
    systemPrompt: 'You are a luxury fashion copywriter for SkyyRose.',
    model: 'gpt-4o-mini'
  });

  console.log('\n🌹 Chat Response:\n');
  console.log(res.text);
  console.log('\nTokens used:', res.usage?.total_tokens);
}

main().catch(console.error);
