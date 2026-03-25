/**
 * Basic chat example with Gemini
 */

const { GeminiClient } = require('../clients/node/gemini-client');

async function main() {
  console.log('💬 Gemini Chat Example\n');

  const client = new GeminiClient();

  // Simple question
  console.log('Question: What is quantum computing?\n');

  const response = await client.generateContent({
    prompt: 'Explain quantum computing in 2-3 sentences',
    maxOutputTokens: 150
  });

  console.log('Answer:', response.text);
  console.log('\nTokens used:', response.usageMetadata.totalTokenCount);

  // Follow-up with conversation
  console.log('\n---\n');
  console.log('Starting a conversation...\n');

  const chat = client.startChat();

  const msg1 = await chat.sendMessage('Hi! My name is Alice.');
  console.log('Assistant:', msg1.response.text());

  const msg2 = await chat.sendMessage('What was my name again?');
  console.log('Assistant:', msg2.response.text());

  console.log('\n✅ Chat completed!');
}

main().catch(console.error);
