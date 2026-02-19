/**
 * List all available OpenAI models
 */
const { OpenAIClient } = require('./openai-client');

async function main() {
  const client = new OpenAIClient();
  console.log('\n🤖 OpenAI — Available Models\n');

  // From config
  const configured = client.getAvailableModels();
  console.log('── Configured Models ──────────────────────');
  for (const m of configured) {
    const rec = m.recommended ? ' ★' : '';
    console.log(`  ${m.id.padEnd(30)} ${m.type.padEnd(18)} ${m.description.slice(0, 50)}${rec}`);
  }

  // From API
  console.log('\n── Live API Models ────────────────────────');
  try {
    const live = await client.listModels();
    const sorted = live.sort((a, b) => a.id.localeCompare(b.id));
    for (const m of sorted) {
      console.log(`  ${m.id}`);
    }
  } catch (e) {
    console.log('  (API list requires valid OPENAI_API_KEY)');
  }

  console.log('\n── Recommended by Task ────────────────────');
  const sel = client.modelConfigs.modelSelection;
  for (const [task, model] of Object.entries(sel)) {
    console.log(`  ${task.padEnd(20)} → ${model}`);
  }
}

main().catch(console.error);
