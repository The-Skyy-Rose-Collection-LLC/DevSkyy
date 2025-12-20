# DevSkyy - Claude Code Configuration

> **Principal Engineer Instructions for Production-Grade Enterprise AI Platform**
> This file is automatically loaded into Claude Code context. Keep it concise and actionable.

---

## 🎯 Project Mission

Transform DevSkyy from B+ (52/100) → A+ (90+/100) enterprise readiness through:
- **Security hardening** (zero vulnerabilities already achieved)
- **API versioning** implementation
- **GDPR compliance** modules
- **Production deployment** readiness
- **Elimination of ALL stubs/placeholders/TODOs**

**CRITICAL**: This is NOT a demo. Every implementation must be production-ready, fully tested, with explicit contracts.

---

## 🔒 ABSOLUTE RULES (NON-NEGOTIABLE)

1. **Correctness > Elegance > Performance**
   - Resolve ambiguity explicitly, never assume intent
   - Encode all behavior; no "magic"

2. **No Feature Deletions**
   - Refactor/formalize/harden - YES
   - Remove capabilities (agents, MCP, RAG, 3D, security, WordPress, Elementor) - NO

3. **Truthful Codebase**
   - README/versioning/license must reflect reality
   - "Production-ready" requires tests + CI enforcement

4. **Deterministic Agent Behavior**
   - No silent fallbacks, no magic strings
   - Every agent action: traceable, validated, testable

5. **Explicit Contracts Everywhere**
   - Inputs validated (Pydantic)
   - Outputs typed
   - Errors classified
   - Side effects documented

6. **Interface Changes Protocol**
   - Update ALL call sites
   - Update ALL tests
   - Document breaks clearly

---

## 🏗️ Repository Structure

