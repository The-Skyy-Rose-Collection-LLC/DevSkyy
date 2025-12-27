# SDK/ADK Upgrade Analysis for DevSkyy

## Current State

### ✅ What's Currently Installed

- `openai>=1.6` - Official OpenAI SDK ✅
- `httpx>=0.25` - HTTP client (used for all other providers)
- `tenacity>=8.2` - Retry logic
- `pydantic>=2.5` - Data validation

### ❌ What's Missing (Commented Out)

- `anthropic>=0.8` - Official Anthropic SDK (COMMENTED OUT)
- `google-generativeai>=0.3` - Official Google Gemini SDK (COMMENTED OUT)

### ❌ Not Installed At All

- Mistral SDK
- Cohere SDK
- Groq SDK (uses OpenAI-compatible API)

---

## Current Implementation Issues

### Problem: Using Raw HTTP Instead of Official SDKs

All providers except OpenAI are using **raw `httpx` HTTP calls** instead of official SDKs:

```python
# Current approach (orchestration/llm_clients.py)
import httpx

class AnthropicClient(BaseLLMClient):
    async def complete(self, ...):
        response = await self._client.post(
            f"{self.base_url}/v1/messages",
            json=payload
        )
```

### Why This Is Suboptimal

1. **No Type Safety** - Missing proper type hints from official SDKs
2. **Manual Error Handling** - Have to parse error responses manually
3. **Missing Features** - SDKs have built-in streaming, retries, helpers
4. **Breaking Changes** - API changes require manual updates
5. **No IDE Support** - Missing autocomplete and documentation
6. **Maintenance Burden** - Have to track API changes ourselves

---

## Recommended Upgrades

### Priority 1: Essential SDKs (Install These)

#### 1. Anthropic SDK

```bash
pip install anthropic>=0.40.0
```

**Benefits:**

- Official Claude SDK with full type safety
- Built-in streaming support
- Automatic retry logic
- Better error messages
- Tool use helpers

**Latest Version:** 0.40.0 (December 2024)

#### 2. Google Generative AI SDK

```bash
pip install google-generativeai>=0.8.0
```

**Benefits:**

- Official Gemini SDK
- Supports Gemini 2.0 Flash
- Built-in safety settings
- Multimodal support (text + images)
- Streaming and async support

**Latest Version:** 0.8.0 (December 2024)

#### 3. Cohere SDK

```bash
pip install cohere>=5.11.0
```

**Benefits:**

- Official Cohere SDK
- RAG-optimized features
- Embeddings support
- Rerank API
- Chat and generation APIs

**Latest Version:** 5.11.0 (December 2024)

---

### Priority 2: Optional SDKs

#### 4. Mistral SDK

```bash
pip install mistralai>=1.2.0
```

**Benefits:**

- Official Mistral SDK
- Supports all Mistral models
- Function calling support
- Streaming

**Latest Version:** 1.2.0 (December 2024)

#### 5. Groq SDK

```bash
pip install groq>=0.11.0
```

**Benefits:**

- Official Groq SDK (OpenAI-compatible)
- Ultra-fast inference
- Same interface as OpenAI
- Better error handling

**Latest Version:** 0.11.0 (December 2024)

**Note:** Groq uses OpenAI-compatible API, so we could also just use the OpenAI SDK with a different base URL.

---

## Additional Upgrades

### 1. LangChain Integration (Optional but Powerful)

```bash
pip install langchain>=0.3.0
pip install langchain-openai>=0.2.0
pip install langchain-anthropic>=0.3.0
pip install langchain-google-genai>=2.0.0
pip install langchain-cohere>=0.3.0
pip install langchain-mistralai>=0.2.0
pip install langchain-groq>=0.2.0
```

**Benefits:**

- Unified interface across all providers
- Built-in prompt templates
- Chain multiple LLM calls
- Memory management
- Agent frameworks
- Vector store integrations

### 2. LiteLLM (Universal LLM Gateway)

```bash
pip install litellm>=1.50.0
```

**Benefits:**

