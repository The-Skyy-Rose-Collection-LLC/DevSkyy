# External Integrations

**Analysis Date:** 2026-03-07

## APIs & External Services

**AI Providers:**
- OpenAI - Text completion, chat, image generation, embeddings
  - SDK: `@ai-sdk/openai`, `openai`
  - Auth: `OPENAI_API_KEY` env var
  - Used in: `src/services/OpenAIService.ts`, `src/config/index.ts`

- Anthropic (Claude) - AI chat completion
  - SDK: `@ai-sdk/anthropic`, `@anthropic-ai/sdk`
  - Auth: `ANTHROPIC_API_KEY` env var

- Google AI (Gemini) - Multimodal AI
  - SDK: `@ai-sdk/google`, `@google/genai`
  - Auth: `GOOGLE_AI_API_KEY` env var

- Google Vertex AI - Enterprise AI on Google Cloud
  - SDK: `@ai-sdk/google-vertex`
  - Auth: GCP credentials

- Groq - Fast inference
  - SDK: `@ai-sdk/groq`
  - Auth: `GROQ_API_KEY`

- Cohere - NLP and embeddings
  - SDK: `@ai-sdk/cohere`

- Mistral AI
  - SDK: `@ai-sdk/mistral`

- Amazon Bedrock - AWS AI services
  - SDK: `@ai-sdk/amazon-bedrock`

- xAI (Grok)
  - SDK: `@ai-sdk/xai`

**LangChain Integration:**
- langchain 1.2.26 - LLM application framework
- @langchain/core, @langchain/openai, @langchain/anthropic
- Used in: Agent orchestration and RAG pipelines

## Data Storage

**Primary Database:**
- PostgreSQL via Neon (serverless)
  - Client: `@neondatabase/serverless`
  - Connection: `DATABASE_URL` env var
  - Used in: `src/config/index.ts` (databaseConfig)

**ORMs:**
- Prisma 7.3.0 - Database ORM
  - Schema: Not detected (prisma directory missing)
  - Used in: Backend services
- Drizzle ORM 0.45.1 - Lightweight ORM
  - Used in: Alternative database layer

**Development Database:**
- SQLite (aiosqlite)
  - Connection: `sqlite+aiosqlite:///./devskyy.db`
  - Used for: Local development

**MongoDB:**
- mongodb 7.0.0 - NoSQL database
- mongoose 9.0.1 - MongoDB ODM
  - Connection: `MONGODB_URL` env var

**Caching:**
- Redis
  - Client: `redis`, `ioredis`
  - Upstash provider: `@upstash/redis`
  - Connection: `REDIS_URL` or `redisConfig` env vars
  - Used in: `src/config/index.ts`

**Vector Database:**
- Pinecone
  - SDK: `@pinecone-database/pinecone`
  - Auth: `PINECONE_API_KEY` env var
  - Used in: Semantic search and RAG

- ChromaDB
  - Client: `chromadb`
  - Used in: Local vector storage

**File Storage:**
- Vercel Blob
  - SDK: `@vercel/blob`
  - Used in: `frontend/lib/` file handling

## Authentication & Identity

**Primary Auth:**
- NextAuth.js v4 - Authentication for Next.js
  - Config: `frontend/lib/auth.ts`
  - Providers: Credentials (JWT-based)
  - Auth endpoint: `frontend/app/api/auth/[...nextauth]/route.ts`
  - Auth URL: `POST /api/v1/auth/token` (backend)
  - Session: JWT strategy with 15-minute max age
  - Env vars: `NEXTAUTH_SECRET`, `NEXTAUTH_URL`

**JWT:**
- JWT-based authentication
- Config: `src/config/index.ts` (jwtConfig)
- Token expiry: 24h default, refresh token 7d

## E-commerce

**WooCommerce:**
- WordPress e-commerce platform
- Integration: `src/collections/WooCommerceProductLoader.ts`
- REST API v3: `wc/v3/`
- Auth: WooCommerce Consumer Key/Secret
- Env vars: `WOOCOMMERCE_KEY`, `WOOCOMMERCE_SECRET`
- Features: Product loading, collections, variations, AR products

**WordPress REST API:**
- WordPress content management
- Proxy: `frontend/app/api/wordpress/proxy/route.ts`
- Env vars: `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD`
- Used in: Content sync, menu management, operations

