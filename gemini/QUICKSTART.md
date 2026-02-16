# Gemini AI Quick Start Guide

Get up and running with Gemini AI in 5 minutes.

## ⚡ Quick Setup

### 1. Get API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Copy your API key

### 2. Configure

```bash
cd /Users/coreyfoster/DevSkyy/gemini

# Create .env file
cp config/.env.example .env

# Edit .env and add your API key
nano .env  # or use your favorite editor
```

Add this line to `.env`:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies

**Node.js:**
```bash
cd clients/node
npm install
```

**Python:**
```bash
cd clients/python
pip install -r requirements.txt
```

### 4. Test Connection

**Node.js:**
```bash
cd clients/node
node test-connection.js
```

**Python:**
```bash
cd clients/python
python test_connection.py
```

You should see:
```
🧪 Testing Gemini API Connection...
✅ Client initialized successfully
📋 Default Model: gemini-2.0-flash-exp
✅ Response received
🎉 All tests passed!
```

## 🎯 First Examples

### Simple Chat (Node.js)

Create `my-first-chat.js`:
```javascript
const { GeminiClient } = require('./clients/node/gemini-client');

async function main() {
  const client = new GeminiClient();

  const response = await client.generateContent({
    prompt: 'Explain AI in one sentence'
  });

  console.log(response.text);
}

main();
```

Run it:
```bash
node my-first-chat.js
```

### Simple Chat (Python)

Create `my_first_chat.py`:
```python
from clients.python.gemini_client import GeminiClient

client = GeminiClient()

response = client.generate_content('Explain AI in one sentence')
print(response['text'])
```

Run it:
```bash
python my_first_chat.py
```

## 📚 More Examples

Run the included examples:

```bash
# Basic chat
npm run example:chat

# Streaming responses
npm run example:stream

# Vision analysis (provide image path)
node examples/vision-analysis.js ~/Pictures/photo.jpg

# Function calling
node examples/function-calling.js
```

## 🚀 Next Steps

1. **Read the full README**: `cat README.md`
2. **Explore examples**: Check `examples/` directory
3. **Try different models**: See `config/models.json`
4. **Adjust settings**: Edit `config/settings.json`

## 🆘 Troubleshooting

### "API key is required" error
- Make sure `.env` file exists in `/Users/coreyfoster/DevSkyy/gemini/`
- Verify `GEMINI_API_KEY=...` is set correctly
- No spaces around the `=` sign
- No quotes needed around the key

### "Invalid API key" error
- Double-check your key at https://makersuite.google.com
- Make sure you copied the entire key
- Try generating a new key

### "Module not found" error (Node.js)
```bash
cd clients/node
npm install
```

### "Module not found" error (Python)
```bash
cd clients/python
pip install -r requirements.txt
```

### Rate limit errors
- Free tier: 60 requests per minute
- Wait 60 seconds between bursts
- Consider upgrading to paid tier

## 💡 Tips

1. **Use streaming** for long responses - better UX
2. **Count tokens** before generation to estimate costs
3. **Try different models** - flash for speed, pro for quality
4. **Adjust temperature** - lower for factual, higher for creative
5. **Enable caching** for repeated queries (saves costs)

## 📖 Resources

- [Full README](README.md)
- [API Documentation](https://ai.google.dev/docs)
- [Model Garden](https://ai.google.dev/models/gemini)
- [Pricing](https://ai.google.dev/pricing)

---

**Need help?** Check the troubleshooting section in the main README or open an issue.
