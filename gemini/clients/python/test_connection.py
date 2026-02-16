"""
Test Gemini API connection
"""

from gemini_client import GeminiClient


def test_connection():
    print('🧪 Testing Gemini API Connection...\n')

    try:
        client = GeminiClient()

        print('✅ Client initialized successfully')
        print(f'📋 Default Model: {client.default_model}\n')

        # Test basic generation
        print('Testing basic text generation...')
        response = client.generate_content('Say "Hello from Gemini!" and nothing else.')

        print('✅ Response received:')
        print(f'📝 {response["text"]}\n')

        # Test token counting
        print('Testing token counting...')
        tokens = client.count_tokens('This is a test message')
        print(f'✅ Token count: {tokens}\n')

        # Display available models
        print('Available models:')
        models = client.get_available_models()
        for model in models[:3]:
            print(f'  • {model["name"]} ({model["id"]})')

        print('\n🎉 All tests passed! Gemini integration is ready.')
        print('\nNext steps:')
        print('  1. Try the chat example')
        print('  2. Test streaming responses')
        print('  3. Experiment with vision analysis')

    except Exception as e:
        print(f'❌ Test failed: {e}')
        print('\nTroubleshooting:')
        print('  1. Check that GEMINI_API_KEY is set in .env file')
        print('  2. Verify API key is valid at https://makersuite.google.com')
        print('  3. Ensure you have internet connection')
        print('  4. Install dependencies: pip install google-generativeai python-dotenv')
        return 1

    return 0


if __name__ == '__main__':
    exit(test_connection())
