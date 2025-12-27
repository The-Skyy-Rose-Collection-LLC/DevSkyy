# LLM Clients Quick Start Guide

Get started with DevSkyy's 6 LLM provider clients in minutes.

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:

- `httpx` - HTTP client
- `pydantic` - Data validation
- `tenacity` - Retry logic

### 2. Set API Keys

Choose the providers you want to use and set their API keys:

```bash
# OpenAI (GPT-4o, o1)
export OPENAI_API_KEY="sk-..."

# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# Google (Gemini)
export GOOGLE_API_KEY="..."

# Mistral
export MISTRAL_API_KEY="..."

# Cohere (Command R)
export COHERE_API_KEY="..."

# Groq (Fast Llama/Mixtral)
export GROQ_API_KEY="gsk_..."
```

### 3. Verify Installation

```bash
python3 scripts/verify_llm_clients.py
```

---

## Basic Usage

### Simple Completion

```python
import asyncio
from orchestration import OpenAIClient, Message, MessageRole

async def main():
    # Initialize client
    client = OpenAIClient()

    # Create message
    messages = [
        Message(role=MessageRole.USER, content="What is Python?")
    ]

    # Get completion
    response = await client.complete(messages=messages, model="gpt-4o-mini")

    # Print result
    print(response.content)
    print(f"Tokens used: {response.total_tokens}")
    print(f"Latency: {response.latency_ms:.0f}ms")

    # Close client
    await client.close()

asyncio.run(main())
```

### Using Different Providers

```python
from orchestration import (
    OpenAIClient,
    AnthropicClient,
    GoogleClient,
    MistralClient,
    CohereClient,
    GroqClient,
)

# OpenAI
client = OpenAIClient()
response = await client.complete(messages, model="gpt-4o")

# Anthropic
client = AnthropicClient()
response = await client.complete(messages, model="claude-3-5-sonnet-20241022")

# Google
client = GoogleClient()
response = await client.complete(messages, model="gemini-1.5-flash")

# Mistral
client = MistralClient()
response = await client.complete(messages, model="mistral-large-latest")

# Cohere
client = CohereClient()
response = await client.complete(messages, model="command-r-plus")

# Groq (Fast!)
client = GroqClient()
response = await client.complete(messages, model="llama-3.1-70b-versatile")
```

---

## Intelligent Orchestration

Let the orchestrator choose the best model for your task:

```python
from orchestration import LLMOrchestrator, TaskType

async def main():
    orchestrator = LLMOrchestrator()

    # Code generation - automatically uses Claude 3.5 Sonnet
    result = await orchestrator.complete(
        prompt="Write a Python function to sort a list",
        task_type=TaskType.CODE_GENERATION
    )

    # Reasoning - automatically uses o1-preview
    result = await orchestrator.complete(
        prompt="Solve this logic puzzle...",
        task_type=TaskType.REASONING
    )

    # Fast chat - automatically uses Llama 3.1 8B on Groq
    result = await orchestrator.complete(
        prompt="Hello!",
        task_type=TaskType.REAL_TIME
    )

    print(f"Model used: {result.model}")
    print(f"Content: {result.content}")

asyncio.run(main())
```

---

## Streaming Responses

```python
async def stream_example():
    client = OpenAIClient()

    messages = [
        Message(role=MessageRole.USER, content="Tell me a story")
    ]

    print("Streaming response: ", end="", flush=True)

    async for chunk in client.stream(messages=messages, model="gpt-4o-mini"):
        print(chunk.content, end="", flush=True)

    print()  # New line
    await client.close()

asyncio.run(stream_example())
```

---

## Advanced Features

### Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

response = await client.complete(
    messages=[Message(role=MessageRole.USER, content="What's the weather in SF?")],
    model="gpt-4o",
    tools=tools
)

if response.tool_calls:
    print(f"Tool called: {response.tool_calls[0].function}")
```

### JSON Mode

```python
response = await client.complete(
    messages=[Message(role=MessageRole.USER, content="List 3 colors")],
    model="gpt-4o-mini",
    response_format={"type": "json_object"}
)

import json
data = json.loads(response.content)
print(data)
```

### Temperature Control

```python
# Creative (high temperature)
response = await client.complete(
    messages=messages,
    model="gpt-4o",
    temperature=0.9
)

# Deterministic (low temperature)
response = await client.complete(
    messages=messages,
    model="gpt-4o",
    temperature=0.1
)
```

---

## Model Selection Guide

| Task | Recommended Model | Provider | Why |
|------|------------------|----------|-----|
| Code Generation | `claude-3-5-sonnet-20241022` | Anthropic | Best at coding |
| Reasoning/Math | `o1-preview` | OpenAI | Advanced reasoning |
| Vision/Images | `gpt-4o` | OpenAI | Multimodal |
| Long Documents | `gemini-1.5-pro` | Google | 2M context |
| Fast Chat | `llama-3.1-8b-instant` | Groq | Ultra-low latency |
| RAG/Search | `command-r-plus` | Cohere | Grounded generation |
| General Chat | `gpt-4o-mini` | OpenAI | Best balance |

---

## Error Handling

All clients have automatic retry logic with exponential backoff:

```python
from tenacity import RetryError

try:
    response = await client.complete(messages=messages)
except RetryError as e:
    print(f"Failed after retries: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Best Practices

1. **Always close clients** when done:

   ```python
   await client.close()
   ```

2. **Use the orchestrator** for automatic model selection:

   ```python
   orchestrator = LLMOrchestrator()
   result = await orchestrator.complete(prompt, task_type=TaskType.CODE_GENERATION)
   ```

3. **Set appropriate timeouts**:

   ```python
   client = OpenAIClient(timeout=30.0)
   ```

4. **Monitor token usage**:

   ```python
   print(f"Tokens: {response.total_tokens}")
   print(f"Cost: ${response.total_tokens * 0.00001}")  # Approximate
   ```

5. **Use streaming for long responses**:

   ```python
   async for chunk in client.stream(messages):
       print(chunk.content, end="")
   ```

---

## Troubleshooting

### "No module named 'tenacity'"

```bash
pip install tenacity
```

### "API key not found"

```bash
export OPENAI_API_KEY="your-key-here"
```

### "Connection timeout"

```python
client = OpenAIClient(timeout=60.0)  # Increase timeout
```

### Check available providers

```python
from orchestration import LLMRegistry

registry = LLMRegistry()
available = registry.get_available_providers()
print(f"Available: {available}")
```

---

## Next Steps

- Read the full integration report: `LLM_CLIENTS_INTEGRATION_REPORT.md`
- Explore the orchestrator: `orchestration/llm_orchestrator.py`
- Check model registry: `orchestration/llm_registry.py`
- Run verification: `python3 scripts/verify_llm_clients.py`

---

**Happy coding with 6 LLM providers!** 🚀