```
/home/runner/work/DevSkyy/DevSkyy/
├── Root Files
│   ├── devskyy_mcp.py            # Main MCP server (11 tools)
│   ├── base.py                   # Base classes and utilities
│   ├── operations.py             # Operations layer
│   ├── main_enterprise.py        # Enterprise FastAPI application
│   ├── README.md                 # Project documentation
│   ├── CLAUDE.md                 # This file - Claude Code configuration
│   ├── Makefile                  # Development commands
│   ├── pyproject.toml            # Python package metadata
│   ├── package.json              # Node/TypeScript dependencies
│   └── requirements.txt          # Python dependencies
│
├── agents/                       # 🤖 Super Agent Implementations
│   ├── base_super_agent.py       # Enhanced base with 17 prompt techniques
│   ├── commerce_agent.py         # E-commerce operations
│   ├── creative_agent.py         # Visual content generation
│   ├── marketing_agent.py        # Marketing & content
│   ├── support_agent.py          # Customer support
│   ├── operations_agent.py       # DevOps & deployment
│   ├── analytics_agent.py        # Data & insights
│   ├── visual_generation.py      # Google Imagen/Veo, FLUX integration
│   ├── tripo_agent.py            # 3D model generation (Tripo3D)
│   ├── fashn_agent.py            # Virtual try-on (FASHN)
│   ├── wordpress_asset_agent.py  # WordPress asset management
│   ├── collection_content_agent.py # Collection content generation
│   └── coding_doctor_agent.py    # Code analysis & fixing
│
├── llm/                          # 🧠 LLM Provider Layer
│   ├── base.py                   # Base LLM interface
│   ├── router.py                 # Intelligent task routing
│   ├── round_table.py            # Multi-LLM competition
│   ├── ab_testing.py             # Statistical A/B testing
│   ├── tournament.py             # Judge-based consensus
│   ├── exceptions.py             # LLM-specific errors
│   └── providers/
│       ├── openai.py             # OpenAI GPT-4, o1, etc.
│       ├── anthropic.py          # Claude 3.5 Sonnet
│       ├── google.py             # Gemini, Imagen, Veo
│       ├── mistral.py            # Mistral AI
│       ├── cohere.py             # Cohere Command
│       └── groq.py               # Groq (fast inference)
│
├── orchestration/                # 🎭 Orchestration Layer
│   ├── llm_orchestrator.py       # Central coordinator
│   ├── tool_registry.py          # Tool schema validation
│   ├── prompt_engineering.py     # 17 prompt techniques
│   ├── asset_pipeline.py         # Automated 3D asset generation
│   ├── brand_context.py          # SkyyRose brand DNA injection
│   ├── vector_store.py           # Chroma/Pinecone RAG
│   ├── document_ingestion.py     # Knowledge base chunking
│   ├── llm_clients.py            # LLM client wrappers
│   ├── llm_registry.py           # LLM provider registry
│   ├── domain_router.py          # Domain-based routing
│   ├── embedding_engine.py       # Embedding generation
│   ├── query_rewriter.py         # Query optimization
│   └── feedback_tracker.py       # Performance tracking
│
├── runtime/                      # ⚙️ Tool Runtime Layer
│   └── tools.py                  # ToolSpec, ToolRegistry, ToolCallContext
│
├── adk/                          # 🔌 ADK Framework Adapters
│   ├── base.py                   # Base ADK interface
│   ├── pydantic_adk.py           # PydanticAI adapter
│   ├── google_adk.py             # Google ADK adapter
│   ├── crewai_adk.py             # CrewAI adapter
│   ├── autogen_adk.py            # AutoGen adapter
│   ├── agno_adk.py               # Agno adapter
│   └── super_agents.py           # Unified super agent interface
│
├── security/                     # 🔒 Enterprise Security
│   ├── aes256_gcm_encryption.py  # AES-256-GCM encryption
│   ├── jwt_oauth2_auth.py        # JWT/OAuth2 authentication
│   ├── secrets_manager.py        # Secrets management (Vault/AWS)
│   ├── pii_protection.py         # PII detection & masking
│   ├── rate_limiting.py          # API rate limiting
│   ├── ssrf_protection.py        # SSRF prevention
│   ├── input_validation.py       # Input sanitization
│   ├── api_security.py           # API security middleware
│   ├── zero_trust_config.py      # Zero-trust architecture
│   ├── mtls_handler.py           # Mutual TLS
│   ├── audit_log.py              # Security audit logging
│   ├── alerting.py               # Security alerting
│   └── vulnerability_scanner.py  # Dependency scanning
│
├── api/                          # 🌐 API Endpoints
│   ├── index.py                  # Main API routes
│   ├── agents.py                 # Agent endpoints
│   ├── gdpr.py                   # GDPR compliance endpoints
│   ├── webhooks.py               # Webhook handlers
│   └── versioning.py             # API versioning support
│
├── mcp/                          # 🛠️ MCP Servers
│   ├── openai_server.py          # OpenAI MCP server
│   ├── agent_bridge_server.py    # Agent bridge MCP
│   ├── rag_server.py             # RAG MCP server
│   └── woocommerce_mcp.py        # WooCommerce integration
│
├── wordpress/                    # 📝 WordPress Integration
│   ├── client.py                 # WordPress REST API client
│   ├── ar_viewer.php             # AR viewer plugin
│   └── assets/                   # WordPress assets
│
├── database/                     # 💾 Database Layer
│   └── db.py                     # Neon PostgreSQL client
│
├── tests/                        # ✅ Test Suite
│   ├── conftest.py               # Pytest fixtures
│   ├── test_agents.py            # Agent tests
│   ├── test_llm.py               # LLM provider tests
│   ├── test_runtime.py           # Tool runtime tests
│   ├── test_security.py          # Security module tests
│   ├── test_adk.py               # ADK adapter tests
│   ├── test_gdpr.py              # GDPR compliance tests
│   ├── test_wordpress.py         # WordPress integration tests
│   ├── test_zero_trust.py        # Zero-trust tests
│   └── security/                 # Security-specific tests
│
├── .github/workflows/            # 🔄 CI/CD Pipelines
│   ├── ci.yml                    # Main CI pipeline
│   ├── asset-generation.yml      # 3D asset generation
│   └── dast-scan.yml.example     # DAST security scanning
│
├── frontend/                     # 🎨 Next.js 15 Dashboard
│   ├── app/                      # Next.js 15 App Router
│   ├── components/               # React components
│   └── public/                   # Static assets
│
├── src/collections/              # 💎 Three.js 3D Experiences
│   ├── black-rose/               # Gothic rose garden
│   ├── signature/                # Luxury outdoor
│   ├── love-hurts/               # Castle ballroom
│   ├── showroom/                 # Virtual showroom
│   └── runway/                   # Fashion runway
│
├── docs/                         # 📚 Documentation
│   ├── README.md                 # Docs index
│   ├── MCP_ARCHITECTURE.md       # MCP architecture
│   ├── ZERO_TRUST_ARCHITECTURE.md # Security architecture
│   ├── LLM_CLIENTS_QUICK_START.md # LLM setup guide
│   ├── architecture/             # Architecture docs
│   │   └── DEVSKYY_MASTER_PLAN.md # Master architecture plan
│   ├── api/                      # API documentation
│   │   └── ECOMMERCE_API.md      # E-commerce API spec
│   └── runbooks/                 # Incident response runbooks
│       ├── security-incident-response.md
│       ├── data-breach.md
│       └── [other security runbooks]
│
└── scripts/                      # 🔧 Utility Scripts
    ├── verify_llm_clients.py     # LLM client verification
    ├── test_mcp_servers.py       # MCP server testing
    ├── run_asset_pipeline.py     # Asset generation
    └── generate_secrets.py       # Secrets generation
```

