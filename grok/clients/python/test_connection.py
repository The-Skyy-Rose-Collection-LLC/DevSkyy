"""Test xAI Grok Python client connection"""
from grok_client import GrokClient


def main():
    print('\n🔌 Grok (xAI) Python Connection Test\n')
    client = GrokClient()
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
            'Say "Grok connected" — nothing else.',
            model='grok-3-mini'
        )
        assert 'grok' in res['text'].lower() or 'connected' in res['text'].lower()

    def t_streaming():
        chunks = list(client.generate_content_stream(
            'Count to 3.', model='grok-3-mini', max_tokens=20
        ))
        text = ''.join(c['text'] for c in chunks if not c['done'])
        assert text, 'No streaming output'

    test('Chat completion (grok-3-mini)', t_chat)
    test('Streaming (grok-3-mini)', t_streaming)

    print(f'\n  {passed} passed · {failed} failed')
    exit(1 if failed else 0)


if __name__ == '__main__':
    main()
