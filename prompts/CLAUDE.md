<claude-mem-context>

</claude-mem-context>

# prompts/ — DevSkyy centralized prompt engineering library

Single Python package serving prompts to all 54 agents across DevSkyy. Houses the COSTARD + Constitutional AI base, per-agent specialty prompts, and a technique engine that auto-selects reasoning strategy by task type.

## Key files

- `base_system_prompt.py` — `BaseSystemPrompt` dataclass implementing the COSTARD framework (Context, Objective, Style, Tone, Audience, Response format) plus Constitutional AI self-critique and OpenAI Six-Strategy (role, step-by-step, examples, criteria, iteration, personas). All 54 agents inherit this base — never duplicate these fields in a subclass.
- `agent_prompts.py` — Per-agent specialty prompts organized by category: Backend (45 agents), Frontend (9 agents), AI Intelligence, Security, E-commerce, Analytics. Import the relevant `*_SYSTEM_PROMPT` constant; do not define new system prompts outside this file.
- `technique_engine.py` — Classifies the incoming task type and auto-selects the reasoning technique: CoT (chain-of-thought for debugging/code), ToT (tree-of-thoughts for architecture), Few-Shot (product descriptions/SEO), Constitutional (brand copy/security review), Self-Consistency (ambiguous requirements). Called by agents before constructing the final user message.
- `rag_mcp_hybrid.py` — Retrieves Pinecone context (catalog embeddings, brand voice) and MCP tool results, then injects them into the **user message** — not the system prompt. RAG context appended as a `[CONTEXT]` block at the bottom of the human turn.
- `chain_orchestrator.py` — Multi-step chain runner: executes a sequence of prompt steps, retries on malformed outputs (up to 3 attempts), collects intermediate outputs for the next step.
- `meta_prompts.py` — Prompt-about-prompt generation: produces optimized system prompt variants given a task description and scoring criteria.
- `task_templates.py` — Structured Jinja2 templates: `product_description`, `seo_copy`, `3d_brief`, `wc_import_row`. Render these before passing to an LLM — do not hand-craft these strings inline in agent code.

## Conventions

- All agents import from `prompts` — never define a system prompt string inside an agent file. Keep prompts and agent logic separated.
- RAG context goes in the user message, not the system prompt. The system prompt is stable across requests; the user message carries the dynamic context.
- `technique_engine.py` runs before every LLM call in the chain — let it choose the technique unless the agent overrides explicitly with `force_technique=`.
- New per-agent prompts go in `agent_prompts.py` under the correct category section. Match the naming convention: `{CATEGORY}_{ROLE}_SYSTEM_PROMPT`.
- `task_templates.py` templates are Jinja2 — render with `template.render(**kwargs)`. Add new templates here; do not duplicate template logic in scripts.

## Don't

- Don't define system prompt strings inside agent files — `agent_prompts.py` is the single source of truth.
- Don't inject RAG context into the system prompt — it makes the system prompt non-cacheable and increases latency.
- Don't call `chain_orchestrator.py` with more than 10 steps — chains beyond that exceed the context budget for Haiku models.
- Don't add COSTARD fields to a subclass if `BaseSystemPrompt` already covers them — override only what differs.

## Related

- `agents/` — all agents that import from this package
- `orchestration/` — LangGraph/CrewAI workflows that compose chains from `chain_orchestrator.py`
- `llm/` — provider clients called with the prompts this package produces
- `database/` — Pinecone vector store queried by `rag_mcp_hybrid.py`
