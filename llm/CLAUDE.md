# DevSkyy LLM

> Multi-provider, cost-optimized | 27 files

## Architecture
```
llm/
├── router.py              # Smart provider routing
├── round_table.py         # Multi-LLM consensus
├── ab_testing.py          # A/B experiments
├── providers/             # anthropic, openai, google, mistral, groq
└── prompts/techniques.py  # 17 prompt techniques
```

## Pattern
```python
class LLMRouter:
    async def route(self, prompt: str, task_type: TaskType, *, correlation_id: str | None = None):
        scores = await self._score_providers(task_type)
        provider = self._select_provider(scores)
        return await self._execute_with_fallback(provider, prompt, correlation_id)

class RoundTable:
    async def deliberate(self, topic: str) -> Consensus:
        responses = await asyncio.gather(*[p.complete(topic) for p in self.providers])
        return self._synthesize_consensus(responses)
```

## Providers
Anthropic (Claude) | OpenAI (GPT) | Google (Gemini) | Mistral | Groq

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
- **MCP**: `llm_route` for routing
- **Skill**: `backend-patterns` for async patterns

**"One prompt. Many models. Best answer wins."**
