---
name: Research and Documentation
description: This skill should be used when the user asks to "research documentation", "find API references", "take notes", "cite sources", "document findings", "search official docs", or needs authenticated information about libraries, frameworks, or DevSkyy components.
version: 1.0.0
---

# Research and Documentation Skill

Use this skill when researching technical documentation, taking structured notes,
and providing cited sources for DevSkyy development.

## When to Use This Skill

Invoke this skill when the user:

- Needs to research external APIs, libraries, or frameworks
- Asks for official documentation or API references
- Wants to document findings or create technical notes
- Requests authenticated sources for implementation decisions
- Mentions Context7, documentation search, or citation requirements
- Needs to understand DevSkyy component architecture

## Research Workflow

### Step 1: Identify Information Need

```python
research_query = {
    "topic": "Tripo3D API authentication",
    "purpose": "Implement 3D generation in agent",
    "sources_needed": ["official_docs", "api_reference"],
    "output_format": "implementation_guide"
}
```

### Step 2: Query Context7 for Documentation

Use Context7 MCP plugin for up-to-date documentation:

```python
# 1. Resolve library ID
library_id = await context7.resolve_library_id(
    libraryName="Tripo3D",
    query="3D model generation API documentation"
)

# 2. Query documentation
docs = await context7.query_docs(
    libraryId=library_id,
    query="How to authenticate and generate 3D models from text prompts"
)
```

### Step 3: Take Structured Notes

Create memory file with findings:

```markdown
# Tripo3D API Research

## Authentication
- API Key: Required in Authorization header
- Format: `Bearer {api_key}`
- Endpoint: `https://api.tripo3d.ai/v1/`

## Text-to-3D Generation
**Endpoint**: `POST /generate`

**Parameters**:
- `prompt` (string, required): Description of 3D model
- `style` (string): realistic|cartoon|low_poly
- `output_format` (string): glb|obj|fbx

**Response**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "model_url": "https://..."
}
```

## Sources

- [Tripo3D Official API Docs](https://docs.tripo3d.ai/api)
- Retrieved: 2026-01-07
- Context7 Library ID: /tripo3d/api

## Implementation Notes

- Add retry logic for long-running generation
- Validate polycount < 100k for web use
- Cache generated models in WordPress media library

```

### Step 4: Document in Serena Memory

```python
await serena.write_memory(
    memory_file_name="tripo3d_api_integration",
    content=research_notes
)
```

## Documentation Templates

### API Reference Template

```markdown
# {Library Name} API Reference

## Overview
Brief description of what this API does and when to use it.

## Authentication
- Method: API Key / OAuth / JWT
- Header format
- Environment variable name

## Endpoints

### {Endpoint Name}
**URL**: `{METHOD} /endpoint/path`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | string | yes | What it does |
| param2 | number | no | Optional param |

**Example Request**:
```bash
curl -X POST https://api.example.com/v1/endpoint \
  -H "Authorization: Bearer {API_KEY}" \
  -d '{"param1": "value"}'
```

**Example Response**:

```json
{
  "status": "success",
  "data": {}
}
```

## Error Handling

- 400: Bad Request - Check parameters
- 401: Unauthorized - Check API key
- 429: Rate Limited - Implement backoff
- 500: Server Error - Retry with exponential backoff

## Rate Limits

- Requests per minute: X
- Daily quota: Y

## Sources

- [Official Documentation](https://...)
- Retrieved: {date}
- Context7 ID: /{org}/{project}

```

### Component Documentation Template

```markdown
# {Component Name}

## Purpose
What this component does and why it exists.

## Architecture
High-level design and dependencies.

## Usage

### Basic Example
```python
from path.to.component import Component

component = Component(config)
result = await component.execute(input)
```

### Advanced Example

```python
# More complex usage with options
```

## API Reference

### Class: {ClassName}

**Location**: `path/to/file.py`

**Constructor Parameters**:

- `param1` (type): Description
- `param2` (type, optional): Description

**Methods**:

- `method_name(args) -> return_type`: What it does

## Integration Points

- Works with: {other components}
- Triggers events: {event names}
- Consumes data from: {data sources}

## File Locations

- Main file: `path/to/main.py`
- Tests: `tests/test_component.py`
- Examples: `examples/component_example.py`

## Testing

```python
@pytest.mark.asyncio
async def test_component():
    ...
```

## Related Documentation

- See also: {related docs}
- Dependencies: {external libraries}

```

## Research Best Practices

### 1. Always Cite Sources

```markdown
## Sources
- [Library Official Docs](https://example.com/docs) - Retrieved 2026-01-07
- [GitHub Repository](https://github.com/org/repo) - Commit abc123
- [Context7 Library](/org/project) - Version 2.1.0
- [Stack Overflow Discussion](https://stackoverflow.com/...) - Verified solution
```

### 2. Version Tracking

```markdown
## Version Information
- Library Version: 2.1.0
- Tested With: DevSkyy 1.0.0
- Last Verified: 2026-01-07
- Breaking Changes: None since 2.0.0
```

### 3. Implementation Notes

```markdown
## Implementation Considerations
- ⚠️ Rate limits: 100 req/min
- ✅ Supports async/await
- ❌ No batch operations
- 💡 Use caching for repeated calls
- 🔒 Requires API key in environment
```

## Context7 Integration

### Resolve Library ID

