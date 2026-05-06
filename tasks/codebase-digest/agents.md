# agents/ — Codebase Digest

Generated: 2026-05-05  
Scope: All Python source files in `agents/` (excluding `devskyy-a2a/.venv/`, `__pycache__/`, generated fixtures)

---

## 1. Purpose and Scope

The `agents/` package is the intelligence layer of DevSkyy — every AI-driven task (product ops, imagery generation, 3D model creation, content writing, marketing campaigns, analytics, deploy automation) routes through one of the classes here.

The package contains **four parallel inheritance hierarchies** that were built at different points in the project's history and were never fully consolidated. All four are currently alive and reachable from production endpoints. The hierarchies are:

1. **CoreAgent / SelfHealingMixin** (`agents/core/`) — newest, circuit-breaker-first design
2. **EnhancedSuperAgent** (`agents/base_super_agent/`) — ADK-backed, ML/prompt-engineering-rich
3. **SuperAgent (legacy)** (`agents/base_legacy.py`) — abstract base still used by FASHN and Tripo agents
4. **SDKSubAgent / ClaudeSDKBaseAgent** (`agents/claude_sdk/`) — Claude Agent SDK execution engine

The total hand-written Python source in scope is roughly 12,000–15,000 lines across ~162 files (per the CLAUDE.md count). The `elite_web_builder/` subtree alone accounts for ~66 files and is a self-contained multi-agent web-building system.

---

## 2. Inheritance Hierarchy Map

### Hierarchy 1: CoreAgent (newest — `agents/core/`)

```
SelfHealingMixin
├── CoreAgent (abstract)
│   ├── CommerceCoreAgent
│   ├── ContentCoreAgent
│   ├── CreativeCoreAgent
│   ├── MarketingCoreAgent
│   ├── OperationsCoreAgent
│   ├── AnalyticsCoreAgent
│   ├── ImageryCoreAgent
│   └── WebBuilderCoreAgent
├── SubAgent (abstract)
│   ├── WordPressAIBridge  (also in shared/)
│   └── SDKSubAgent        (via claude_sdk/sdk_sub_agent.py — also inherits SDKCapabilityMixin)
│       ├── SDKCatalogManagerAgent
│       ├── SDKPriceOptimizerAgent
│       ├── SDKGarment3DAgent
│       ├── SDKSceneBuilderAgent
│       ├── SDKAvatarStylistAgent
│       └── ... (one SDKSubAgent per claude_sdk/domain_agents/*.py)
└── Orchestrator  (SelfHealingMixin directly, not CoreAgent)
```

**Canonical import:** `from agents.core.base import CoreAgent, SelfHealingMixin, CoreAgentType`

### Hierarchy 2: EnhancedSuperAgent (`agents/base_super_agent/`)

```
BaseDevSkyyAgent (from adk.base)
└── EnhancedSuperAgent
    ├── CommerceAgent       (agents/commerce_agent.py)
    ├── CreativeAgent       (agents/creative_agent.py)
    ├── MarketingAgent      (agents/marketing_agent.py)
    ├── OperationsAgent     (agents/operations_agent.py)
    ├── AnalyticsAgent      (agents/analytics_agent.py)
    ├── SecurityOpsAgent    (agents/security_ops_agent.py)
    └── SkyyRoseImageryAgent (agents/skyyrose_imagery_agent.py)
```

**Canonical import:** `from agents.base_super_agent import EnhancedSuperAgent`  
**Runtime:** ADK (`adk.base.BaseDevSkyyAgent`), NOT CoreAgent

### Hierarchy 3: Legacy SuperAgent (`agents/base_legacy.py`)

```
SuperAgent (ABC — from agents.core.base re-export / agents.base_legacy)
├── FashnTryOnAgent     (agents/fashn_agent.py)
└── TripoAssetAgent     (agents/tripo_agent.py)
```

**Note:** `agents/core/base.py` re-exports `SuperAgent`, `AgentConfig`, `AgentCapability`, `AgentStatus`, `ExecutionResult`, `LLMCategory`, `PlanStep`, `RetrievalContext`, `ValidationResult` from `agents.base_legacy` at the bottom of the file. So `from agents.core.base import SuperAgent` works but resolves to the legacy class.

### Hierarchy 4: Claude SDK (`agents/claude_sdk/`)

```
ClaudeSDKBaseAgent     (agents/claude_sdk/base.py — wraps ClaudeSDKClient directly)
SDKCapabilityMixin     (agents/claude_sdk/mixin.py — composable, not a base class)
SDKSubAgent(SubAgent, SDKCapabilityMixin)  (agents/claude_sdk/sdk_sub_agent.py)
WordPressBridgeAgent   (agents/wordpress_bridge/agent.py — standalone, no hierarchy)
```

### Standalone Systems

