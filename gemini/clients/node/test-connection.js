/**
 * Test Gemini API connection
 */

const { GeminiClient } = require('./gemini-client');

async function testConnection() {
  console.log('🧪 Testing Gemini API Connection...\n');

  try {
    const client = new GeminiClient();

    console.log('✅ Client initialized successfully');
    console.log(`📋 Default Model: ${client.defaultModel}\n`);

    // Test basic generation
    console.log('Testing basic text generation...');
    const response = await client.generateContent({
      prompt: 'Say "Hello from Gemini!" and nothing else.'
    });

    console.log('✅ Response received:');
    console.log(`📝 ${response.text}\n`);

    // Test token counting
    console.log('Testing token counting...');
    const tokens = await client.countTokens('This is a test message');
    console.log(`✅ Token count: ${tokens}\n`);

    // Display available models
    console.log('Available models:');
    const models = client.getAvailableModels();
    models.slice(0, 3).forEach(model => {
      console.log(`  • ${model.name} (${model.id})`);
    });

    console.log('\n🎉 All tests passed! Gemini integration is ready.');
    console.log('\nNext steps:');
    console.log('  1. Run examples: npm run example:chat');
    console.log('  2. Try streaming: npm run example:stream');
    console.log('  3. Test vision: npm run example:vision');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('\nTroubleshooting:');
    console.error('  1. Check that GEMINI_API_KEY is set in .env file');
    console.error('  2. Verify API key is valid at https://makersuite.google.com');
    console.error('  3. Ensure you have internet connection');
    process.exit(1);
  }
}

testConnection();
