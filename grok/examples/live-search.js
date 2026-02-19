/**
 * Live search — Grok's signature feature
 * Real-time web + X/Twitter grounding via search_parameters
 */
const { GrokClient } = require('../clients/node/grok-client');

async function main() {
  const client = new GrokClient();

  console.log('\n🌐 Grok Live Search\n');

  // Web + X search (default)
  console.log('── Web + X Search ─────────────────────────');
  const webRes = await client.liveSearch({
    query: 'What are the latest trends in luxury gothic streetwear fashion?',
    model: 'grok-3',
    sources: [{ type: 'web' }, { type: 'x' }]
  });
  console.log(webRes.text);
  if (webRes.citations?.length) {
    console.log('\nCitations:');
    webRes.citations.forEach((c, i) => console.log(`  [${i + 1}] ${c.url || c}`));
  }

  console.log('\n── X/Twitter Only ─────────────────────────');
  const xRes = await client.liveSearch({
    query: 'SkyyRose fashion brand',
    model: 'grok-3',
    sources: [{ type: 'x' }],
    systemPrompt: 'You have access to real-time X/Twitter data. Summarize recent mentions.'
  });
  console.log(xRes.text);
}

main().catch(console.error);
