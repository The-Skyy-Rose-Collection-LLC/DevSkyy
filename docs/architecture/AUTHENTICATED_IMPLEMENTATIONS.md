# Authenticated Industry Implementations Reference

**Document Version:** 1.0.0
**Research Date:** December 17-18, 2025
**Purpose:** Document industry-proven implementations for production hardening

---

## 1. Model Context Protocol (MCP)

### Official Specification

- **Protocol Version:** 2025-11-25 (Current)
- **Transport:** JSON-RPC 2.0 over stdio/HTTP+SSE
- **Schema:** [GitHub - modelcontextprotocol/specification](https://github.com/modelcontextprotocol/specification)

### Core Primitives

| Primitive | Direction | Description |
|-----------|-----------|-------------|
| Tools | Server → Client | Executable functions LLMs can call |
| Resources | Server → Client | Data/content providers |
| Prompts | Server → Client | Pre-defined prompt templates |
| Roots | Client → Server | File system access points |
| Sampling | Client → Server | LLM inference requests |

### Tool Schema (from official schema.json)

```json
{
  "CallToolRequestParams": {
    "properties": {
      "name": { "type": "string", "description": "The name of the tool" },
      "arguments": { "type": "object", "description": "Arguments for the tool call" },
      "_meta": { "type": "object", "properties": { "progressToken": {} } }
    },
    "required": ["name"]
  },
  "CallToolResult": {
    "properties": {
      "content": { "type": "array", "items": { "$ref": "#/$defs/ContentBlock" } },
      "isError": { "type": "boolean" },
      "structuredContent": { "type": "object" }
    },
    "required": ["content"]
  }
}
```

### Key November 2025 Updates

- Tool calling in sampling requests
- Server-side agent loops
- Parallel tool calls support
- Donated to Agentic AI Foundation (Linux Foundation) - December 2025

### Sources

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [MCP GitHub Specification](https://github.com/modelcontextprotocol/specification)
- [Anthropic MCP Announcement](https://www.anthropic.com/news/model-context-protocol)
- [One Year of MCP Blog Post](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)

---

## 2. LangChain Tool Calling (2025)

### Standard Interface

```python
# ChatModel.bind_tools() - Universal interface for all tool-calling models
model_with_tools = model.bind_tools([tool1, tool2])

# Provider-specific schema differences:
# OpenAI: {"name", "description", "parameters"}
# Anthropic: {"name", "description", "input_schema"}
```

### Tool Definition Methods

1. **@tool decorator** - Simple tools with automatic schema generation
2. **BaseTool subclass** - Advanced tools with custom initialization, async operations

### ToolRuntime (NEW in 2025)

```python
# Unified parameter providing access to:
# - state: Current workflow state
# - context: Execution context
# - store: Persistent storage
# - streaming: Stream handlers
# - config: Configuration
# - tool_call_id: Unique call identifier
```

### Standardized Tool Calls

```python
# AIMessage.tool_calls provides standardized interface across providers
# Replaces provider-specific AIMessage.additional_kwargs / AIMessage.content
```

### Production Patterns

- LangGraph for production agents (stateful graph architecture)
- Human-in-the-loop interrupts
- Time-travel debugging
- Checkpointing with PostgresSaver/SqliteSaver

### Sources

- [LangChain Tools Documentation](https://docs.langchain.com/oss/python/langchain/tools)
- [Tool Calling with LangChain Blog](https://blog.langchain.com/tool-calling-with-langchain/)
- [LangGraph Platform GA Announcement](https://blog.langchain.com/langgraph-platform-ga/)

---

## 3. OpenAI Function Calling

### Function Schema Structure

```json
{
  "name": "function_name",
  "description": "What the function does",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": { "type": "string", "description": "..." }
    },
    "required": ["param1"]
  }
}
```

### Structured Outputs (2025)

- Model guarantees responses adhere to supplied JSON Schema
- SDK support: Pydantic (Python), Zod (JavaScript)
- **Not supported:** allOf, not, dependentRequired, if/then/else composition

### Response Format

```json
{
  "type": "function_call",
  "call_id": "unique_id",
  "name": "function_name",
  "arguments": "{\"param1\": \"value\"}"  // JSON-encoded string
}
```

### Sources

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)

---

## 4. AES-256-GCM Cryptography (OWASP/NIST)

### OWASP Recommendations

| Requirement | Specification |
|-------------|---------------|
| Algorithm | AES-GCM (authenticated encryption) |
| Key Size | Minimum 128-bit, preferably 256-bit |
| Mode | GCM (Galois/Counter Mode) - provides confidentiality + integrity + authenticity |
| IV/Nonce | 96-bit, NEVER reuse, set to maximum values |
| Key Derivation | Use KDF (scrypt/PBKDF2), NOT direct passwords |

### Avoid List (NIST/OWASP)

- MD5, SHA-1 for passwords
- RC4, DES, 3DES
- Custom/homegrown crypto
- Outdated SSL/TLS versions
- IV/nonce reuse
- Hard-coded keys

### Python Libraries

```python
# Recommended: cryptography library
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# For high-level encryption: Fernet (AES-128-CBC + HMAC-SHA256)
from cryptography.fernet import Fernet

# Key derivation
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
```

### Sources

- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST SP 800-38D (GCM)](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- [Python Cryptography Documentation](https://cryptography.io/en/latest/)

---

## 5. Three.js Production Optimization (2025)

### Performance Techniques

| Technique | Benefit |
|-----------|---------|
| Lower resolution for high-DPI | Reduce GPU load |
| Texture atlases | -30% draw calls |
| DRACO mesh compression | <10% of original file size |
| KTX2/Basis textures | GPU-ready, reduced memory |
| Occlusion culling | +50% rendering efficiency |
| WebGPU (where supported) | +30% rendering speed vs WebGL |

### Asset Optimization

```bash
# glTF Transform commands
gltf-transform draco input.glb output.glb
gltf-transform uastc input.glb output.glb --level 4
gltf-transform webp input.glb output.glb
```

### WebGL Context Loss Handling

- Common with multiple WebGL contexts (React re-renders)
- Large models (30MB+) can trigger context loss
- Implement explicit `webglcontextlost` / `webglcontextrestored` event handlers

### Best Practices

```javascript
// Avoid shader recompilation
light.visible = false;  // Good
scene.remove(light);    // Bad - causes recompile

// OffscreenCanvas + Web Workers for complex scenes
const offscreen = canvas.transferControlToOffscreen();
worker.postMessage({ canvas: offscreen }, [offscreen]);
```

### Sources

- [Codrops - Building Efficient Three.js Scenes](https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/)
- [Three.js Journey - Performance Tips](https://threejs-journey.com/lessons/performance-tips)
- [Evil Martians - OffscreenCanvas + Web Workers](https://evilmartians.com/chronicles/faster-webgl-three-js-3d-graphics-with-offscreencanvas-and-web-workers)

---

## 6. RAG Production Architecture (2025)

### Market Context

- $1.85B market in 2024, 49% CAGR growth
- 60-80% cheaper than fine-tuning via document retrieval

### Modular Architecture Pattern

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Retriever  │ → │ Orchestrator │ → │  Generator  │
└─────────────┘    └─────────────┘    └─────────────┘
      ↑                  ↑
      │                  │
┌─────────────┐    ┌─────────────┐
│Vector Store │    │   Context   │
└─────────────┘    └─────────────┘
```

### Hybrid Retrieval Strategy

```python
# Combine BM25 keyword + dense embeddings
results = (
    bm25_retriever.retrieve(query, k=10) +
    dense_retriever.retrieve(query, k=10)
)
# Re-rank combined results
final_results = reranker.rerank(query, results, k=5)
```

### Production Challenges

1. Retrieval quality
2. Privacy concerns
3. Integration overhead
4. Latency optimization

### Emerging Patterns

- GraphRAG (knowledge graph augmented)
- Agentic RAG (multi-step reasoning)
- Self-RAG (self-reflection)
- Corrective RAG (retrieval validation)

### Sources

- [Pinecone - RAG Guide](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [orq.ai - RAG Architecture 2025](https://orq.ai/blog/rag-architecture)
- [Springer - RAG Research Paper](https://link.springer.com/article/10.1007/s12599-025-00945-3)

---

## 7. glTF/DRACO/KTX2 Pipeline (2025)

### Compression Tools

| Tool | Purpose |
|------|---------|
| glTF Transform | CLI for mesh + texture optimization |
| gltf-pipeline (CesiumGS) | Draco compression |
| gltfpack | KTX2 + meshopt compression |

### KTX2 Compression Methods

| Method | Use Case |
|--------|----------|
| ETC1S | Greater compression, solid colors |
| UASTC | Higher quality, larger size |

### Runtime Benefits

- GPU-ready texture upload
- Reduced memory consumption vs JPEG/PNG/WebP
- Cross-platform transcoding (BC7/ETC/ASTC)

### Sources

- [glTF Transform](https://gltf-transform.dev/)
- [CesiumGS gltf-pipeline](https://github.com/CesiumGS/gltf-pipeline)
- [Khronos KTX Artist Guide](https://github.com/KhronosGroup/3D-Formats-Guidelines/blob/main/KTXArtistGuide.md)

---

## 8. Pydantic v2 Validation (2025)

### Current Version: v2.12.5

### Validation Patterns

```python
# TypedDict for performance (less overhead than BaseModel)
from typing import TypedDict
from pydantic import TypeAdapter

class ToolCallDict(TypedDict):
    name: str
    arguments: dict

adapter = TypeAdapter(ToolCallDict)
validated = adapter.validate_python(data)

# Pydantic Dataclasses
from pydantic.dataclasses import dataclass

@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict
```

### Validator Types

1. **After validators** - Run after Pydantic's internal validation (recommended)
2. **Before validators** - Run before type coercion
3. **Wrap validators** - Full control (avoid for performance)
4. **Plain validators** - Replace Pydantic validation entirely

### Performance Tips

- Use TypedDict over nested models
- FailFast annotation (v2.8+) for sequences
- Avoid wrap validators for hot paths

### Sources

- [Pydantic Documentation](https://docs.pydantic.dev/latest/)
- [Pydantic Validators Guide](https://docs.pydantic.dev/latest/concepts/validators/)

---

## 9. LangGraph Production Architecture (2025)

### Core Concepts

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: dict

graph = StateGraph(AgentState)
```

### Checkpointing

```python
# Development: MemorySaver (in-memory, non-persistent)
from langgraph.checkpoint.memory import MemorySaver

# Production: PostgresSaver or SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver
```

### Key Features

1. Parallelization
2. Streaming
3. Checkpointing
4. Human-in-the-loop
5. Tracing
6. Task queue

### Production Users

- LinkedIn, Uber, Klarna
- ~400 companies on LangGraph Platform

### Sources

- [LangGraph Documentation](https://www.langchain.com/langgraph)
- [Building LangGraph Blog](https://blog.langchain.com/building-langgraph/)

---

## 10. WordPress/Elementor Production Patterns (2025)

### REST API Best Practices

```php
// Input sanitization
sanitize_text_field($input);
sanitize_email($email);
sanitize_url($url);

// Authentication required for sensitive endpoints
add_action('rest_api_init', function() {
    register_rest_route('namespace/v1', '/endpoint', [
        'permission_callback' => function() {
            return current_user_can('edit_posts');
        }
    ]);
});
```

### Headless WordPress Architecture

```
WordPress Backend (CMS)
         ↓
    REST API / GraphQL
         ↓
Frontend (React/Vue/Next.js)
```

### Elementor Developer APIs

- Locations API for theme control
- Hello Theme as minimal base
- Widget/Extension development standards

### Sources

- [Elementor Developer Documentation](https://developers.elementor.com/)
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Elementor Headless WordPress Guide](https://elementor.com/blog/headless-wordpress/)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-18 | Initial authenticated research documentation |

---

**Next Steps:**

1. Implement Tool Runtime layer based on MCP + LangChain patterns
2. Apply AES-256-GCM best practices to existing crypto module
3. Implement Three.js collection experiences with DRACO/KTX2
4. Integrate LangGraph checkpointing for agent state management
