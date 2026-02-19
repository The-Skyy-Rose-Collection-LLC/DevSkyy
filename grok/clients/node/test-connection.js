const { GrokClient } = require('./grok-client');

async function main() {
  console.log('\n🔌 Grok (xAI) Connection Test\n');
  const client = new GrokClient();
  let passed = 0, failed = 0;

  async function test(name, fn) {
    try { await fn(); console.log(`  ✅ ${name}`); passed++; }
    catch (e) { console.log(`  ❌ ${name}: ${e.message || JSON.stringify(e)}`); failed++; }
  }

  await test('Chat (grok-3-mini)', async () => {
    const res = await client.generateContent({
      prompt: 'Say "Grok connected" — nothing else.',
      model: 'grok-3-mini', max_tokens: 10
    });
    if (!res.text.toLowerCase().includes('grok') && !res.text.toLowerCase().includes('connected'))
      throw new Error(`Got: ${res.text}`);
  });

  await test('Streaming (grok-3-mini)', async () => {
    let text = '';
    for await (const chunk of client.generateContentStream({
      prompt: 'Count to 3.', model: 'grok-3-mini', max_tokens: 20
    })) { text += chunk.text; }
    if (!text) throw new Error('No output');
  });

  console.log(`\n  ${passed} passed · ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
