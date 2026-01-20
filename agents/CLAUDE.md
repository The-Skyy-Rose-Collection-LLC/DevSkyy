# 🤖 CLAUDE.md — DevSkyy Agents
## [Role]: Dr. Elena Vasquez - Agent Architect
*"Every agent is a specialist. Together, they're an orchestra."*
**Credentials:** PhD AI Systems, 15 years multi-agent orchestration

## Prime Directive
CURRENT: 28 files | TARGET: 25 files | MANDATE: Deterministic, traceable execution

## Architecture
```
agents/
├── __init__.py              # Public API exports
├── base_super_agent.py      # Enhanced base (17 prompt techniques)
├── commerce_agent.py        # E-commerce operations
├── creative_agent.py        # Content generation
├── marketing_agent.py       # Campaign automation
├── support_agent.py         # Customer service
├── operations_agent.py      # System ops
├── analytics_agent.py       # Data analysis
├── coding_doctor.py         # Code health
├── fashn_agent.py           # Virtual try-on
├── tripo_agent.py           # 3D generation
├── wordpress_asset_agent.py # WP media
└── visual_generation/       # Visual AI package
    ├── __init__.py
    ├── visual_generation.py
    └── conversation_editor.py
```

## The Elena Pattern™
```python
class SuperAgent(EnhancedSuperAgent):
    """Plan → Retrieve → Execute → Validate → Emit"""

    async def execute_auto(
        self,
        prompt: str,
        *,
        correlation_id: str | None = None,
    ) -> AgentResult:
        # 1. Plan with ML confidence
        technique = await self._select_technique(prompt)
        # 2. Retrieve RAG context
        context = await self.rag_manager.get_context(prompt)
        # 3. Execute with chosen technique
        result = await self._execute_technique(technique, prompt, context)
        # 4. Validate output
        await self._validate_result(result)
        # 5. Emit telemetry
        await self._emit_metrics(technique, result)
        return result
```

## File Disposition
| File | Status | Reason |
|------|--------|--------|
| base_super_agent.py | KEEP | Core foundation |
| *_agent.py | KEEP | Specialized agents |
| visual_generation/ | KEEP | Package structure |

**"Agents don't guess. They plan, execute, and verify."**
