# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

### Python Backend
```bash
make dev          # Install all dependencies (Python + TypeScript)
make test         # Run pytest
make test-cov     # pytest with coverage report
make lint         # Ruff + mypy checking
make format       # isort + ruff + black formatting
make ci           # Full CI pipeline (lint + test + coverage)
```

### TypeScript/Node.js
```bash
npm run build           # TypeScript compilation
npm run dev             # Development server with nodemon
npm run test            # Jest testing
npm run test:watch      # Watch mode testing
npm run lint            # ESLint checking
npm run lint:fix        # ESLint auto-fix
npm run type-check      # TypeScript strict mode check
```

### Next.js Frontend Dashboard
```bash
cd frontend
npm run dev             # Next.js dev server (port 3000)
npm run build           # Production build
npm run type-check      # TypeScript validation
```

### 3D Collection Demos
```bash
npm run demo:black-rose   # Gothic rose garden experience
npm run demo:signature    # Luxury outdoor experience
npm run demo:love-hurts   # Castle ballroom experience
npm run demo:showroom     # Virtual showroom
npm run demo:runway       # Fashion runway
```

## Architecture Overview

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
- PydanticAI, LangChain, LangGraph, Google ADK, CrewAI, AutoGen

### Visual Generation (`agents/visual_generation.py`)
Google + HuggingFace handle ALL imagery with SkyyRose brand assets:
- **Google Imagen 3**: Text-to-image
- **Google Veo 2**: Text-to-video
- **HuggingFace FLUX.1**: High-quality image generation
- **Tripo3D**: 3D model generation
- **FASHN**: Virtual try-on

### Frontend Architecture
- **`src/collections/`**: 5 immersive Three.js experiences (Black Rose, Signature, Love Hurts, Showroom, Runway)
- **`frontend/`**: Next.js 15 dashboard with agent control, Round Table viewer, A/B testing dashboard, tools browser

### Security (`security/`)
Enterprise security modules: AES-256-GCM encryption, JWT/OAuth2, Argon2id hashing, PII protection, SSRF prevention, rate limiting

## Key Patterns

### Tool Execution
Tools are registered in `runtime/tools.py` with schema validation. Execute via:
```python
result = await agent.use_tool("tool_name", {"param": "value"})
```

### LLM Round Table Flow
1. All 6 LLMs generate responses in parallel
2. Responses scored on relevance, coherence, completeness, creativity
3. Top 2 finalists go through A/B testing
4. Winner determined by statistical significance
5. Results persisted to Neon PostgreSQL

### Prompt Technique Selection
`base_super_agent.py` auto-selects technique based on `TaskCategory`:
- reasoning → chain_of_thought
- classification → few_shot
- creative → tree_of_thoughts
- search → react
- qa → rag

## Database
- **Neon PostgreSQL**: Serverless, connection pooling via `DATABASE_URL`
- **Vector Stores**: Chroma (local), Pinecone (production)
- **Redis**: Caching and task queues

## Deployment
- **Vercel**: Full-stack serverless (`vercel.json` at root)
- **Docker**: `make docker-build && make docker-run`

## Brand Context
SkyyRose brand DNA is injected into all visual generation:
```python
SKYYROSE_BRAND_DNA = {
    "name": "SkyyRose",
    "tagline": "Where Love Meets Luxury",
    "colors": {"primary": "#B76E79", "secondary": "#1A1A1A"},
    "style_keywords": ["premium", "sophisticated", "bold", "elegant", "luxury"]
}
```
