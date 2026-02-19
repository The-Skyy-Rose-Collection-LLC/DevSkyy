const { AnthropicClient } = require('./anthropic-client');

async function main() {
  const client = new AnthropicClient();
  console.log('\n🤖 Anthropic Claude — Available Models\n');

  console.log('── Configured Models ──────────────────────');
  for (const m of client.getAvailableModels()) {
    const rec = m.recommended ? ' ★' : '';
    console.log(`  ${m.id.padEnd(35)} ${m.type.padEnd(10)} ${m.description.slice(0, 50)}${rec}`);
  }

  console.log('\n── Recommended by Task ────────────────────');
  for (const [task, model] of Object.entries(client.modelConfigs.modelSelection)) {
    console.log(`  ${task.padEnd(20)} → ${model}`);
  }
}

main().catch(console.error);