- **EliteDirector / Director** (`agents/elite_web_builder/director.py`) — standalone multi-agent system with its own internal `agents/` package (not the top-level one). Spawns 8 specialist SDK agents (frontend_dev, backend_dev, accessibility, performance, qa, seo_content, design_system, runtime) via `AgentRuntime`.
- **SkyyRoseSpacesOrchestrator** (`agents/skyyrose_spaces_orchestrator.py`) — standalone class (no base class), manages HuggingFace Spaces + WordPress API pipeline for batch product rendering.

---

## 3. Agent Inventory

### Top-level domain agents (legacy EnhancedSuperAgent hierarchy)

| File | Class | Hierarchy | agent_type |
|------|-------|-----------|------------|
| `commerce_agent.py` | `CommerceAgent` | EnhancedSuperAgent | COMMERCE |
| `creative_agent.py` | `CreativeAgent` | EnhancedSuperAgent | CREATIVE |
| `marketing_agent.py` | `MarketingAgent` | EnhancedSuperAgent | MARKETING |
| `operations_agent.py` | `OperationsAgent` | EnhancedSuperAgent | OPERATIONS |
| `analytics_agent.py` | `AnalyticsAgent` | EnhancedSuperAgent | ANALYTICS |
| `security_ops_agent.py` | `SecurityOpsAgent` | EnhancedSuperAgent | (unset — uses ANALYTICS default) |
| `skyyrose_imagery_agent.py` | `SkyyRoseImageryAgent` | EnhancedSuperAgent | (custom) |
| `skyyrose_content_agent.py` | `SkyyRoseContentAgent` | EnhancedSuperAgent | (custom) |

### Top-level specialized agents (legacy SuperAgent hierarchy)

| File | Class | Hierarchy | Key config |
|------|-------|-----------|------------|
| `fashn_agent.py` | `FashnTryOnAgent` | SuperAgent | `FASHN_USD_PER_IMAGE = 0.075`; preflight gate via `/preflight` |
| `tripo_agent.py` | `TripoAssetAgent` | SuperAgent | Multi-account/multi-region key rotation; `TripoConfig` dataclass; `GARMENT_TEMPLATES` |

### Top-level orchestrators (standalone)

| File | Class | Hierarchy | Purpose |
|------|-------|-----------|---------|
| `skyyrose_spaces_orchestrator.py` | `SkyyRoseSpacesOrchestrator` | standalone | HF Spaces → WordPress batch pipeline |

### Core agents (`agents/core/*/agent.py`)

| Module | Class | core_type | Sub-agents registered |
|--------|-------|-----------|----------------------|
| `core/commerce/agent.py` | `CommerceCoreAgent` | COMMERCE | product_ops, wordpress_assets, wordpress_bridge, sdk_catalog_manager, sdk_price_optimizer |
| `core/content/agent.py` | `ContentCoreAgent` | CONTENT | collection_content, seo_copywriter (+ aliases), sdk_seo_writer, sdk_collection_publisher |
| `core/creative/agent.py` | `CreativeCoreAgent` | CREATIVE | brand_creative (+ aliases) |
| `core/marketing/agent.py` | `MarketingCoreAgent` | MARKETING | social_media, campaign_ops (+ aliases), sdk_campaign_analyst, sdk_competitive_intel |
| `core/operations/agent.py` | `OperationsCoreAgent` | OPERATIONS | deploy_health (+ aliases), security_monitor, coding_doctor, sdk_deploy_runner, sdk_code_doctor, sdk_security_scanner |
| `core/analytics/agent.py` | `AnalyticsCoreAgent` | ANALYTICS | analytics_ops (+ aliases), algorithm (+ aliases), brand_intel (+ aliases), sdk_data_analyst, sdk_report_generator |
| `core/imagery/agent.py` | `ImageryCoreAgent` | IMAGERY | gemini_image, fashn_vton, tripo_3d, meshy_3d, hf_spaces; overrides `_apply_fix()` for 3D provider failover |
| `core/web_builder/agent.py` | `WebBuilderCoreAgent` | WEB_BUILDER | web_dev (+ aliases), sdk_theme_dev, sdk_template_builder; delegates full builds to `EliteDirector` |

### Claude SDK domain agents (`agents/claude_sdk/domain_agents/`)

Each file exports 2–3 `SDKSubAgent` subclasses. All use `SDKCapabilityMixin._sdk_execute()` as the execution engine with Claude Agent SDK tool use. Key classes:

| File | Classes | Parent type |
|------|---------|-------------|
| `commerce.py` | `SDKCatalogManagerAgent`, `SDKPriceOptimizerAgent` | COMMERCE |
| `content.py` | `SDKSeoWriterAgent`, `SDKCollectionPublisherAgent` | CONTENT |
| `creative.py` | `SDKBrandGuardianAgent`, ... | CREATIVE |
| `marketing.py` | `SDKCampaignAnalystAgent`, `SDKCompetitiveIntelAgent` | MARKETING |
| `operations.py` | `SDKDeployRunnerAgent`, `SDKCodeDoctorAgent`, `SDKSecurityScannerAgent` | OPERATIONS |
| `analytics.py` | `SDKDataAnalystAgent`, `SDKReportGeneratorAgent` | ANALYTICS |
| `immersive.py` | `SDKGarment3DAgent`, `SDKSceneBuilderAgent`, `SDKAvatarStylistAgent` | IMAGERY / WEB_BUILDER |
| `web_builder.py` | `SDKThemeDevAgent`, `SDKTemplateBuilderAgent` | WEB_BUILDER |
| `imagery.py` | `SDKImageGeneratorAgent`, ... | IMAGERY |

