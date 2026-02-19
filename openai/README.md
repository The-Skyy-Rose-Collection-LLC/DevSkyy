# OpenAI — DevSkyy Integration

Full OpenAI ecosystem: SDK, Agents SDK, Assistants, Realtime, Embeddings, Vision, Images, Audio.

## Structure

```
openai/
├── clients/
│   ├── node/
│   │   ├── openai-client.js      # Full OpenAI Node.js client
│   │   ├── list-models.js        # List all available models
│   │   ├── test-connection.js    # Test API connectivity
│   │   └── package.json          # openai + @openai/agents + @ai-sdk/openai
│   └── python/
│       ├── openai_client.py      # Full OpenAI Python client
│       ├── test_connection.py    # Test API connectivity
│       └── requirements.txt      # openai + openai-agents + langchain-openai
├── config/
│   ├── models.json               # Model catalog with pricing + capabilities
│   └── settings.json             # Default generation config, rate limits
└── examples/
    ├── chat-basic.js             # Simple chat completion
    ├── chat-streaming.js         # Streaming response
    ├── embeddings.js             # Semantic similarity with embeddings
    ├── image-generation.js       # gpt-image-1 / DALL·E generation
    └── agents-basic.js           # @openai/agents multi-agent example
```

## Quick Start

### Node.js
```bash
cd clients/node && npm install
node test-connection.js
node list-models.js
```

### Python
```bash
cd clients/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python test_connection.py
```

## SDKs Included

| SDK | Package | Purpose |
|-----|---------|---------|
| OpenAI SDK | `openai` | Core chat, embeddings, images, audio, assistants |
| Agents SDK | `@openai/agents` (JS) / `openai-agents` (PY) | Multi-agent orchestration, tool use, handoffs |
| Vercel AI SDK | `@ai-sdk/openai` | Edge-compatible streaming, unified AI interface |
| LangChain | `langchain-openai` (PY) | Chain/agent composition with OpenAI |

## Models

| Model | Best For | Context |
|-------|---------|---------|
| `gpt-4o` | Production, vision, complex tasks | 128K |
| `gpt-4o-mini` | Fast, affordable, everyday tasks | 128K |
| `o3` | Advanced reasoning, math, code | 200K |
| `o4-mini` | Fast reasoning | 200K |
| `gpt-image-1` | Image generation/editing | — |
| `text-embedding-3-small` | Semantic search, RAG | 8K |
| `whisper-1` | Audio transcription | — |
| `tts-1-hd` | Text-to-speech | — |

## Environment

```bash
OPENAI_API_KEY=sk-proj-...   # Required
```

Set in root `DevSkyy/.env` — all clients resolve up to repo root automatically.