---

## 🏛️ Architecture Overview

### 6 SuperAgents (`agents/`)
All agents inherit from `EnhancedSuperAgent` in `base_super_agent.py`, which provides:
- 17 prompt engineering techniques with auto-selection based on task type
- ML capabilities module (scikit-learn, prophet)
- Self-learning optimization with performance tracking
- LLM Round Table interface for multi-model competition

| Agent | Domain | Key Capabilities |
|-------|--------|------------------|
| CommerceAgent | E-commerce | Products, orders, inventory, pricing optimization |
| CreativeAgent | Visual | 3D assets (Tripo3D), images (Google Imagen/FLUX), virtual try-on (FASHN) |
| MarketingAgent | Content | SEO, social media, email campaigns, trend analysis |
| SupportAgent | Service | Tickets, FAQs, escalation, intent classification |
| OperationsAgent | DevOps | WordPress, Elementor, deployment, monitoring |
| AnalyticsAgent | Data | Reports, forecasting, clustering, anomaly detection |

### LLM Layer (`llm/`)
- **6 Providers**: OpenAI, Anthropic, Google, Mistral, Cohere, Groq
- **router.py**: Task-based intelligent routing with cost/speed/quality optimization
- **round_table.py**: LLM competition where all providers compete, top 2 go to A/B testing
- **ab_testing.py**: Statistical significance testing with z-score, p-value, power analysis
- **tournament.py**: Judge-based consensus mechanism

### Orchestration Layer (`orchestration/`)
- **llm_orchestrator.py**: Central coordinator for model selection and task routing
- **tool_registry.py**: Schema validation and permission-based tool execution
- **prompt_engineering.py**: 17 techniques (CoT, Few-Shot, ToT, ReAct, RAG, Constitutional, etc.)
- **asset_pipeline.py**: Automated 3D asset generation from product descriptions
- **brand_context.py**: SkyyRose brand DNA injection into all prompts
- **vector_store.py**: Chroma/Pinecone for RAG retrieval
- **document_ingestion.py**: Chunking and embedding for knowledge base

### ADK Adapters (`adk/`)
Framework abstraction layer supporting multiple agent frameworks:
- **PydanticAI**: Type-safe agents with Pydantic validation
- **Google ADK**: Google's Agent Development Kit
- **CrewAI**: Multi-agent collaboration
- **AutoGen**: Microsoft AutoGen framework
- **Agno**: Agno framework adapter

### Visual Generation (`agents/visual_generation.py`)
Google + HuggingFace handle ALL imagery with SkyyRose brand assets:
- **Google Imagen 3**: Text-to-image
- **Google Veo 2**: Text-to-video
- **HuggingFace FLUX.1**: High-quality image generation
- **Tripo3D**: 3D model generation (via tripo_agent.py)
- **FASHN**: Virtual try-on (via fashn_agent.py)

