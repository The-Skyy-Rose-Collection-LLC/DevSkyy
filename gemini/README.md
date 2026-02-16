# Gemini AI Integration

Complete Google Gemini AI integration for DevSkyy projects with multi-language support.

## 🚀 Features

- **Multi-Model Support**: Gemini 2.0, Gemini Pro, Gemini Flash
- **Multi-Language**: Node.js/TypeScript and Python clients
- **Authentication**: API Key and OAuth 2.0 support
- **Rate Limiting**: Built-in request throttling and retry logic
- **Streaming**: Real-time response streaming
- **Function Calling**: Tool integration support
- **Context Management**: Conversation history and context window optimization

## 📁 Structure

```
gemini/
├── README.md                 # This file
├── config/                   # Configuration files
│   ├── settings.json         # Gemini settings
│   ├── models.json           # Model configurations
│   └── .env.example          # Environment template
├── clients/                  # API clients
│   ├── node/                 # Node.js/TypeScript client
│   └── python/               # Python client
├── services/                 # Service integrations
│   ├── chat.js              # Chat completion service
│   ├── embeddings.js        # Text embeddings
│   ├── vision.js            # Vision/image analysis
│   └── code-generation.js   # Code generation utilities
├── utils/                    # Utility functions
│   ├── auth.js              # Authentication helpers
│   ├── rate-limiter.js      # Rate limiting
│   └── token-counter.js     # Token estimation
├── examples/                 # Usage examples
└── tests/                    # Test suite
```

## 🔧 Setup

### 1. Install Dependencies

#### Node.js
```bash
cd gemini/clients/node
npm install @google/generative-ai dotenv
```

#### Python
```bash
cd gemini/clients/python
pip install google-generativeai python-dotenv
```

### 2. Configure API Key

Create `.env` file in the gemini directory:
```bash
cp config/.env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Test Connection

#### Node.js
```bash
node clients/node/test-connection.js
```

#### Python
```bash
python clients/python/test_connection.py
```

## 📖 Usage

### Basic Chat (Node.js)

```javascript
const { GeminiClient } = require('./clients/node/gemini-client');

const client = new GeminiClient();

async function chat() {
  const response = await client.generateContent({
    model: 'gemini-2.0-flash-exp',
    prompt: 'Explain quantum computing in simple terms'
  });

  console.log(response.text);
}

chat();
```

### Streaming Response (Node.js)

```javascript
const stream = await client.generateContentStream({
  model: 'gemini-2.0-flash-exp',
  prompt: 'Write a creative story about AI'
});

for await (const chunk of stream) {
  process.stdout.write(chunk.text);
}
```

### Vision Analysis (Node.js)

```javascript
const response = await client.analyzeImage({
  imagePath: './image.jpg',
  prompt: 'Describe this image in detail'
});

console.log(response.text);
```

### Chat with Context (Python)

```python
from clients.python.gemini_client import GeminiClient

client = GeminiClient()

# Start a conversation
chat = client.start_chat()

# Send messages
response1 = chat.send_message("What is machine learning?")
print(response1.text)

response2 = chat.send_message("Give me a practical example")
print(response2.text)
```

### Function Calling (Node.js)

```javascript
const tools = [{
  name: 'get_weather',
  description: 'Get current weather for a location',
  parameters: {
    type: 'object',
    properties: {
      location: { type: 'string' }
    }
  }
}];

const response = await client.generateWithTools({
  prompt: 'What is the weather in San Francisco?',
  tools
});

if (response.functionCall) {
  console.log('Function:', response.functionCall.name);
  console.log('Args:', response.functionCall.args);
}
```

## 🎯 Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| `gemini-2.0-flash-exp` | Latest experimental flash model | Fast responses, general tasks |
| `gemini-pro` | Stable production model | Complex reasoning, long context |
| `gemini-pro-vision` | Multimodal model | Image + text analysis |
| `gemini-ultra` | Most capable model | Advanced reasoning, complex tasks |

## ⚙️ Configuration

Edit `config/settings.json` to customize:

```json
{
  "defaultModel": "gemini-2.0-flash-exp",
  "temperature": 0.7,
  "topK": 40,
  "topP": 0.95,
  "maxOutputTokens": 2048,
  "safetySettings": {
    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE"
  }
}
```

## 🔐 Authentication

### API Key (Recommended for Development)

Set in `.env`:
```env
GEMINI_API_KEY=your_key_here
```

### OAuth 2.0 (For Production)

1. Create OAuth credentials in Google Cloud Console
2. Set redirect URI
3. Configure in `config/auth.json`

## 📊 Rate Limits

- **Free Tier**: 60 requests per minute
- **Paid Tier**: Higher limits based on plan

Built-in rate limiting automatically handles:
- Request throttling
- Exponential backoff
- Retry logic

## 🧪 Testing

Run test suite:
```bash
# Node.js
npm test

# Python
pytest tests/
```

## 🔗 Integration Examples

### WordPress Plugin
```javascript
// Use in wordpress-copilot
const gemini = require('../gemini/clients/node/gemini-client');
```

### CLI Tool
```javascript
#!/usr/bin/env node
const { GeminiClient } = require('./gemini/clients/node/gemini-client');
// Build CLI tool
```

### API Endpoint
```javascript
app.post('/api/ai/generate', async (req, res) => {
  const client = new GeminiClient();
  const response = await client.generateContent({
    prompt: req.body.prompt
  });
  res.json({ text: response.text });
});
```

## 📚 Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Model Garden](https://ai.google.dev/models/gemini)
- [Pricing](https://ai.google.dev/pricing)
- [Quickstart Guide](https://ai.google.dev/tutorials/get_started_node)

## 🛠️ Troubleshooting

### API Key Issues
```bash
# Verify API key is set
node -e "console.log(process.env.GEMINI_API_KEY)"
```

### Rate Limit Errors
- Wait 60 seconds between requests
- Upgrade to paid tier
- Use built-in rate limiter

### Connection Issues
- Check internet connection
- Verify API key is valid
- Check Google AI service status

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

---

**Last Updated**: February 16, 2026
**Maintained By**: DevSkyy Team
