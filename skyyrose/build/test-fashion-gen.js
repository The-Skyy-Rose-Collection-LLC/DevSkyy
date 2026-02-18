/**
 * Test fashion model generation with one product
 */
const { PRODUCTS, generateFashionModel } = require('./generate-fashion-models.js');
const { GoogleGenAI } = require('@google/genai');

async function test() {
  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    console.error('No API key found');
    process.exit(1);
  }

  const ai = new GoogleGenAI({ apiKey });
  const product = PRODUCTS[0]; // First product: Black Rose Tee

  console.log('Testing fashion model generation with:', product.name);
  const result = await generateFashionModel(product, ai);
  console.log('\nResult:', result);
}

test().catch(console.error);