### Frontend Architecture
- **`src/collections/`**: 5 immersive Three.js experiences (Black Rose, Signature, Love Hurts, Showroom, Runway)
- **`frontend/`**: Next.js 15 dashboard with agent control, Round Table viewer, A/B testing dashboard, tools browser

### Security (`security/`)
Enterprise security modules: AES-256-GCM encryption, JWT/OAuth2, Argon2id hashing, PII protection, SSRF prevention, rate limiting

### Key Patterns

#### Tool Execution
Tools are registered in `runtime/tools.py` with schema validation. Execute via:
```python
result = await agent.use_tool("tool_name", {"param": "value"})
```

#### LLM Round Table Flow
1. All 6 LLMs generate responses in parallel
2. Responses scored on relevance, coherence, completeness, creativity
3. Top 2 finalists go through A/B testing
4. Winner determined by statistical significance
5. Results persisted to Neon PostgreSQL

#### Prompt Technique Selection
`base_super_agent.py` auto-selects technique based on `TaskCategory`:
- reasoning → chain_of_thought
- classification → few_shot
- creative → tree_of_thoughts
- search → react
- qa → rag

### Database
- **Neon PostgreSQL**: Serverless, connection pooling via `DATABASE_URL`
- **Vector Stores**: Chroma (local), Pinecone (production)
- **Redis**: Caching and task queues

### Deployment
- **Vercel**: Full-stack serverless (`vercel.json` at root)
- **Docker**: `make docker-build && make docker-run`

### Brand Context
SkyyRose brand DNA is injected into all visual generation:
```python
SKYYROSE_BRAND_DNA = {
    "name": "SkyyRose",
    "tagline": "Where Love Meets Luxury",
    "colors": {"primary": "#B76E79", "secondary": "#1A1A1A"},
    "style_keywords": ["premium", "sophisticated", "bold", "elegant", "luxury"]
}
```

---

## 🛠️ Common Commands

### Development
```bash
# Install dependencies
pip install -e .

# Run formatters (ALWAYS after file changes)
isort .
ruff check . --fix
black .

# Run type checker
mypy .

# Run tests
pytest tests/ -v

# Run security audit
pip-audit
bandit -r .
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_agents.py::test_tool_runtime -v

# Skip slow tests
pytest -m "not slow"
```

### MCP Server
```bash
# Start MCP server
python devskyy_mcp.py

# Debug mode
python devskyy_mcp.py --mcp-debug

# Test MCP tools
python -c "from devskyy_mcp import mcp; print(mcp.list_tools())"
```

---

## 📋 Code Style Guidelines

### Python Style (PEP8)
- Use **type hints** everywhere
- Prefer **dataclasses/Pydantic** over dicts
- **No mutable defaults** ([], {})
- **Explicit is better than implicit**
- Use **async/await** for I/O operations
- **Docstrings** for all public functions (Google style)

### Example:
```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ToolSpec(BaseModel):
    """Specification for a registered tool.
    
    Attributes:
        name: Unique tool identifier
        schema: JSON schema for inputs
        handler: Callable that executes the tool
        permissions: Required permission level
        timeout_ms: Maximum execution time
        idempotency_key: Optional key for duplicate detection
    """
    name: str = Field(..., description="Tool name")
    schema: Dict[str, Any]
    handler: Callable
    permissions: List[str] = Field(default_factory=list)
    timeout_ms: int = 5000
    idempotency_key: Optional[str] = None
```

### Error Handling
```python
# GOOD - Explicit error taxonomy
class DevSkyError(Exception):
    """Base exception for all DevSkyy errors."""
    pass

class ToolExecutionError(DevSkyError):
    """Raised when tool execution fails."""
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Tool {tool_name} failed: {reason}")

# BAD - Generic exceptions
raise Exception("Something went wrong")
```

### No Placeholder Strings
```python
# BAD - Returns placeholder in production
async def execute_agent(task: str) -> str:
    return "Agent execution simulated"

# GOOD - Real implementation or explicit stub
async def execute_agent(task: str) -> AgentResult:
    if not self._initialized:
        raise RuntimeError("Agent not initialized")
    
    plan = await self._plan(task)
    result = await self._execute(plan)
    return AgentResult(
        status="completed",
        artifacts=result.artifacts,
        metrics=result.metrics
    )
```

