# DevSkyy Agents

> Deterministic, traceable execution | 28 files

## Architecture
```
agents/
├── base_super_agent.py      # Enhanced base (17 prompt techniques)
├── commerce_agent.py        # E-commerce operations
├── creative_agent.py        # Content generation
├── marketing_agent.py       # Campaign automation
├── support_agent.py         # Customer service
├── analytics_agent.py       # Data analysis
├── fashn_agent.py           # Virtual try-on
├── tripo_agent.py           # 3D generation
└── visual_generation/       # Visual AI package
```

## Pattern
```python
class SuperAgent(EnhancedSuperAgent):
    """Plan → Retrieve → Execute → Validate → Emit"""
    async def execute_auto(self, prompt: str, *, correlation_id: str | None = None) -> AgentResult:
        technique = await self._select_technique(prompt)
        context = await self.rag_manager.get_context(prompt)
        result = await self._execute_technique(technique, prompt, context)
        await self._validate_result(result)
        return result
```

## Related
- **MCP**: `agent_orchestrator` for routing
- **Skill**: `~/.claude/agents/` for Claude Code agents

**"Agents don't guess. They plan, execute, and verify."**
