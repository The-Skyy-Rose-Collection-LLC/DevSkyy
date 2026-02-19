"""Test OpenAI Python client connection"""
from openai_client import OpenAIClient

def main():
    print('\n🔌 OpenAI Python Connection Test\n')
    client = OpenAIClient()
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
        res = client.generate_content('Say "Python connected" — nothing else.', model='gpt-4o-mini')
        assert 'python' in res['text'].lower() or 'connected' in res['text'].lower()

    def t_embed():
        emb = client.embed_content('SkyyRose luxury fashion')
        assert isinstance(emb, list) and len(emb) > 100

    test('Chat completion (gpt-4o-mini)', t_chat)
    test('Embeddings (text-embedding-3-small)', t_embed)

    print(f'\n  {passed} passed · {failed} failed')
    exit(1 if failed else 0)

if __name__ == '__main__':
    main()