---

## 🔍 Testing Philosophy

### Test-Driven Development (TDD)
1. **Write tests FIRST** based on expected behavior
2. **Confirm tests fail** before implementation
3. **Implement code** to pass tests
4. **Iterate** until all tests pass
5. **Commit** tests and code separately

### Test Structure
```python
# tests/test_agents.py
import pytest
from agents.commerce import CommerceAgent
from runtime.tools import ToolRegistry

@pytest.fixture
def tool_registry():
    """Shared tool registry fixture."""
    registry = ToolRegistry()
    # Register test tools
    return registry

@pytest.mark.asyncio
async def test_commerce_agent_uses_tool_runtime(tool_registry):
    """Commerce agent must use ToolRegistry, not direct calls."""
    agent = CommerceAgent(tool_registry=tool_registry)
    
    # Plan phase
    plan = await agent.plan("Create product listing")
    assert plan.tools_required  # Must identify needed tools
    
    # Execute phase
    result = await agent.execute(plan)
    assert result.status == "completed"
    assert result.tool_calls  # Must show which tools were called
    assert all(call.validated for call in result.tool_calls)
```

---

## 🎨 WordPress/Elementor Integration

### Theme Builder Pattern
```python
# NO - Hardcoded brand constants
def generate_theme():
    colors = {"primary": "#1a1a1a", "accent": "#gold"}
    return theme

# YES - BrandKit abstraction
class BrandKit(BaseModel):
    name: str
    colors: ColorPalette
    typography: TypographySystem
    spacing: SpacingScale
    imagery: ImageryGuidelines
    voice: BrandVoice

class PageSpec(BaseModel):
    type: Literal["home", "collection", "pdp", "about"]
    layout: LayoutConfig
    sections: List[SectionSpec]
    
# Usage
brand = BrandKit.from_yaml("skyyrose_brand.yml")
spec = PageSpec(type="pdp", layout="luxury_fashion")
theme = await builder.generate(brand, spec)
```

### Validation Pipeline
```python
# Generate → Validate → Import → Assign
theme_json = await builder.generate_theme(brand, pages)
validation = await validator.validate_structure(theme_json)
if not validation.passed:
    raise ThemeValidationError(validation.errors)

wp_import = await wp_client.import_theme(theme_json)
await wp_client.assign_theme(site_id, wp_import.theme_id)
```

---

## 🤖 Agent Architecture

### Super Agent Pattern
Each Super Agent MUST:
1. **Plan** - Break down task into steps
2. **Retrieve** - RAG-ready interface (stub acceptable)
3. **Execute** - Use ToolRegistry for all actions
4. **Validate** - Verify outputs against schema
5. **Emit** - Structured artifacts, not strings

### Tool Runtime Layer
```python
# runtime/tools.py
class ToolCallContext(BaseModel):
    correlation_id: str
    agent_id: str
    timestamp: datetime
    metadata: Dict[str, Any]

class ToolRegistry:
    def register(self, spec: ToolSpec) -> None: ...
    def get_tool(self, name: str) -> ToolSpec: ...
    def execute(self, name: str, inputs: Dict, context: ToolCallContext) -> ToolResult: ...
    def list_tools(self, permissions: List[str]) -> List[ToolSpec]: ...
```

---

## 🔐 Security & Compliance

### Crypto Contracts
```python
# Encryption MUST support:
# - str
# - bytes  
# - dict (via stable JSON serialization)

def encrypt(data: Union[str, bytes, dict]) -> bytes:
    """Encrypt data with AES-256-GCM."""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    # ... implementation
    
def decrypt(ciphertext: bytes) -> str:
    """Decrypt and return as string by default."""
    # ... implementation

def decrypt_bytes(ciphertext: bytes) -> bytes:
    """Decrypt and return raw bytes for binary workflows."""
    # ... implementation
```