```python
# Always resolve library ID first
result = await context7.resolve_library_id(
    libraryName="Next.js",
    query="Server components and app router documentation"
)

# Result includes multiple matches, select best:
# - Name similarity (exact match prioritized)
# - Description relevance
# - Documentation coverage (snippet count)
# - Source reputation (High > Medium > Low)
# - Benchmark score (quality indicator)

selected_library = result.matches[0]["library_id"]  # e.g., "/vercel/next.js"
```

### Query Documentation

```python
# Query with specific, detailed questions
docs = await context7.query_docs(
    libraryId="/vercel/next.js",
    query="""
    How to implement server-side data fetching in Next.js 15 App Router?
    Include examples of async Server Components, data caching strategies,
    and error handling patterns.
    """
)

# IMPORTANT: Do not include sensitive information in queries:
# ❌ Don't include: API keys, passwords, credentials, personal data
# ✅ Do include: Technical concepts, patterns, feature names
```

### Citation Format

```markdown
## Sources
- **Next.js Documentation**: Server Components
  - Context7 ID: `/vercel/next.js`
  - Retrieved: 2026-01-07 via Context7
  - Relevant sections: "Data Fetching", "Server Components"
  - Code examples: Async component patterns, `fetch()` with caching
```

## DevSkyy Component Research

### Agent Architecture

Research pattern for understanding agents:

```python
# 1. Read agent file
agent_code = await serena.read_file("agents/commerce_agent.py")

# 2. Get symbol overview
symbols = await serena.get_symbols_overview("agents/commerce_agent.py")

# 3. Find specific methods
method = await serena.find_symbol(
    name_path_pattern="CommerceAgent/execute_task",
    relative_path="agents/commerce_agent.py",
    include_body=True
)

# 4. Find references
references = await serena.find_referencing_symbols(
    name_path="CommerceAgent/execute_task",
    relative_path="agents/commerce_agent.py"
)

# 5. Document findings
notes = f"""
# CommerceAgent Research

## Purpose
{extract_purpose_from_docstring(agent_code)}

## Key Methods
{format_methods(symbols)}

## Usage Pattern
{analyze_references(references)}

## Integration Points
{identify_dependencies(agent_code)}
"""

await serena.write_memory("commerce_agent_architecture", notes)
```

### MCP Tool Research

```python
# Research MCP tool implementation
tool_code = await serena.read_file("devskyy_mcp.py")

# Search for specific tool
tool_pattern = await serena.search_for_pattern(
    substring_pattern="@mcp\\.tool.*devskyy_generate_3d",
    paths_include_glob="devskyy_mcp.py"
)

# Document tool schema
tool_doc = """
# 3D Generation MCP Tool

## Tool Name
`devskyy_generate_3d_from_description`

## Input Schema
- prompt: str (required)
- style: str (optional, default: "realistic")
- output_format: str (optional, default: "glb")

## Implementation
Location: `devskyy_mcp.py` lines 245-280

## Dependencies
- TripoAgent from agents/tripo_agent.py
- ThreeDAssetPipeline from agents/visual_generation.py

## Usage Example
See examples/3d_generation_example.py
"""
```

## Memory Management

### Create Research Memory

```python
await serena.write_memory(
    memory_file_name="research_topic_name",
    content=markdown_formatted_notes
)
```

### Read Existing Research

```python
# List available memories
memories = await serena.list_memories()

# Read specific memory
notes = await serena.read_memory("research_topic_name")
```

### Update Research

```python
# Edit existing memory
await serena.edit_memory(
    memory_file_name="research_topic_name",
    needle="## Implementation Notes",
    repl="## Implementation Notes\n- Updated finding: New pattern discovered",
    mode="literal"
)
```

## File Locations

- **Context7 Plugin**: MCP plugin (auto-loaded)
- **Serena Memory Tools**: MCP plugin (auto-loaded)
- **Research Memories**: `.serena/memories/`
- **Documentation**: `docs/` directory

## Research Checklist

When documenting findings:

- [ ] Cite all sources with URLs and retrieval dates
- [ ] Include version information for libraries
- [ ] Provide working code examples
- [ ] Document error handling patterns
- [ ] Note rate limits and constraints
- [ ] Add implementation warnings
- [ ] Cross-reference related documentation
- [ ] Test all code examples
- [ ] Save to Serena memory for future reference
- [ ] Link to official documentation

## Common Research Patterns

### Pattern 1: New API Integration

```markdown
1. Query Context7 for official documentation
2. Document authentication method
3. List key endpoints with examples
4. Note rate limits and constraints
5. Create code examples
6. Test integration
7. Document in memory
8. Create agent integration pattern
```

### Pattern 2: Framework Update Research

```markdown
1. Check current version in package.json
2. Query Context7 for new version docs
3. Identify breaking changes
4. List migration steps
5. Update code examples
6. Test compatibility
7. Document findings
8. Create migration guide
```

### Pattern 3: Component Deep Dive

```markdown
1. Read component source code
2. Get symbol overview
3. Find all references
4. Understand data flow
5. Document architecture
6. Create usage examples
7. Identify optimization opportunities
8. Save findings to memory
```

## Next Steps

1. **Identify** research needs for current task
2. **Query** Context7 for relevant documentation
3. **Document** findings in structured format
4. **Cite** all sources with retrieval dates
5. **Test** all code examples
6. **Save** to Serena memory
7. **Share** findings with team

## References

See `references/` directory for:

- Context7 usage guide
- Documentation templates
- Citation formats
- Research workflow examples
- Memory management patterns
- DevSkyy component map