- Single interface for 100+ LLM providers
- Automatic fallbacks
- Load balancing
- Cost tracking
- Caching
- Rate limiting

### 3. Instructor (Structured Outputs)

```bash
pip install instructor>=1.6.0
```

**Benefits:**

- Pydantic models → LLM outputs
- Automatic validation
- Retry on validation failure
- Works with all providers

### 4. OpenTelemetry (Observability)

```bash
pip install opentelemetry-api>=1.27.0
pip install opentelemetry-sdk>=1.27.0
pip install opentelemetry-instrumentation-httpx>=0.48b0
```

**Benefits:**

- Track LLM performance
- Monitor costs
- Trace requests
- Debug issues

---

## Upgrade Implementation Plan

### Phase 1: Install Official SDKs (Immediate)

```bash
# Essential SDKs
pip install anthropic>=0.40.0
pip install google-generativeai>=0.8.0
pip install cohere>=5.11.0

# Optional SDKs
pip install mistralai>=1.2.0
pip install groq>=0.11.0
```

### Phase 2: Refactor LLM Clients (1-2 hours)

Rewrite `orchestration/llm_clients.py` to use official SDKs:

**Before (current):**

```python
class AnthropicClient(BaseLLMClient):
    async def complete(self, ...):
        response = await self._client.post(...)  # Raw HTTP
```

**After (with SDK):**

```python
from anthropic import AsyncAnthropic

class AnthropicClient(BaseLLMClient):
    def __init__(self, ...):
        self.client = AsyncAnthropic(api_key=api_key)

    async def complete(self, ...):
        response = await self.client.messages.create(...)  # Official SDK
```

### Phase 3: Add Advanced Features (Optional)

1. **LangChain Integration** - For complex workflows
2. **LiteLLM** - For unified interface and fallbacks
3. **Instructor** - For structured outputs
4. **OpenTelemetry** - For monitoring

---

## Cost-Benefit Analysis

### Current Approach (Raw HTTP)

- ✅ Minimal dependencies
- ✅ Full control
- ❌ High maintenance
- ❌ No type safety
- ❌ Missing features
- ❌ Manual error handling

### With Official SDKs

- ✅ Type safety
- ✅ Better error messages
- ✅ Built-in features (streaming, retries)
- ✅ Automatic updates
- ✅ IDE support
- ❌ More dependencies (~50MB total)

### With LangChain/LiteLLM

- ✅ All SDK benefits
- ✅ Unified interface
- ✅ Advanced features (agents, chains)
- ✅ Production-ready
- ❌ Larger dependencies (~200MB)
- ❌ Learning curve

---

## Recommended Action

### Minimal Upgrade (Recommended)

Install the 3 essential SDKs:

```bash
pip install anthropic>=0.40.0 google-generativeai>=0.8.0 cohere>=5.11.0
```

**Time:** 5 minutes to install, 1-2 hours to refactor
**Benefit:** Much better developer experience, fewer bugs

### Full Upgrade (If Building Production App)

Install all SDKs + LangChain:

```bash
pip install anthropic>=0.40.0 google-generativeai>=0.8.0 cohere>=5.11.0 \
            mistralai>=1.2.0 groq>=0.11.0 \
            langchain>=0.3.0 langchain-openai>=0.2.0 \
            langchain-anthropic>=0.3.0 langchain-google-genai>=2.0.0
```

**Time:** 10 minutes to install, 4-6 hours to refactor
**Benefit:** Production-ready, scalable, maintainable

---

## Next Steps

1. **Decide on upgrade level** (minimal vs full)
2. **Install SDKs**
3. **Refactor llm_clients.py** to use official SDKs
4. **Update tests** to verify everything works
5. **Update documentation**

---

## Questions to Consider

1. **Are you building a production app?** → Full upgrade
2. **Just experimenting?** → Minimal upgrade
3. **Need advanced features (agents, chains)?** → Add LangChain
4. **Need monitoring/observability?** → Add OpenTelemetry
5. **Want automatic fallbacks?** → Add LiteLLM

---

**Recommendation:** Start with the **minimal upgrade** (3 essential SDKs), then add LangChain later if needed.