### Visual Generation (`agents/visual_generation/`)

Standalone module — no agent base class. Providers: `google_imagen`, `google_veo`, `huggingface_flux`, `huggingface_sd`, `replicate_lora`, `tripo3d`, `fashn`. Contains `VisualGenerationAgent`, `ConversationEditorAgent`, `GeminiNativeAgent`, `PromptOptimizer`, `ReferenceManager`.

### WordPress Bridge (`agents/wordpress_bridge/`)

`WordPressBridgeAgent` — standalone class using `ClaudeSDKClient` directly with 15 MCP tools. Uses `claude-opus-4-6` model with adaptive thinking. Not part of any inheritance hierarchy.

### Elite Web Builder (`agents/elite_web_builder/`)

66 Python files. `Director` class orchestrates 8 specialist specs (frontend_dev, backend_dev, accessibility, performance, qa, seo_content, design_system, runtime) via its own internal `AgentRuntime`. Has `RalphExecutor` integration, `CostTracker`, `LearningJournal`, `SelfHealer`, `Context7Bridge`, `LighthouseRunner`, `ScreenshotDiff` tools. This is a self-contained multi-agent theme-building system that `WebBuilderCoreAgent` delegates full builds to.

---

## 4. Key Data Flows

### Task execution through the CoreAgent hierarchy

```
User request
    → Orchestrator.route(task)
        → keyword scoring → CoreAgentType
        → CoreAgent.execute_safe(task)
            → circuit_breaker_allows()?
            → CoreAgent.execute(task)
                → keyword routing → delegate(sub_agent_name, task)
                    → SubAgent.execute_safe(task)
                        → SubAgent.execute(task)
                            → _llm_execute() [UnifiedLLMClient] OR _sdk_execute() [ClaudeSDKClient]
                        on failure: heal() → retry → _escalation_response()
            on failure: heal() → _try_alternative_sub_agents()
        on escalation: _handle_escalation() → other core agents → _sdk_escalation()
```

### Task execution through EnhancedSuperAgent hierarchy

```
Agent.execute_auto(prompt)
    → correlation_id generation
    → TaskCategoryAnalyzer.analyze(prompt) → TaskCategory + confidence
    → PromptEngineeringModule.select_technique() → PromptTechnique
    → apply_technique(prompt, technique) → enriched_prompt
    → _is_high_stakes_task()? → execute_with_round_table() OR execute_with_learning()
        → LLMRoundTableInterface.compete() if round_table
            → asyncio.gather(all providers) → score → _ab_test() → winner
        → _route_to_provider() → LLMRouter OR _execute_direct()
    → SelfLearningModule.record_execution()
    → if score ≥ 0.8: ingest_successful_response() → RAG queue (stubbed)
```

### WordPress AI Bridge flow

```
Python CoreAgent/Orchestrator
    → WordPressAIBridge.generate_text/image()
        → POST /index.php?rest_route=/wp-ai/v1/ai/prompt
            → WordPress PHP AI Client SDK
                → OpenAI / Anthropic / Google provider
```

### Round Table provider mapping

```
Round Table provider name → WordPress SDK provider
"claude" → "anthropic"
"gpt4"   → "openai"
"gemini" → "google"
```

---

## 5. Module-by-Module Breakdown

### `agents/core/base.py` (779 lines) — MOST CRITICAL

**`SelfHealingMixin`**
- `__init_healing__()`: sets `_consecutive_failures=0`, `_circuit_state=CLOSED`, `_heal_journal` (LRU OrderedDict, max 100 entries)
- `categorize_failure(error)`: 16 `_CATEGORY_OVERRIDES` keyword rules (env var→CONFIG, 429→EXTERNAL, 503→PROVIDER_DOWN, etc.) + `AgentError` category mapping
- `diagnose(error)`: categorizes + checks journal for past fixes → `DiagnosisResult`
- `heal(diagnosis)`: async, up to `_max_heal_attempts=3`, records to journal, calls `_apply_fix()`
- `_apply_fix(diagnosis)`: base: wait 2s for EXTERNAL/PROVIDER_DOWN, return failure otherwise; subclasses override
- `circuit_breaker_allows()`: CLOSED=True, OPEN checks 60s cooldown → HALF_OPEN, HALF_OPEN=True (one test pass)
- `_record_success()`: resets failures; if HALF_OPEN → CLOSED
- `_record_failure()`: increments; at threshold=5 → OPEN
- `health_check()`: collects sub-agent health via `dir()` scan for SelfHealingMixin instances → `HealthStatus`

