# Dependencies Codemap

<!-- Generated: 2026-07-06 | Files scanned: pyproject.toml deps, requirements-imagery.txt, llm/providers/ (11 files), package.json | Token estimate: ~700 -->

## External services

| Service | Used by | Notes |
|---|---|---|
| WooCommerce REST (`/wp-json/wc/v3`) | `wordpress/products.py`, `agents/wordpress_bridge/` | BasicAuth via `.env.wordpress` keys; on WP.com use `index.php?rest_route=` (not `/wp-json/`, which 401s) |
| WordPress.com (SFTP deploy + MCP) | `scripts/deploy-theme.sh`, WP.com MCP server | SSH key `~/.ssh/skyyrose-deploy`, server `sftp.wp.com` |
| Vercel | `frontend/` (devskyy.app), `api/index.py` serverless mirror | `vercel.json`; use npm not pnpm (Node 22 `ERR_INVALID_THIS`) |
| OpenAI gpt-image-2 | `scripts/oai_render/` (client.py, pipeline.py) | Canonical NEW-render engine; paid, STOP-AND-SHOW gated (`oai-render-run.py generate --yes`) |
| Pinecone | `orchestration/vector_store.py` | Index `skyyrose-catalog`, region us-west-2, dim=1024, cosine, Standard plan |
| Meshy / Tripo3D | `ai_3d/providers/{meshy,tripo}.py`, `agents/{meshy,tripo}_agent.py` | 3D generation; Tripo has separate `.ai`/`.com` regions with separate API keys |
| FASHN | `agents/fashn_agent.py` | Virtual try-on API; paid, STOP-AND-SHOW gated |
| Stripe | `src/lib/stripeIntegration.ts` (legacy SDK), `frontend/app/api/checkout` | Payments |
| Klaviyo | `inc/klaviyo-integration.php` | Email marketing |
| Sentry | `sentry-sdk` (backend), `@sentry/nextjs` (frontend) | Error monitoring |

## LLM providers — 11 adapters, not 6 (verified this pass)

`llm/providers/`: `anthropic.py`, `openai.py`, `google.py`, `mistral.py`, `cohere.py`, `groq.py` (the "6" cited in root CLAUDE.md) **plus** `deepseek.py`, `replicate.py`, `stability.py`, `vertex_imagen.py`, `litellm_provider.py` (generic gateway). The latter 5 are undocumented in root CLAUDE.md and are mostly image/video-generation oriented rather than chat LLMs. Routing chain: `llm/router.py` → `llm/task_classifier.py` → `llm/tournament.py` → `llm/round_table.py` (consensus) → `llm/verification.py`.

## Key Python package versions (pyproject.toml)

| Package | Version | Purpose |
|---|---|---|
| fastapi | >=0.104 | HTTP framework |
| sqlalchemy / alembic | >=2.0 / >=1.13 | ORM + migrations |
| anthropic | >=0.75.0 | Claude SDK |
| google-genai | >=1.50.0 | Gemini SDK |
| claude-agent-sdk | >=0.1.0 | Multi-agent orchestration |
| strawberry-graphql[fastapi] | >=0.217.0 | GraphQL |
| mcp | >=1.23.0 | MCP protocol (pinned past CVE-2025-53365/-53366/-66416) |
| tripo3d | >=0.4.1 | 3D generation SDK |
| voyageai | >=0.2.4 | RAG-optimized embeddings |

## Key Node/frontend dependencies

| Package | Purpose |
|---|---|
| next 16 / react 19 | Dashboard framework |
| next-auth v4 | Admin auth (`frontend/proxy.ts` gate) |
| three / @react-three/fiber+drei | 3D (legacy `src/` SDK — the live theme uses vanilla Three.js in `front-page.php` instead) |
| zustand | Cart state persistence |
| @tanstack/react-query | Server data fetching |

## Never cross-wire

devskyy.app (dashboard) and skyyrose.co (WordPress) are separate deployables with separate credential sets — never point one system's client at the other's admin API.

## Related codemaps

[backend.md](backend.md) (LLM routing consumers) · [frontend.md](frontend.md) · [architecture.md](architecture.md)
