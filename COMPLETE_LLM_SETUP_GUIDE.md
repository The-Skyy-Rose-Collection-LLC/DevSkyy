# Complete LLM Provider Setup Guide

Step-by-step guide to set up all 6 LLM providers for DevSkyy.

---

## ✅ Current Status

- ✅ **OpenAI** - Already configured and working!

**Remaining providers to set up:**
- ⏳ Anthropic (Claude)
- ⏳ Google (Gemini)
- ⏳ Groq (Fast inference)
- ⏳ Mistral (Optional)
- ⏳ Cohere (Optional)

---

## 🎯 Recommended Setup Order

### Priority 1: Essential (Highly Recommended)

1. **Anthropic (Claude)** - Best for coding, analysis, long context
2. **Google (Gemini)** - Best for long documents (2M tokens), free tier
3. **Groq** - Ultra-fast inference, generous free tier

### Priority 2: Optional

4. **Mistral** - European alternative, good for privacy
5. **Cohere** - Best for RAG/search applications

---

## 📋 Step-by-Step Setup

### Step 1: Get Your API Keys

Open these URLs and create API keys:

| Provider | URL | Notes |
|----------|-----|-------|
| **Anthropic** | https://console.anthropic.com/settings/keys | $5 free credit |
| **Google** | https://aistudio.google.com/app/apikey | Free tier available |
| **Groq** | https://console.groq.com/keys | Generous free tier |
| Mistral | https://console.mistral.ai/api-keys/ | €5 free credit |
| Cohere | https://dashboard.cohere.com/api-keys | Free trial |