**`CoreAgent(SelfHealingMixin)`**
- Abstract: `core_type: CoreAgentType`, `name: str`, `description: str` (class-level attrs)
- `register_sub_agent(name, agent)`, `get_sub_agents()`
- `delegate(name, task)`: circuit breaker check → `execute()` → heal on failure → `_try_alternative_sub_agents()`
- `_try_alternative_sub_agents(task, excluded)`: skips OPEN circuits, escalates if all fail
- Abstract `execute(task, **kwargs) → dict[str, Any]`
- `execute_safe(task)`: circuit gate → execute → heal → retry → error dict
- `to_portal_node()`: React Three Fiber-compatible dict for 3D dashboard

**Re-export gotcha (line ~779):** `core/base.py` re-exports `SuperAgent`, `AgentConfig`, `AgentCapability`, `AgentStatus`, `ExecutionResult`, `LLMCategory`, `PlanStep`, `RetrievalContext`, `ValidationResult` from `agents.base_legacy`. So the old "correct" import `from agents.core.base import SuperAgent` silently resolves to the deprecated class.

### `agents/core/sub_agent.py` (269 lines)

**`SubAgent(SelfHealingMixin)`**
- `name`, `parent_type`, `capabilities`, `description`, `system_prompt` (class-level)
- `_llm_execute(task, *, system_prompt, temperature, execution_mode, preferred_provider)`: lazy-init `UnifiedLLMClient` singleton; wraps `Message.system + Message.user`; maps string mode → `ExecutionMode` enum; returns `{"success", "result", "provider", "model", "technique", "latency_ms", "agent"}`
- Abstract `execute(task, **kwargs)`
- `execute_safe(task)`: circuit gate → execute → self-heal → escalation response
- `_escalation_response(error)`: `{"success": False, "escalation_needed": True, "sub_agent", "parent_type", "diagnosis"}`
- `escalate_to_parent(task, error)`: calls `parent.execute_safe()` if parent set
- `to_portal_node()`: sub-agent card for 3D dashboard

### `agents/core/orchestrator.py` (442 lines)

**`Orchestrator(SelfHealingMixin)`**
- Keyword-based `route_task(task)` → `CoreAgentType` via `_ROUTING_RULES` (8 rule tuples)
- `route(task)`: AI generation keywords → `WordPressAIBridge`; else → keyword routing → budget gate → core agent `execute_safe()` → escalation chain
- `_handle_escalation()`: tries other core agents → `_sdk_escalation()` (ephemeral `SDKCapabilityMixin` instance) → `requires_human_approval=True`
- Budget tracking: `_budget_limit_usd`, `_budget_spent_usd`; returns `requires_human_approval=True` when exceeded
- `system_health()`: all core agent HealthStatus + AI bridge health + summary dict
- `to_portal_graph()`: nodes + connections for React Three Fiber 3D portal

### `agents/core/factory.py` (80 lines)

`create_orchestrator(correlation_id, budget_limit_usd)` — dynamic imports of all 8 `_CORE_AGENT_REGISTRY` entries with graceful degradation (logs warning, continues on `ImportError`).

### `agents/core/shared/wp_ai_bridge.py` (380 lines)

**`WordPressAIBridge(SubAgent)`**
- REST API calls to `{wp_url}/index.php?rest_route=/wp-ai/v1/ai/prompt`
- `generate_text()`, `generate_image()`, `provider_status()`, `list_models()`
- `execute(task)`: keyword routing → provider_status / image / text
- `compete_for_round_table(prompt, round_table_provider)`: maps RT provider names → WP SDK names
- Auth: `httpx.BasicAuth` from `WP_AUTH_USER` / `WP_AUTH_PASS` env vars

### `agents/core/validation_scoring.py` (67 lines)

`compute_validation_scores(asset_validation, warning_count) → (quality_score, confidence_score)`: replaces hardcoded `0.9` baseline with real `fidelity_score` from validation dict (confidence=0.95) or penalty-degraded baseline (confidence=0.5). Handles 0-1 and 0-100 scale normalization.

### `agents/base_super_agent/agent.py` (1330 lines)

**`EnhancedSuperAgent(BaseDevSkyyAgent)`** — the production workhorse for legacy agents
- `agent_type: SuperAgentType = None` (must override in subclass)
- `initialize()`: creates all 4 modules (Learning, ML, Prompt, RoundTable) + LLMRouter (COST if temp<0.5, PRIORITY if ≥0.5) + Enterprise Intelligence (optional, silent ImportError)
- `execute_auto(prompt)`: PRIMARY ENTRY — correlation_id → TaskCategoryAnalyzer → technique selection → apply_technique → optional RAG inject → route/round_table/direct → record learning
- `execute_with_round_table(prompt)`: full RT competition; RAG auto-ingest of winners scoring ≥0.8
- `execute_smart(prompt)`: auto-detects high-stakes → round_table or learning path
- `_is_high_stakes_task(prompt)`: checks `HIGH_STAKES_TASK_TYPES` (10 entries), `HIGH_STAKES_AGENT_TYPES` ({commerce, operations}), prompt keyword scan
- `_get_preferred_provider(category)`: cross-refs `AGENT_PROVIDER_PREFERENCES` + `TASK_PROVIDER_PREFERENCES`
- `gather_enterprise_context()`: DeepSeek code search + semantic analysis + recommendations (all gated by ImportError)