### GDPR Endpoints
- `GET /api/v1/gdpr/export` - Right of Access (Article 15)
- `DELETE /api/v1/gdpr/delete` - Right to Erasure (Article 17)
- `GET /api/v1/gdpr/retention-policy` - Right to Information (Article 13)

---

## 📦 3D Asset Pipeline

### Production-Safe Pattern
```python
class ThreeDAssetPipeline:
    async def generate(
        self,
        prompt: str,
        retries: int = 3,
        idempotency_key: Optional[str] = None
    ) -> ThreeDAsset:
        """Generate 3D asset with retries and validation.
        
        Returns:
            ThreeDAsset with validated polycount and texture size.
            
        Raises:
            AssetGenerationError: If generation fails after retries.
            AssetValidationError: If output doesn't meet quality standards.
        """
        # Implementation with retry logic
        # Output validation (polycount, texture size)
        # WP media upload integration
        # WooCommerce product attachment
        
    async def validate_output(self, asset: ThreeDAsset) -> ValidationResult:
        """Validate 3D asset meets quality standards.
        
        Checks:
        - Polycount within acceptable range (stub acceptable)
        - Texture size appropriate for web (stub acceptable)
        - File format compatibility
        """
```

---

## 🚀 Deployment Workflow

### Pre-Commit Checklist
- [ ] Run formatters: `isort . && ruff check . --fix && black .`
- [ ] Type check: `mypy .`
- [ ] Run tests: `pytest`
- [ ] Security audit: `pip-audit && bandit -r .`
- [ ] Update documentation if interfaces changed
- [ ] No TODO/FIXME/placeholder strings

### CI/CD Pipeline (.github/workflows/ci.yml)
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Lint
        run: |
          isort --check .
          ruff check .
          black --check .
      - name: Type check
        run: mypy .
      - name: Security
        run: |
          pip-audit
          bandit -r .
      - name: Test
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📝 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, perf, test, chore

**Example**:
```
feat(agents): implement Tool Runtime Layer

- Add ToolSpec, ToolRegistry, ToolCallContext
- Unified exception taxonomy for tool errors
- Permission metadata and timeout hooks
- Idempotency key support

Closes #123
Breaking: Agents now require ToolRegistry injection
```

---

## 🎓 Learning Resources

### Fashion Domain
- PDP (Product Detail Page) vs Collection layout logic
- Image hierarchy: hero → lifestyle → detail shots
- Typography hierarchy: display → heading → body → caption
- Size recommendation algorithms
- Color palette psychology in fashion

### ML/AI
- Model registry with version control
- Distributed caching strategies (Redis + in-memory)
- SHAP-based explainability
- A/B testing frameworks
- Continuous retraining pipelines

### WordPress/Elementor
- REST API authentication patterns
- Media upload with proper MIME types
- Shoptimizer 2.9.0 theme integration
- Elementor Pro 3.32.2 widget system
- WooCommerce product variants

---

## ⚠️ Common Pitfalls

### DON'T
- ❌ Return placeholder strings in agent logic
- ❌ Use mutable defaults (list=[], dict={})
- ❌ Ignore failing tests
- ❌ Hand-wave tool execution/validation
- ❌ Optimize prematurely (correctness first)
- ❌ Commit secrets/API keys
- ❌ Skip documentation updates

### DO
- ✅ Write tests before implementation (TDD)
- ✅ Use type hints everywhere
- ✅ Validate inputs with Pydantic
- ✅ Return structured objects, not strings
- ✅ Log with correlation IDs
- ✅ Update ALL related files after changes
- ✅ Run formatters after every change

---

## 🔄 Workflow: Explore → Plan → Code → Commit

### 1. Explore Phase
```bash
# Ask Claude to read relevant files
read devskyy_mcp.py operations.py
read DEVSKYY_MASTER_PLAN.md

# Explicitly tell Claude NOT to code yet
"Please analyze the codebase architecture but DO NOT write any code yet."
```

### 2. Plan Phase
```bash
# Use extended thinking for complex problems
"Think hard about implementing the Tool Runtime Layer. 
Consider:
- How existing agents will migrate
- What interfaces need to change
- Test coverage requirements
- Backward compatibility

Create a detailed plan as a GitHub issue."
```

