# xAI Grok — DevSkyy

xAI Grok client for Node.js and Python. Grok uses an **OpenAI-compatible API** (`https://api.x.ai/v1`) with unique real-time capabilities.

## Unique Features

| Feature | Details |
|---------|---------|
| **Live Search** | Real-time web + X/Twitter grounding via `search_parameters` |
| **X/Twitter Access** | Direct access to X posts and real-time social data |
| **Aurora** | xAI's image generation model |
| **grok-3-mini** | Fast, cost-effective reasoning model |

## Setup

### API Key

Add to your root `.env`:

```env
XAI_API_KEY=xai-...
```

Get your key at [console.x.ai](https://console.x.ai).

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

| Model | Type | Best For |
|-------|------|----------|
| `grok-3` | Chat + Live Search | Real-time research, complex queries |
| `grok-3-fast` | Chat + Live Search | Fast real-time responses |
| `grok-3-mini` | Chat | Cost-effective reasoning |
| `grok-3-mini-fast` | Chat | Fastest responses |
| `grok-2-vision-1212` | Vision | Image analysis |
| `aurora` | Image Gen | Image generation |

## Examples

### Basic Chat

```javascript
const { GrokClient } = require('./clients/node/grok-client');
const client = new GrokClient();

const res = await client.generateContent({
  prompt: 'What is the latest trend in luxury streetwear?',
  model: 'grok-3-mini'
});
console.log(res.text);
```

### Live Search (Grok's Signature Feature)

```javascript
const res = await client.liveSearch({
  query: 'Latest gothic fashion trends this week',
  model: 'grok-3',
  sources: [{ type: 'web' }, { type: 'x' }]
});
console.log(res.text);
console.log('Citations:', res.citations);
```

### Python

```python
from clients.python.grok_client import GrokClient

client = GrokClient()

# Basic chat
res = client.generate_content('Describe luxury streetwear in 2 sentences.')
print(res['text'])

# Live search
res = client.live_search('Latest fashion week highlights', sources=[{'type': 'web'}])
print(res['text'])
```

## Running Examples

```bash
cd examples

# Basic chat
node chat-basic.js

# Streaming
node chat-streaming.js

# Live web + X search (requires grok-3)
node live-search.js

# Vision analysis
node vision-analysis.js

# Aurora image generation
node image-generation.js
```

## Directory Structure

```
grok/
├── clients/
│   ├── node/
│   │   ├── grok-client.js     # GrokClient class
│   │   ├── package.json
│   │   ├── test-connection.js
│   │   └── list-models.js
│   └── python/
│       ├── grok_client.py     # GrokClient class
│       ├── requirements.txt
│       └── test_connection.py
├── config/
│   ├── models.json            # Model catalog + task routing
│   └── settings.json          # Base URL, defaults, rate limits
├── examples/
│   ├── chat-basic.js
│   ├── chat-streaming.js
│   ├── live-search.js         # Real-time web + X grounding
│   ├── vision-analysis.js     # grok-2-vision-1212
│   └── image-generation.js    # Aurora
└── README.md
```