### `agents/base_super_agent/types.py` (210 lines)

Key constants:
- `AGENT_PROVIDER_PREFERENCES`: per-agent-type preferred provider ordering (6 agent types × 3 providers)
- `TASK_PROVIDER_PREFERENCES`: per-task-category preferred providers
- `ROUND_TABLE_QUALITY_THRESHOLD = 0.8`
- `HIGH_STAKES_AGENT_TYPES = {"commerce", "operations"}`
- `HIGH_STAKES_TASK_TYPES`: set of 10 task type strings

### `agents/base_super_agent/learning_module.py` (474 lines)

**`SelfLearningModule`**
- Per-task-type stats: technique success rates, provider success rates, latency
- `get_best_technique()`: max success rate
- `get_best_provider()`: weighted formula (success_rate×0.7 + latency_score×0.3)
- `ingest_successful_response(prompt, response, score)`: only if score≥0.8; stores to `_knowledge_base` dict + queues RAG ingestion
- `flush_rag_queue()`: **STUBBED** — checks for `orchestration.document_ingestion` import but falls back to dict store; no real vector store write
- `query_similar_prompts(prompt)`: word-overlap Jaccard similarity (not semantic)

### `agents/base_super_agent/ml_module.py` (484 lines)

Three model wrappers: `SklearnModelWrapper`, `ProphetModelWrapper`, `TrendExtrapolationWrapper`
- All auto-fit with synthetic/random data if not fitted — confidence drops to 0.6 (silent degradation)
- Per-agent model configs: commerce=Prophet+Ridge, creative=ViT+custom, marketing=RoBERTa+Prophet, support=BART-MNLI+LogReg, operations=IsolationForest+Ridge, analytics=Prophet+KMeans

### `agents/base_super_agent/prompt_module.py` (537 lines)

**`PromptEngineeringModule`**: 11 technique dispatches (CoT, FewShot, ToT, ReAct, RAG, StructuredOutput, Constitutional, NegativePrompting, RoleBased, SelfConsistency, Ensemble); running outcome averages per technique.

**`TaskCategoryAnalyzer`**: 12 categories × {strong, moderate} keyword lists; scores by strong×2.0 + moderate×1.0, normalizes by /6.0, MD5 caches results; global singleton via `get_task_analyzer()`.

### `agents/base_super_agent/round_table_module.py` (555 lines)

**`LLMRoundTableInterface`**
- Wraps `llm.round_table.LLMRoundTable` (production) if available, else lightweight fallback
- `SCORING_CRITERIA`: relevance=0.25, quality=0.25, completeness=0.20, efficiency=0.15, brand_alignment=0.15
- `BRAND_KEYWORDS`: 15 luxury/fashion keywords
- `_generate_all_with_retry()`: asyncio.gather + exponential backoff (0.5s→1s→2s)
- `_score_entries()`: heuristic (word overlap, length/structure, completion indicators, latency/cost, brand keywords)
- `_ab_test()`: judge LLM picks between top 2 via "WINNER: A/B" string parsing
- Prometheus metrics via `security.prometheus_exporter` if importable

### `agents/claude_sdk/mixin.py` (349 lines)

**`SDKCapabilityMixin`**
- `sdk_tools`, `sdk_model`, `sdk_max_turns=15`, `sdk_permission`, `sdk_output_base` (class-level, override in subclass)
- `_sdk_execute(prompt, *, system_prompt, tools, agents, model, session_dir, label)`: async context manager over `ClaudeSDKClient`; streams `AssistantMessage` content blocks; returns `SDKExecutionResult`
- `_sdk_delegate(prompt, agents)`: lead agent spawns named subagents via `Task` tool
- `_sdk_session(prompt, session_id)`: stateful multi-turn (session_dir as session ID)
- `_sdk_build_hooks()`: wires `DevSkyyHookSystem` with optional self-healing integration (feeds tool failures into circuit breaker if `_record_failure` is present)
- Default system prompt includes project context, brand tokens, and output format instructions

### `agents/claude_sdk/sdk_sub_agent.py` (80+ lines)

**`SDKSubAgent(SubAgent, SDKCapabilityMixin)`** — MRO: SubAgent → SDKCapabilityMixin → SelfHealingMixin
- Default `execute(task)` routes through `_sdk_execute(task).to_dict()`
- Subclasses override `_sdk_default_prompt()`, `sdk_tools`, `sdk_model`, `sdk_output_base` for domain-specific behavior

### `agents/claude_sdk/tool_bridge.py` — `ToolProfile`

