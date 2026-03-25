/**
 * Function calling example with Gemini
 * Demonstrates tool use / function calling
 */

const { GeminiClient } = require('../clients/node/gemini-client');

async function main() {
  console.log('🔧 Gemini Function Calling Example\n');

  const client = new GeminiClient();

  // Define available functions/tools
  const tools = [
    {
      name: 'get_weather',
      description: 'Get current weather for a location',
      parameters: {
        type: 'object',
        properties: {
          location: {
            type: 'string',
            description: 'City name or location'
          },
          unit: {
            type: 'string',
            enum: ['celsius', 'fahrenheit'],
            description: 'Temperature unit'
          }
        },
        required: ['location']
      }
    },
    {
      name: 'search_web',
      description: 'Search the web for information',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Search query'
          }
        },
        required: ['query']
      }
    }
  ];

  // Simulate function implementations
  const functions = {
    get_weather: ({ location, unit = 'celsius' }) => {
      // In real app, call weather API
      return {
        location,
        temperature: 22,
        unit,
        condition: 'Partly cloudy',
        humidity: 65
      };
    },
    search_web: ({ query }) => {
      // In real app, call search API
      return {
        query,
        results: [
          { title: 'Result 1', snippet: 'Information about ' + query },
          { title: 'Result 2', snippet: 'More details on ' + query }
        ]
      };
    }
  };

  // Test queries
  const queries = [
    "What's the weather in San Francisco?",
    "Search for information about quantum computing",
    "What's the temperature in Tokyo in fahrenheit?"
  ];

  for (const query of queries) {
    console.log(`\nQuery: ${query}`);
    console.log('---');

    const response = await client.generateWithTools({
      prompt: query,
      tools
    });

    if (response.functionCall) {
      const { name, args } = response.functionCall;
      console.log(`🔧 Function call: ${name}`);
      console.log('📋 Arguments:', JSON.stringify(args, null, 2));

      // Execute the function
      const result = functions[name](args);
      console.log('✅ Result:', JSON.stringify(result, null, 2));
    } else {
      console.log('💬 Direct response:', response.text);
    }
  }

  console.log('\n✅ Function calling demo completed!');
}

main().catch(console.error);
