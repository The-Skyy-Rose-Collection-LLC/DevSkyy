# Technology Stack

**Analysis Date:** 2026-03-07

## Languages

**Primary:**
- TypeScript 5.9.3 - Core development language for backend and frontend
- Python - MCP servers and automation scripts

**Secondary:**
- JavaScript/JSX - Legacy code and configuration

## Runtime

**Environment:**
- Node.js >= 22 - Primary runtime for backend services
- npm >= 10 - Package manager

**Package Manager:**
- npm - Primary package manager
- Lockfile: `package-lock.json` (present)

## Frameworks

**Core (Backend):**
- Express 5.2.1 - Legacy HTTP server
- Fastify 5.8.1 - Modern HTTP server with better performance
- Next.js 16.1.6 - Frontend framework and API routes
- Nuxt 4.2.2 - Alternative Vue.js framework

**Core (Frontend):**
- React 19.2.3 - UI library
- Next.js 16 - React framework for frontend
- Tailwind CSS 4 - Utility-first CSS framework
- Radix UI - Unstyled component primitives

**3D/Graphics:**
- Three.js 0.182.0 - 3D rendering engine
- React Three Fiber 9.5.0 - React renderer for Three.js
- React Three Drei 10.7.7 - Useful helpers for R3F
- React Three Postprocessing 3.0.4 - Post-processing effects
- @pixiv/three-vrm 3.4.5 - VRM model support

**Testing:**
- Jest 30.2.0 - Unit testing
- Vitest 4.0.18 - Fast test runner
- Playwright 1.58.2 - E2E testing
- Testing Library - React component testing

**Build/Dev:**
- Vite 7.2.7 - Build tool
- Webpack 5.104.1 - Module bundler
- TypeScript 5.9.3 - Type checking and compilation
- ts-node - TypeScript execution
- tsx - TypeScript executor

## Key Dependencies

**AI/ML:**
- ai 6.0.97 - AI SDK (Vercel)
- @ai-sdk/openai 3.0.31 - OpenAI SDK
- @ai-sdk/anthropic 3.0.46 - Anthropic SDK
- @ai-sdk/google 3.0.30 - Google AI SDK
- @ai-sdk/google-vertex 4.0.61 - Google Vertex AI
- @ai-sdk/groq 3.0.24 - Groq SDK
- @ai-sdk/cohere 3.0.21 - Cohere SDK
- @ai-sdk/mistral 3.0.20 - Mistral AI
- @ai-sdk/amazon-bedrock 4.0.63 - AWS Bedrock
- openai 6.24.0 - Legacy OpenAI client
- @anthropic-ai/sdk 0.73.0 - Legacy Anthropic client
- langchain 1.2.26 - LLM framework

**Database:**
- @prisma/client 7.3.0 - Prisma ORM
- prisma 7.1.0 - Database tools
- drizzle-orm 0.45.1 - Drizzle ORM
- @neondatabase/serverless 1.0.2 - Neon serverless driver
- mongodb 7.0.0 - MongoDB driver
- mongoose 9.0.1 - MongoDB ODM

**Caching:**
- redis 5.10.0 - Redis client
- ioredis 5.8.2 - Advanced Redis client
- @upstash/redis 1.36.2 - Upstash Redis
- @upstash/ratelimit 2.0.8 - Rate limiting
- @upstash/qstash 2.9.0 - Message queue
- @upstash/vector 1.2.2 - Vector database

**Search/Vector:**
- @pinecone-database/pinecone 7.1.0 - Pinecone vector DB
- chromadb 3.3.1 - ChromaDB vector store

**Authentication:**
- next-auth 4.24.13 - Next.js authentication
- @auth/core 0.34.3 - Auth.js core

**Payments:**
- stripe 20.3.1 - Stripe SDK
- @stripe/stripe-js 8.8.0 - Stripe.js client

**E-commerce:**
- WooCommerce REST API - E-commerce backend
- Facebook Business SDK 24.0.1 - Meta ads integration

**Communication:**
- socket.io 4.8.1 - WebSocket server
- socket.io-client 4.8.1 - WebSocket client
- bullmq 5.70.1 - Message queue
- amqplib 0.10.9 - AMQP library

**Email:**
- resend 6.9.2 - Email service

**File/Storage:**
- @vercel/blob 2.3.0 - Vercel Blob storage
- sharp 0.34.5 - Image processing
- uploadthing 7.7.4 - File uploads

**Monitoring:**
- @sentry/nextjs 10.38.0 - Error tracking
- @sentry/node 10.40.0 - Node error tracking
- @opentelemetry/api 1.9.0 - Observability
- @vercel/analytics 1.6.1 - Analytics

**HTTP/API:**
- axios 1.13.5 - HTTP client
- zod 4.3.6 - Schema validation

**UI Components:**
- framer-motion 12.30.0 - Animations
- lucide-react 0.562.0 - Icons
- recharts 3.6.0 - Charts
- sonner 2.0.7 - Toast notifications
- vaul 1.1.2 - Drawer component

## Configuration

**Environment:**
- Environment variables via `process.env`
- Configuration files: `src/config/index.ts`, `.env` files
- Key configs: Database, Redis, AI providers, WordPress

**Build:**
- TypeScript: `config/typescript/tsconfig.json`
- Frontend: `frontend/next.config.ts`
- Testing: `config/testing/jest.config.cjs`
- Vite: `config/vite/demo.config.ts`

## Platform Requirements

**Development:**
- Node.js >= 22
- npm >= 10
- TypeScript knowledge

**Production:**
- Vercel (frontend/API)
- PostgreSQL-compatible database (Neon)
- Redis (Upstash)
- WordPress/WooCommerce hosting (separate)

---

*Stack analysis: 2026-03-07*