Predefined least-privilege tool sets per domain:
- `BASE`: [Read, Write]
- `COMMERCE`: [Read, Write, Bash, Glob, Grep]
- `CONTENT`: [Read, Write, Edit, Bash, WebSearch, WebFetch]
- `OPERATIONS`: [Read, Write, Edit, Bash, Glob, ...]
- `IMAGERY`: [Read, Write, Bash, WebFetch, ...]
- `FULL`: everything (orchestrator-level only)

### `agents/visual_generation/visual_generation.py`

Providers: `google_imagen`, `google_veo`, `huggingface_flux`, `huggingface_sd`, `replicate_lora`, `tripo3d`, `fashn`. Types: `IMAGE_FROM_TEXT`, `IMAGE_FROM_IMAGE`, `VIDEO_FROM_TEXT`, `VIDEO_FROM_IMAGE`, `MODEL_3D`, `VIRTUAL_TRYON`, `EXACT_PRODUCT` (LoRA). Uses `aiohttp` for async API calls. Not wired into CoreAgent hierarchy — called directly by pipeline scripts.

### `agents/wordpress_bridge/agent.py`

**`WordPressBridgeAgent`** — standalone, uses `ClaudeSDKClient` directly
- 15 MCP tools from `create_wordpress_tools()` (in `mcp_server.py`)
- `thinking={"type": "adaptive"}`, model `claude-opus-4-6`, max_turns=20, permission_mode `acceptEdits`
- `execute(prompt)`: streams response, collects `ResultMessage` for session_id + cost_usd

### `agents/elite_web_builder/director.py`

**`Director`** — standalone multi-agent system (66 files total)
- Parses user requirements → `PRDBreakdown` with `UserStory` items
- Each story dispatched through `AgentRuntime` to 8 specialist specs
- `LearningJournal` persists cross-session "instincts" from build outcomes
- `CostTracker` tallies token usage per agent per story
- `SelfHealer` handles build failures (distinct from `SelfHealingMixin`)
- `Context7Bridge` resolves library docs before generating code
- `RalphExecutor` integration: Ralph iteration loop can drive the Director
- `WebBuilderCoreAgent._get_director()` lazy-loads this for full build delegation

### `agents/base_legacy.py` (500+ lines) — DEPRECATED

`SuperAgent(ABC)` — abstract base with `AgentCapability` (38 capabilities), `AgentConfig`, `LLMCategory`, `PlanStep`, `RetrievalContext`, `ExecutionResult`, `ValidationResult`. Imports from `core.runtime.tool_registry`. `FashnTryOnAgent` and `TripoAssetAgent` still inherit from this directly (via `from agents.core.base import SuperAgent` which re-exports it).

### `agents/enhanced_base.py`

`EnhancedAgentConfig(BaseModel)` — Pydantic wrapper over `AgentConfig` with field validation (name format, length, timeout bounds). `to_base_config()` for backward compat. Adds retry + caching + telemetry config fields. Not used by any current agent — appears to be an intermediate refactor artifact.

### `agents/errors.py` (507 lines)

`AgentError(base)` with `ErrorCategory` (11 values: CONFIGURATION, AUTHENTICATION, VALIDATION, EXECUTION, TIMEOUT, RESOURCE, NETWORK, DEPENDENCY, DATA, PERMISSION, UNKNOWN) and `ErrorSeverity` (CRITICAL, HIGH, MEDIUM, LOW). 9 typed subclasses. `classify_exception(exc)` and `wrap_exception(exc)` utilities for converting raw exceptions.

### `agents/models.py` (436 lines)

SQLAlchemy ORM for PostgreSQL: `User`, `Product`, `Order`, `LLMRoundTableResult`, `AgentExecution`, `ToolExecution`, `RAGDocument`, `BrandAsset`, `BrandAssetIngestionJob`. UUID PKs, JSONB metadata, ARRAY types. Unusual placement (DB models in `agents/`) — these are the persistence models for agent execution history and LLM competition results.

---

## 6. Gotchas and Non-Obvious Behaviors

### G1: `from agents.core.base import SuperAgent` resolves to the deprecated class

`agents/core/base.py` ends with a bulk re-export from `agents.base_legacy`:
```python
from agents.base_legacy import SuperAgent, AgentConfig, AgentCapability, ...
```
Any code using `from agents.core.base import SuperAgent` is silently using the deprecated `base_legacy.SuperAgent`, not a new `CoreAgent`. `FashnTryOnAgent` and `TripoAssetAgent` rely on this path.

### G2: SelfLearningModule RAG flush is stubbed

`learning_module.py:flush_rag_queue()` looks up `orchestration.document_ingestion` but falls back unconditionally to `_knowledge_base[f"rag:{key}"] = content`. No data ever reaches a real vector store. High-scoring responses (≥0.8) accumulate in memory per process and are lost on restart.

### G3: MLCapabilitiesModule auto-fits with synthetic data

