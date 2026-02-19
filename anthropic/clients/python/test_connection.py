"""Test Anthropic Claude Python client connection"""
from anthropic_client import AnthropicClient


def main():
    print('\n🔌 Anthropic Claude Python Connection Test\n')
    client = AnthropicClient()
    passed = failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f'  ✅ {name}')
            passed += 1
        except Exception as e:
            print(f'  ❌ {name}: {e}')
            failed += 1

    def t_chat():
        res = client.generate_content(
            'Say "Claude connected" — nothing else.',
            model='claude-haiku-4-5',
            max_tokens=10
        )
        assert 'claude' in res['text'].lower() or 'connected' in res['text'].lower()

    def t_streaming():
        chunks = list(client.generate_content_stream(
            'Count to 3.', model='claude-sonnet-4-6', max_tokens=20
        ))
        text = ''.join(c['text'] for c in chunks if not c['done'])
        assert text, 'No streaming output'

    test('Chat (claude-haiku-4-5)', t_chat)
    test('Streaming (claude-sonnet-4-6)', t_streaming)

    print(f'\n  {passed} passed · {failed} failed')
    exit(1 if failed else 0)


if __name__ == '__main__':
    main()
