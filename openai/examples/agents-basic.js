/**
 * OpenAI Agents SDK — Basic Example
 * Uses @openai/agents for multi-agent orchestration
 */
const { Agent, run, tool } = require('@openai/agents');
const { z } = require('zod');
require('dotenv').config({ path: require('path').join(__dirname, '../../.env') });

// Define a tool the agent can use
const searchProducts = tool({
  name: 'search_products',
  description: 'Search SkyyRose product catalog by keyword',
  parameters: z.object({
    query: z.string().describe('Search query'),
    collection: z.enum(['BLACK ROSE', 'LOVE HURTS', 'SIGNATURE', 'all']).default('all')
  }),
  execute: async ({ query, collection }) => {
    // In production: wire to semantic search / product-embeddings.json
    return JSON.stringify({
      results: [
        { id: 'br-001', name: 'BLACK Rose Crewneck', collection: 'BLACK ROSE', price: '$125' },
        { id: 'lh-004', name: 'Love Hurts Varsity Jacket', collection: 'LOVE HURTS', price: '$265' }
      ].filter(p => collection === 'all' || p.collection === collection),
      query
    });
  }
});

// SkyyRose shopping assistant agent
const skyyAgent = new Agent({
  name: 'Skyy',
  instructions: `You are Skyy, the SkyyRose luxury fashion assistant.
Help customers discover and explore the SkyyRose collections: BLACK ROSE, LOVE HURTS, and SIGNATURE.
Always be stylish, warm, and knowledgeable about luxury streetwear.
Use the search_products tool to find relevant items when customers ask.`,
  model: 'gpt-4o-mini',
  tools: [searchProducts]
});

async function main() {
  console.log('\n🌹 SkyyRose Agent — @openai/agents\n');

  const result = await run(skyyAgent, 'What varsity jackets do you have?');

  console.log('Agent response:', result.finalOutput);
  console.log('\nUsage:', result.usage);
}

main().catch(console.error);