All three model wrappers (`SklearnModelWrapper`, `ProphetModelWrapper`, `TrendExtrapolationWrapper`) silently call `fit(synthetic_data)` if no real training data is present, returning predictions with confidence 0.6. There is no error or log warning. Code that checks only `success: True` will receive plausible-looking but uncalibrated ML predictions.

### G4: `EnhancedSuperAgent` is NOT a `CoreAgent`

Despite the CLAUDE.md stating "Custom agents extend `SuperAgent` from `agents.core.base`", the six legacy domain agents (`CommerceAgent`, `CreativeAgent`, etc.) extend `EnhancedSuperAgent` which extends `BaseDevSkyyAgent` from the `adk` package — a completely different lineage. They have no `SelfHealingMixin`, no circuit breaker, and no `execute_safe()` in the CoreAgent sense. The CoreAgent pattern (with self-healing) is layered on TOP of them via `CommerceCoreAgent._get_legacy_agent()` lazy-load.

### G5: `WordPressBridgeAgent` vs `WordPressAIBridge` — two different WP bridge classes

- `agents/wordpress_bridge/agent.py:WordPressBridgeAgent` — SDK-based, 15 MCP tools, opus model, standalone
- `agents/core/shared/wp_ai_bridge.py:WordPressAIBridge` — `SubAgent` subclass, direct REST calls to `wp-ai/v1/ai`, httpx-based, registered in Orchestrator
These are not the same class and serve different call sites.

### G6: `SDKSceneBuilderAgent` references `immersive-world.js` which may not exist

The agent's default prompt hardcodes `immersive-world.js` as the Three.js engine file, but `MEMORY.md` lists the actual active files as `experience-base.js`, `blackrose-experience.js`, etc. The `immersive-world.js` name is documented as retired in MEMORY.md ("Retired/non-existent names — do not resurrect"). Any SDK session using `SDKSceneBuilderAgent` will instruct Claude to read a non-existent file.

### G7: `enhanced_base.py:EnhancedAgentConfig` is unused

`EnhancedAgentConfig(BaseModel)` defines a full Pydantic config with `to_base_config()` backward compat method, but no current agent instantiates it. It's an intermediate refactor artifact that was never wired in.

### G8: Core sub-agent routing often references unregistered names

`CommerceCoreAgent.execute()` checks for `"product_manager"` and `"pricing_engine"` in `self._sub_agents`, but `_register_sub_agents()` registers `"product_ops"` and `"sdk_price_optimizer"`. The routing branches for those names will never match — they fall through to the legacy agent silently.

### G9: `TripoAssetAgent` uses `SuperAgent` from the legacy re-export path

`agents/tripo_agent.py` imports `SuperAgent` from `agents.core.base`. This resolves to `agents.base_legacy.SuperAgent` (the deprecated class) via the re-export at line ~779 of `core/base.py`. Tripo is wired into the round table orchestration via `orchestration/threed_round_table.py`.

### G10: `EliteDirector` (elite_web_builder) has its own internal `agents/` namespace

`elite_web_builder/director.py` imports `from agents.frontend_dev import FRONTEND_DEV_SPEC` — these are NOT the same `agents/` package as the top-level one. The elite web builder has its own local `agents/` sub-package with 8 specialist specs. This is a namespace collision that Python resolves correctly only if the import search path is configured correctly. Running `director.py` from the wrong CWD will import the wrong `agents`.

---

## 7. LLM Routing and Provider Selection

### CoreAgent / SubAgent path
Route: `SubAgent._llm_execute()` → `UnifiedLLMClient.complete(LLMRequest)` with `ExecutionMode` (FAST / BALANCED / ROUND_TABLE). Provider preference set via `preferred_provider` kwarg.

### EnhancedSuperAgent path
Route: `execute_auto()` → `_get_preferred_provider(task_category)` → `_route_to_provider()` → `LLMRouter` (COST strategy if temp<0.5, PRIORITY if ≥0.5) → fallback to `_execute_direct()` → `_backend_agent.run()` → fallback to `get_llm_router()`. Hard fail (`RuntimeError`) if no path works.

### Provider preference tables

**By agent type (`AGENT_PROVIDER_PREFERENCES`):**
- COMMERCE → [anthropic, openai, google]
- CREATIVE → [openai, anthropic, google]
- MARKETING → [google, anthropic, openai]
- SUPPORT → [anthropic, openai, google]
- OPERATIONS → [openai, anthropic, groq]
- ANALYTICS → [anthropic, openai, google]

**Round Table scoring weights:**
- relevance 0.25, quality 0.25, completeness 0.20, efficiency 0.15, brand_alignment 0.15

**High-stakes triggers** (→ Round Table):
- `HIGH_STAKES_AGENT_TYPES`: {commerce, operations}
- `HIGH_STAKES_TASK_TYPES`: 10 task types (payment, pricing, security, deployment, etc.)
- Prompt keyword scan (e.g., "payment", "delete", "production")

