/**
 * Embeddings — semantic similarity example
 */
const { OpenAIClient } = require('../clients/node/openai-client');

function cosineSimilarity(a, b) {
  const dot = a.reduce((sum, v, i) => sum + v * b[i], 0);
  const magA = Math.sqrt(a.reduce((sum, v) => sum + v * v, 0));
  const magB = Math.sqrt(b.reduce((sum, v) => sum + v * v, 0));
  return dot / (magA * magB);
}

async function main() {
  const client = new OpenAIClient();

  const texts = [
    'BLACK Rose Crewneck — gothic rose emblem',
    'Love Hurts Varsity Jacket — satin bomber',
    'Mint Lavender Hoodie — soft pastel streetwear',
    'luxury gothic fashion dark roses'
  ];

  console.log('\n🌹 Embeddings — Semantic Search Demo\n');

  const embeddings = await client.embedContent(texts, 'text-embedding-3-small');
  const query = embeddings[3]; // "luxury gothic fashion dark roses"

  console.log('Query: "luxury gothic fashion dark roses"\n');
  console.log('Similarity scores:');

  for (let i = 0; i < texts.length - 1; i++) {
    const score = cosineSimilarity(query, embeddings[i]);
    console.log(`  ${score.toFixed(4)}  ${texts[i]}`);
  }
}

main().catch(console.error);
