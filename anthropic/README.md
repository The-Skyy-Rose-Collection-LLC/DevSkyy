# Anthropic Claude — DevSkyy

Anthropic Claude client for Node.js and Python. Claude 4.5/4.6: Sonnet, Opus, Haiku.

## Capabilities

- **Chat** — Multi-turn conversations with 200K context
- **Streaming** — Real-time token streaming
- **Vision** — Image analysis (Sonnet/Opus)
- **Tool Use** — Function/tool calling
- **Long Context** — 200K token context window

## Setup

### API Key

Add to your root `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Get your key at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys).

### Node.js

```bash
cd clients/node
npm install
node list-models.js
node test-connection.js
```

### Python

```bash
cd clients/python
pip install -r requirements.txt
python test_connection.py
```

## Models

| Model | Type | Best For | Context | Cost (input/output per 1M tok) |
|-------|------|----------|---------|--------------------------------|
| `claude-opus-4-6` | Chat | Most intelligent for agents and coding | 200K | $5 / $25 |
| `claude-sonnet-4-6` ★ | Chat | Best speed + intelligence (recommended) | 200K | $3 / $15 |
| `claude-haiku-4-5` | Chat | Fastest with near-frontier intelligence | 200K | $1 / $5 |

## Examples

### Basic Chat

```javascript
const { AnthropicClient } = require('./clients/node/anthropic-client');
const client = new AnthropicClient();

const res = await client.generateContent({
  prompt: 'Explain luxury gothic fashion in 2 sentences.',
  model: 'claude-sonnet-4-6'
});
console.log(res.text);
```

### Streaming

```javascript
for await (const chunk of client.generateContentStream({
  prompt: 'Write a poem about SkyyRose.',
  model: 'claude-sonnet-4-6'
})) {
  if (!chunk.done) process.stdout.write(chunk.text);
}
```

### Vision

```javascript
const res = await client.analyzeImage({
  imagePath: './product.jpg',
  prompt: 'Describe this luxury fashion item in detail.',
  model: 'claude-sonnet-4-6'
});
```

### Python

```python
from clients.python.anthropic_client import AnthropicClient

client = AnthropicClient()

# Basic chat
res = client.generate_content('Describe luxury streetwear in 2 sentences.')
print(res['text'])

# Vision
res = client.analyze_image(image_path='./product.jpg', prompt='Describe this product.')
print(res['text'])
```

## Running Examples

```bash
cd examples

# Basic chat
node chat-basic.js

# Streaming
node chat-streaming.js

# Vision analysis
node vision-analysis.js

# Tool calling
node tool-calling.js
```

## Directory Structure

```
anthropic/
├── clients/
│   ├── node/
│   │   ├── anthropic-client.js  # AnthropicClient class
│   │   ├── package.json
│   │   ├── test-connection.js
│   │   └── list-models.js
│   └── python/
│       ├── anthropic_client.py  # AnthropicClient class
│       ├── requirements.txt
│       └── test_connection.py
├── config/
│   ├── models.json              # Model catalog + task routing
│   └── settings.json            # Base URL, defaults, rate limits
├── examples/
│   ├── chat-basic.js
│   ├── chat-streaming.js
│   ├── vision-analysis.js
│   └── tool-calling.js
└── README.md
```