### 3. Code Phase
```bash
# Implement with TDD
"Now implement the Tool Runtime Layer following the plan.
1. Write tests first for ToolRegistry
2. Confirm tests fail
3. Implement ToolRegistry
4. Iterate until tests pass
5. Commit tests and code separately"
```

### 4. Commit Phase
```bash
# Git operations
"Commit the changes with a descriptive message following our format.
Then create a PR with:
- Summary of changes
- Breaking changes list
- Testing instructions"
```

---

## 🎯 Current Sprint Focus

### Immediate Priorities (Next 7 Days)
1. **Run test suite** → enumerate all failures
2. **Fix security + crypto contract failures**
3. **Fix packaging/import hygiene** 
4. **Eliminate mutable defaults & typing leaks**
5. **Implement Tool Runtime Layer**
6. **Refactor Super Agents** to use Tool Runtime
7. **Refactor MCP** to expose Tool Runtime
8. **Harden Elementor pipeline** (BrandKit, PageSpec, validation)
9. **Harden 3D pipeline** (retries, validation, WordPress integration)
10. **Align documentation & CI**

### Success Metrics
- [ ] pytest passes with zero unexpected failures
- [ ] All crypto methods exist and handle str/bytes/dict
- [ ] Tool Runtime Layer operational with tests
- [ ] All Super Agents use ToolRegistry
- [ ] MCP exposes real tools from registry
- [ ] Elementor pipeline has deterministic validation
- [ ] 3D pipeline has retry/validation/WordPress integration
- [ ] GitHub Actions CI passes
- [ ] Zero TODOs/FIXMEs in production paths

---

## 💡 Tips for Working with Claude Code

### Use Subagents for Verification
```bash
# For complex tasks, verify details with subagents
"Before implementing, please use subagents to:
1. Verify the current crypto implementation
2. Check for existing ToolRegistry patterns
3. Review test coverage gaps"
```

### Course Correct Early
```bash
# Press ESC to interrupt and redirect
# Double-tap ESC to go back and edit prompt
# Use /clear between independent tasks

"Actually, let's approach this differently.
Instead of modifying existing code, create a new
Tool Runtime module first, then migrate agents one at a time."
```

### Use Checklists for Complex Tasks
```bash
"Create a checklist in TOOL_RUNTIME_MIGRATION.md:
- [ ] Create runtime/tools.py
- [ ] Implement ToolSpec
- [ ] Implement ToolRegistry
- [ ] Write tests for ToolRegistry
- [ ] Migrate CommerceAgent
- [ ] Migrate CreativeAgent
...

Work through each item, checking off as you complete."
```

---

## 📞 Emergency Contacts

- **Repository Owner**: damBruh (SkyyRose LLC)
- **Primary Email**: support@skyyrose.com
- **GitHub Issues**: Use for bugs/features
- **Security Issues**: security@skyyrose.com (private disclosure)

---

## 📚 Documentation Index

- **Architecture**: `docs/architecture/DEVSKYY_MASTER_PLAN.md`
- **MCP Architecture**: `docs/MCP_ARCHITECTURE.md`
- **MCP Configuration**: `docs/MCP_CONFIGURATION_GUIDE.md`
- **MCP Quick Reference**: `docs/MCP_QUICK_REFERENCE.md`
- **Zero Trust Architecture**: `docs/ZERO_TRUST_ARCHITECTURE.md`
- **LLM Clients Setup**: `docs/LLM_CLIENTS_QUICK_START.md`
- **API Documentation**: `docs/api/ECOMMERCE_API.md`
- **JavaScript/TypeScript SDK**: `docs/javascript-typescript-sdk.md`
- **Security Runbooks**: `docs/runbooks/` (incident response procedures)
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md`
- **Secrets Migration**: `docs/SECRETS_MIGRATION.md`

---

**Last Updated**: 2024-12-20
**Version**: 1.0.0
**Status**: Production Hardening in Progress

---

# REMEMBER:
- This is NOT a demo - every line must be production-ready
- Correctness > Elegance > Performance
- No stubs, no placeholders, no TODOs in production paths
- Test-driven development is mandatory
- Update this file as patterns emerge
