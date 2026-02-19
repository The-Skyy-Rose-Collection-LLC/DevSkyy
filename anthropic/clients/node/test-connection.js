const { AnthropicClient } = require('./anthropic-client');

async function main() {
  console.log('\n🔌 Anthropic Claude Connection Test\n');
  const client = new AnthropicClient();
  let passed = 0, failed = 0;

  async function test(name, fn) {
    try { await fn(); console.log(`  ✅ ${name}`); passed++; }
    catch (e) { console.log(`  ❌ ${name}: ${e.message || JSON.stringify(e)}`); failed++; }
  }

  await test('Chat (claude-haiku-4-5)', async () => {
    const res = await client.generateContent({
      prompt: 'Say "Claude connected" — nothing else.',
      model: 'claude-haiku-4-5',
      max_tokens: 10
    });
    if (!res.text.toLowerCase().includes('claude') && !res.text.toLowerCase().includes('connected'))
      throw new Error(`Got: ${res.text}`);
  });

  await test('Streaming (claude-sonnet-4-6)', async () => {
    let text = '';
    for await (const chunk of client.generateContentStream({
      prompt: 'Count to 3.',
      model: 'claude-sonnet-4-6',
      max_tokens: 20
    })) { text += chunk.text; }
    if (!text) throw new Error('No output');
  });

  console.log(`\n  ${passed} passed · ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
