/**
 * List available Gemini models
 */

const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config({ path: '../../.env' });

async function listModels() {
  const apiKey = process.env.GEMINI_API_KEY;

  if (!apiKey) {
    console.error('GEMINI_API_KEY not found in .env file');
    process.exit(1);
  }

  const genAI = new GoogleGenerativeAI(apiKey);

  try {
    console.log('Fetching available models...\n');

    // List models using the API
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.models && data.models.length > 0) {
      console.log('Available models:\n');
      data.models.forEach((model, index) => {
        console.log(`${index + 1}. ${model.name}`);
        console.log(`   Display Name: ${model.displayName}`);
        console.log(`   Description: ${model.description || 'N/A'}`);
        console.log(`   Supported Methods: ${model.supportedGenerationMethods?.join(', ') || 'N/A'}`);
        console.log('');
      });

      // Find recommended model for generateContent
      const generateContentModels = data.models.filter(m =>
        m.supportedGenerationMethods?.includes('generateContent')
      );

      if (generateContentModels.length > 0) {
        console.log('\n✅ Recommended models for text generation:');
        generateContentModels.slice(0, 5).forEach(model => {
          const modelId = model.name.replace('models/', '');
          console.log(`  • ${modelId}`);
        });
      }
    } else {
      console.log('No models available');
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

listModels();
