/**
 * Tool/function calling with Claude
 */
const { AnthropicClient } = require('../clients/node/anthropic-client');

async function main() {
  const client = new AnthropicClient();

  console.log('\n🔧 Claude Tool Calling\n');

  const tools = [{
    name: 'get_product_info',
    description: 'Get information about a SkyyRose product by SKU',
    parameters: {
      type: 'object',
      properties: {
        sku: {
          type: 'string',
          description: 'Product SKU (e.g., SR-BR-001)'
        }
      },
      required: ['sku']
    }
  }];

  const res = await client.generateWithTools({
    prompt: 'What can you tell me about product SR-BR-001?',
    tools,
    model: 'claude-sonnet-4-5-20250929',
    systemPrompt: 'You are a SkyyRose product assistant. Use the get_product_info tool to look up products.'
  });

  console.log('Response:', res.text);
  if (res.toolCall) {
    console.log('\nTool Call:');
    console.log('  Function:', res.toolCall.name);
    console.log('  Arguments:', JSON.stringify(res.toolCall.args, null, 2));
  }
}

main().catch(console.error);