**For each provider:**
1. Sign up or log in
2. Navigate to API keys section
3. Click "Create API Key" or similar
4. Copy the key immediately (you won't see it again)
5. Keep it in a secure place temporarily

---

### Step 2: Add Keys to Your Environment

**Option A: Interactive Script (Easiest)**

```bash
./setup_all_llm_keys.sh
```

This will:
- Check which keys you already have
- Prompt you for each missing key
- Add them to your ~/.zshrc
- Skip any you don't want to set up

**Option B: Manual Setup**

Add to your ~/.zshrc:

```bash
# Open your shell config
nano ~/.zshrc

# Add these lines (replace with your actual keys):
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GOOGLE_API_KEY="your-google-key-here"
export GROQ_API_KEY="gsk_your-groq-key-here"
export MISTRAL_API_KEY="your-mistral-key-here"
export COHERE_API_KEY="your-cohere-key-here"

# Save: Ctrl+X, then Y, then Enter

# Reload your shell
source ~/.zshrc
```

---

### Step 3: Verify Setup

```bash
# Reload shell
source ~/.zshrc

# Verify all providers
python3 scripts/verify_llm_clients.py
```

You should see green checkmarks for each provider you configured.

---

## 🔍 Provider Details

### 1. Anthropic (Claude) - HIGHLY RECOMMENDED

**Why use it:**
- Best for coding tasks
- Excellent reasoning
- 200K context window
- Very accurate

**Models:**
- `claude-3-5-sonnet-20241022` - Best overall (recommended)
- `claude-3-opus-20240229` - Most capable
- `claude-3-haiku-20240307` - Fastest, cheapest

**Pricing:**
- Sonnet: $3/$15 per 1M tokens (input/output)
- Free $5 credit to start

**Get key:** https://console.anthropic.com/settings/keys

---

### 2. Google (Gemini) - HIGHLY RECOMMENDED

**Why use it:**
- Massive 2M token context window
- Free tier available
- Good for document analysis
- Multimodal (text + images)

**Models:**
- `gemini-2.0-flash-exp` - Latest, fastest
- `gemini-1.5-pro` - Best quality
- `gemini-1.5-flash` - Fast and cheap

**Pricing:**
- Free tier: 15 requests/minute
- Pro: $1.25/$5 per 1M tokens

**Get key:** https://aistudio.google.com/app/apikey

---

### 3. Groq - HIGHLY RECOMMENDED

**Why use it:**
- Ultra-fast inference (500+ tokens/sec)
- Generous free tier
- Great for development/testing
- Open source models

**Models:**
- `llama-3.1-70b-versatile` - Best quality
- `llama-3.1-8b-instant` - Fastest
- `mixtral-8x7b-32768` - Good balance

**Pricing:**
- Free tier: 30 requests/minute
- Very affordable paid tier

**Get key:** https://console.groq.com/keys

---

### 4. Mistral (Optional)

**Why use it:**
- European company (GDPR compliant)
- Good for privacy-sensitive work
- Competitive pricing
- Code-specialized models

**Models:**
- `mistral-large-latest` - Best quality
- `codestral-latest` - Code generation
- `mistral-small-latest` - Fast and cheap

**Get key:** https://console.mistral.ai/api-keys/

---

### 5. Cohere (Optional)

**Why use it:**
- Best for RAG (Retrieval Augmented Generation)
- Excellent embeddings
- Good for search applications

**Models:**
- `command-r-plus` - Best quality
- `command-r` - Balanced

**Get key:** https://dashboard.cohere.com/api-keys

---

## 🧪 Testing Each Provider

After setup, test each provider:

```python
import asyncio
from orchestration import (
    OpenAIClient, AnthropicClient, GoogleClient,
    GroqClient, MistralClient, CohereClient,
    Message, MessageRole
)

async def test_provider(client, name):
    try:
        response = await client.complete(
            messages=[Message(role=MessageRole.USER, content="Say hello!")],
            max_tokens=50
        )
        print(f"✓ {name}: {response.content}")
    except Exception as e:
        print(f"✗ {name}: {e}")

async def test_all():
    await test_provider(OpenAIClient(), "OpenAI")
    await test_provider(AnthropicClient(), "Anthropic")
    await test_provider(GoogleClient(), "Google")
    await test_provider(GroqClient(), "Groq")
    # await test_provider(MistralClient(), "Mistral")
    # await test_provider(CohereClient(), "Cohere")

asyncio.run(test_all())
```

---

## 🎯 Quick Start Examples

### Use the Orchestrator (Automatic Selection)

```python
import asyncio
from orchestration import LLMOrchestrator, TaskType

async def main():
    orchestrator = LLMOrchestrator()
    
    # Automatically picks best model for the task
    result = await orchestrator.complete(
        prompt="Write a Python function to calculate fibonacci",
        task_type=TaskType.CODE_GENERATION
    )
    
    print(f"Model used: {result.model}")
    print(f"Provider: {result.provider}")
    print(result.content)

asyncio.run(main())
```

### Use Specific Provider

```python
import asyncio
from orchestration import AnthropicClient, Message, MessageRole

async def main():
    client = AnthropicClient()
    
    response = await client.complete(
        messages=[
            Message(role=MessageRole.USER, content="Explain async/await")
        ],
        model="claude-3-5-sonnet-20241022",
        max_tokens=500
    )
    
    print(response.content)

asyncio.run(main())
```

---

## 📊 Cost Comparison

| Provider | Model | Input (per 1M) | Output (per 1M) | Context |
|----------|-------|----------------|-----------------|---------|
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | 128K |
| Anthropic | claude-3-5-sonnet | $3.00 | $15.00 | 200K |
| Google | gemini-1.5-flash | $0.075 | $0.30 | 1M |
| Groq | llama-3.1-70b | Free tier | Free tier | 128K |
| Mistral | mistral-small | $0.20 | $0.60 | 32K |
| Cohere | command-r | $0.50 | $1.50 | 128K |

---

## ✅ Verification Checklist

After setup:

- [ ] API keys obtained from provider websites
- [ ] Keys added to ~/.zshrc
- [ ] Shell reloaded (`source ~/.zshrc`)
- [ ] Verification script run successfully
- [ ] Test script confirms providers work
- [ ] Keys are NOT committed to git

---

## 🔐 Security Reminders

- ✅ Keys are in ~/.zshrc (not in git)
- ✅ .env file is in .gitignore
- ✅ Never paste keys in chat/messages
- ✅ Rotate keys every 90 days
- ✅ Set billing limits on each platform

---

## 🆘 Troubleshooting

### "API key not found"
```bash
source ~/.zshrc
```

### "Authentication failed"
- Verify key at provider's website
- Check for typos
- Ensure key hasn't been revoked

### "Rate limit exceeded"
- Check your usage dashboard
- Wait a few minutes
- Upgrade to paid tier if needed

---

## 📚 Next Steps

1. Set up at least Anthropic and Google (recommended)
2. Run verification: `python3 scripts/verify_llm_clients.py`
3. Try the orchestrator examples
4. Read the full docs: `docs/LLM_CLIENTS_QUICK_START.md`

---

**Ready to set up? Run:** `./setup_all_llm_keys.sh`

