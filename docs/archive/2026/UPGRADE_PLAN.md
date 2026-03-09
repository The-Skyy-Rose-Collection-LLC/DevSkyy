# DevSkyy SDK/ADK Upgrade Plan

## Current Installation Status

### ✅ Currently Installed

```
openai                    2.11.0    ✅ LATEST (Dec 2024)
httpx                     0.28.1    ✅ LATEST
pydantic                  2.12.5    ✅ LATEST
pydantic-settings         2.12.0    ✅ LATEST
tenacity                  9.1.2     ✅ LATEST
httpx-sse                 0.4.3     ✅ (for streaming)
```

### ❌ Missing Official SDKs

```
anthropic                 NOT INSTALLED (should be 0.40.0+)
google-generativeai       NOT INSTALLED (should be 0.8.0+)
cohere                    NOT INSTALLED (should be 5.11.0+)
mistralai                 NOT INSTALLED (should be 1.2.0+)
groq                      NOT INSTALLED (should be 0.11.0+)
```

---

## Critical Issue: Using Raw HTTP Instead of SDKs

**Current Implementation:**

- ✅ OpenAI: Using official SDK ✅
- ❌ Anthropic: Using raw `httpx` HTTP calls
- ❌ Google: Using raw `httpx` HTTP calls
- ❌ Mistral: Using raw `httpx` HTTP calls
- ❌ Cohere: Using raw `httpx` HTTP calls
- ❌ Groq: Using raw `httpx` HTTP calls

**This means:**

- 5 out of 6 providers are using manual HTTP calls
- Missing type safety, error handling, and features
- Higher maintenance burden

---

## Recommended Upgrades

### Option 1: Minimal Upgrade (Recommended to Start)

**Install 3 Essential SDKs:**

```bash
python3 -m pip install anthropic>=0.40.0
python3 -m pip install google-generativeai>=0.8.0
python3 -m pip install cohere>=5.11.0
```

**Time:** 5 minutes
**Size:** ~50MB
**Benefit:**

- Type safety for Claude, Gemini, Cohere
- Better error messages
- Built-in streaming and retries
- Official support

---

### Option 2: Full SDK Upgrade

**Install All Provider SDKs:**

```bash
python3 -m pip install anthropic>=0.40.0
python3 -m pip install google-generativeai>=0.8.0
python3 -m pip install cohere>=5.11.0
python3 -m pip install mistralai>=1.2.0
python3 -m pip install groq>=0.11.0
```

**Time:** 10 minutes
**Size:** ~80MB
**Benefit:** All 6 providers using official SDKs

---

### Option 3: Production-Ready Upgrade (Advanced)

**Add LangChain for Advanced Features:**

```bash
# Core LangChain
python3 -m pip install langchain>=0.3.0
python3 -m pip install langchain-core>=0.3.0

# Provider integrations
python3 -m pip install langchain-openai>=0.2.0
python3 -m pip install langchain-anthropic>=0.3.0
python3 -m pip install langchain-google-genai>=2.0.0
python3 -m pip install langchain-cohere>=0.3.0
python3 -m pip install langchain-mistralai>=0.2.0
python3 -m pip install langchain-groq>=0.2.0

# Optional but useful
python3 -m pip install langchain-community>=0.3.0  # Extra tools
python3 -m pip install langgraph>=0.2.0            # Agent workflows
```

**Time:** 15 minutes
**Size:** ~200MB
**Benefits:**

- Unified interface across all providers
- Built-in prompt templates
- Chain multiple LLM calls together
- Memory management
- Agent frameworks (ReAct, Plan-and-Execute)
- Vector store integrations
- Document loaders
- Output parsers

---

### Option 4: Ultimate Upgrade (Enterprise)

**Add Everything:**

```bash
# All SDKs (from Option 2)
python3 -m pip install anthropic>=0.40.0 google-generativeai>=0.8.0 \
                       cohere>=5.11.0 mistralai>=1.2.0 groq>=0.11.0

# LangChain (from Option 3)
python3 -m pip install langchain>=0.3.0 langchain-openai>=0.2.0 \
                       langchain-anthropic>=0.3.0 langchain-google-genai>=2.0.0

# LiteLLM (Universal Gateway)
python3 -m pip install litellm>=1.50.0

# Instructor (Structured Outputs)
python3 -m pip install instructor>=1.6.0

# OpenTelemetry (Monitoring)
python3 -m pip install opentelemetry-api>=1.27.0 \
                       opentelemetry-sdk>=1.27.0 \
                       opentelemetry-instrumentation-httpx>=0.48b0

# DSPy (Prompt Optimization)
python3 -m pip install dspy-ai>=2.5.0
```

**Time:** 20 minutes
**Size:** ~400MB
**Benefits:** Everything + monitoring, optimization, structured outputs

---

## My Recommendation

**Start with Option 2 (Full SDK Upgrade):**

```bash
python3 -m pip install anthropic>=0.40.0 \
                       google-generativeai>=0.8.0 \
                       cohere>=5.11.0 \
                       mistralai>=1.2.0 \
                       groq>=0.11.0
```

**Why:**

1. ✅ All providers get official SDK support
2. ✅ Better developer experience
3. ✅ Type safety and autocomplete
4. ✅ Not too heavy (~80MB)
5. ✅ Can add LangChain later if needed

**Then, if you need advanced features, add Option 3 (LangChain).**

---

## Implementation Steps

### Step 1: Install SDKs

```bash
python3 -m pip install anthropic>=0.40.0 \
                       google-generativeai>=0.8.0 \
                       cohere>=5.11.0 \
                       mistralai>=1.2.0 \
                       groq>=0.11.0
```

### Step 2: Update requirements.txt

Uncomment and update the SDK lines:

```diff
- # anthropic>=0.8
- # google-generativeai>=0.3
+ anthropic>=0.40.0
+ google-generativeai>=0.8.0
+ cohere>=5.11.0
+ mistralai>=1.2.0
+ groq>=0.11.0
```

### Step 3: Refactor LLM Clients

I can help refactor `orchestration/llm_clients.py` to use the official SDKs instead of raw HTTP.

### Step 4: Test Everything

Run the test suite to make sure all providers still work.

---

## What You'll Get After Upgrade

### Before (Current)

```python
# Manual HTTP calls
response = await self._client.post(
    f"{self.base_url}/v1/messages",
    json={"model": "claude-3-5-sonnet", "messages": [...]}
)
data = response.json()  # Manual parsing
```

### After (With SDK)

```python
# Official SDK with types
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=api_key)
response = await client.messages.create(
    model="claude-3-5-sonnet",
    messages=[...]  # Type-checked!
)
# response is a proper Message object with autocomplete
```

---

## Ready to Upgrade?

**I recommend we:**

1. ✅ Install all 5 missing SDKs (Option 2)
2. ✅ Update requirements.txt
3. ✅ Refactor the LLM clients to use official SDKs
4. ✅ Test everything
5. ⏸️ Consider LangChain later if you need advanced features

**Want me to proceed with the upgrade?**
