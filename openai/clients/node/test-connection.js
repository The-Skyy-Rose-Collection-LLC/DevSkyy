/**
 * Test OpenAI API connection + core capabilities
 */
const { OpenAIClient } = require('./openai-client');

async function main() {
  console.log('\n🔌 OpenAI Connection Test\n');

  const client = new OpenAIClient();
  let passed = 0, failed = 0;

  async function test(name, fn) {
    try {
      await fn();
      console.log(`  ✅ ${name}`);
      passed++;
    } catch (e) {
      console.log(`  ❌ ${name}: ${e.message || JSON.stringify(e)}`);
      failed++;
    }
  }

  await test('Chat completion (gpt-4o-mini)', async () => {
    const res = await client.generateContent({
      prompt: 'Say "OpenAI connected" — nothing else.',
      model: 'gpt-4o-mini',
      max_tokens: 10
    });
    if (!res.text.toLowerCase().includes('openai')) throw new Error(`Got: ${res.text}`);
  });

  await test('Streaming (gpt-4o-mini)', async () => {
    let text = '';
    for await (const chunk of client.generateContentStream({
      prompt: 'Count to 3.', model: 'gpt-4o-mini', max_tokens: 20
    })) {
      text += chunk.text;
    }
    if (!text) throw new Error('No streaming output');
  });

  await test('Embeddings (text-embedding-3-small)', async () => {
    const emb = await client.embedContent('SkyyRose luxury fashion');
    if (!Array.isArray(emb) || emb.length < 100) throw new Error('Bad embedding');
  });

  console.log(`\n  ${passed} passed · ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