## Payments

**Stripe:**
- Payment processing
- SDK: `stripe` (server), `@stripe/stripe-js` (client)
- Integration: `src/lib/stripeIntegration.ts`, `frontend/lib/stripe/`
- Env vars: `STRIPE_API_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- Features: Payment intents, Elements, webhooks

## 3D & AR Services

**HuggingFace:**
- 3D model generation (Hunyuan3D, TripoSR)
- SDK: `@huggingface/inference`, `@huggingface/hub`
- Env vars: `HF_TOKEN`, `HF_HOME`
- Models: `tencent/Hunyuan3D-2`, `stabilityai/TripoSR`

**Tripo3D:**
- 3D asset generation API
- Env vars: `TRIPO_API_KEY`, `TRIPO_API_BASE_URL`
- API: `frontend/lib/tripo/client.ts`

**Fashn.ai:**
- Virtual try-on service
- Env vars: `FASHN_API_KEY`, `FASHN_API_BASE_URL`

**Google Model Viewer:**
- Web component for 3D/AR
- SDK: `@google/model-viewer`

## Marketing

**Facebook Business SDK:**
- Meta advertising integration
- SDK: `facebook-nodejs-business-sdk`
- Env vars: `FACEBOOK_ACCESS_TOKEN`

**Klaviyo:**
- Email marketing automation
- Env vars: `KLAVIYO_PRIVATE_KEY`, `KLAVIYO_PUBLIC_KEY`, `KLAVIYO_LIST_ID`

**Resend:**
- Email delivery service
- SDK: `resend`
- Used for: Transactional emails

## Monitoring & Observability

**Sentry:**
- Error tracking and performance monitoring
- SDK: `@sentry/nextjs`, `@sentry/node`
- Env vars: `SENTRY_DSN`
- Used in: Frontend and backend error handling

**OpenTelemetry:**
- Distributed tracing
- SDK: `@opentelemetry/api`, `@opentelemetry/sdk-node`
- Exporters: OTLP HTTP
- Used in: Backend observability

**Vercel Analytics:**
- Frontend analytics
- SDK: `@vercel/analytics`

**Vercel Speed Insights:**
- Performance monitoring
- SDK: `@vercel/speed-insights`

## MCP (Model Context Protocol)

**MCP Servers:**
- Python-based MCP implementations
- Located in: `mcp_servers/`
- Files: `orchestrator.py`, `rag_server.py`, `openai_server.py`, etc.

**WordPress.com MCP:**
- WordPress.com integration
- Location: `mcp_servers/wordpress-com/`

## CI/CD & Deployment

**Hosting:**
- Vercel - Frontend and API routes deployment
- Frontend: `frontend/package.json` deploy scripts

**CI Pipeline:**
- GitHub Actions (implied by repository structure)
- Playwright for E2E testing

## Environment Configuration

**Required env vars:**
- `NODE_ENV` - Environment (development/production)
- `NEXTAUTH_SECRET` - Auth secret
- `JWT_SECRET_KEY` - JWT signing
- `ENCRYPTION_MASTER_KEY` - Data encryption

**Database:**
- `DATABASE_URL` - PostgreSQL/SQLite connection

**AI Services:**
- `OPENAI_API_KEY` - OpenAI
- `ANTHROPIC_API_KEY` - Anthropic
- `GOOGLE_AI_API_KEY` - Google AI
- `HF_TOKEN` - HuggingFace

**E-commerce:**
- `WORDPRESS_URL` - WordPress site
- `WOOCOMMERCE_KEY`, `WOOCOMMERCE_SECRET` - WooCommerce API

**Payments:**
- `STRIPE_API_KEY`, `STRIPE_PUBLISHABLE_KEY` - Stripe

**Secrets location:**
- `.env` - Root project
- `.env.local` - Frontend (not committed)
- Server-side env vars in Vercel project settings

## Webhooks & Callbacks

**Incoming:**
- Stripe webhooks - Payment events
- WordPress webhooks - Content updates (if configured)

**Outgoing:**
- Stripe webhook delivery - `/api/stripe/webhook`
- WordPress REST API calls - Via proxy

---

*Integration audit: 2026-03-07*