### SDK agents
`SDKCapabilityMixin._sdk_execute()` → `ClaudeSDKClient` with `model` from class-level `sdk_model` attr (haiku/sonnet/opus depending on agent complexity). `SDKSceneBuilderAgent` uses opus; most domain agents use sonnet; catalog readers use haiku.

---

## 8. Configuration, Environment Variables, and ML Models

### Environment variables consumed by agents/

| Variable | Consumer | Purpose |
|----------|----------|---------|
| `WORDPRESS_URL` | `WordPressAIBridge` | WordPress site URL (default: https://skyyrose.co) |
| `WP_AUTH_USER` / `WP_AUTH_PASS` | `WordPressAIBridge` | WordPress REST API auth |
| `FASHN_API_KEY` | `FashnTryOnAgent` | FASHN virtual try-on API |
| `TRIPO_API_KEY` | `TripoAssetAgent` | Tripo3D model generation |
| `GOOGLE_API_KEY` | `visual_generation/` | Imagen / Veo |
| `OPENAI_API_KEY` | Various | GPT providers |
| `ANTHROPIC_API_KEY` | Various | Claude providers |

### ML model configs per `EnhancedSuperAgent` subtype

| Agent type | Models configured |
|------------|-------------------|
| COMMERCE | Prophet (demand forecast), Ridge (pricing) |
| CREATIVE | ViT (image classification), custom |
| MARKETING | RoBERTa (sentiment), Prophet (trend) |
| SUPPORT | BART-MNLI (classification), LogisticRegression |
| OPERATIONS | IsolationForest (anomaly), Ridge |
| ANALYTICS | Prophet (forecast), KMeans (clustering) |

All models auto-fit with synthetic data if no real training data supplied (confidence=0.6).

### Prompt technique mapping (`TaskCategory → PromptTechnique`)

| Task Category | Default Technique |
|--------------|-------------------|
| REASONING | ChainOfThought |
| CLASSIFICATION | FewShot |
| CREATIVE | RoleBased |
| SEARCH | ReAct |
| QA | RAG |
| EXTRACTION | StructuredOutput |
| MODERATION | Constitutional |
| GENERATION | NegativePrompting |
| ANALYSIS | TreeOfThoughts |
| PLANNING | TreeOfThoughts |
| DEBUGGING | ReAct |
| OPTIMIZATION | SelfConsistency |

---

## 9. Testing Surface

### Tests relevant to agents/

- `tests/test_catalog_csv_integrity.py`: validates SKU counts and retired SKU codes (referenced by `SDKCatalogManagerAgent` prompt comments)
- No dedicated unit tests found for `SelfHealingMixin`, `LLMRoundTableInterface`, or `PromptEngineeringModule` in the agents/ directory itself
- Integration tests in `tests/integration/` (per CLAUDE.md convention) cover API endpoints that surface agents
- `agents/elite_web_builder/` has its own `tests/` subdirectory with tests for Director, tools (contrast_checker, file_validator, screenshot_diff, lighthouse_runner)

### What is NOT tested

- `SelfLearningModule.flush_rag_queue()` stub behavior
- ML auto-fit-with-synthetic-data fallback paths
- `WordPressAIBridge` REST integration (would require live WP site)
- Circuit breaker OPEN→HALF_OPEN→CLOSED state transitions
- `EnhancedSuperAgent` enterprise intelligence (DeepSeek + Claude verification)

---

## 10. Integration Points and Exposure

### API exposure (`api/agents.py`, `api/dashboard.py`)

- `CommerceCoreAgent`, `ContentCoreAgent`, and other core agents are wired into FastAPI routes
- `FashnTryOnAgent` exposed via `/api/v1/agents/fashn/tryon` with preflight cost gate
- `WordPressBridgeAgent` exposed via dashboard endpoints
- `FASHN_USD_PER_IMAGE = 0.075` is the single source of truth for pricing in cost-gate logic

### Orchestration pipelines

- `orchestration/asset_pipeline.py` — uses EnhancedSuperAgent layer
- `orchestration/threed_round_table.py` — wires `TripoAssetAgent` via `_get_tripo_agent()` lazy-load at line 552
- `orchestration/agent_counter.py` — tracks agent fleet status
- `orchestration/huggingface_3d_client.py` — async httpx + Pydantic; pattern to mirror for new 3D backends

### MCP exposure

- `mcp_servers/agent_bridge_server.py` — 20+ MCP tools surfacing agent capabilities
- `agents/wordpress_bridge/mcp_server.py` — 15 MCP tools for WordPress operations

### Ralph integration

- `agents/elite_web_builder/core/ralph_integration.py:RalphExecutor` — Ralph drives the Director
- `WebBuilderCoreAgent._get_director()` → `EliteDirector` → `Director`

### 3D portal (React Three Fiber)

- `CoreAgent.to_portal_node()`, `SubAgent.to_portal_node()`, `Orchestrator.to_portal_graph()` — serialize the entire agent fleet as nodes + connections for the 3D dashboard portal

---

*Digest path: `/Users/theceo/DevSkyy/tasks/codebase-digest/agents.md`*
