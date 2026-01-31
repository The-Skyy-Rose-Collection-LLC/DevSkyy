# DevSkyy Data Flow Documentation

**Version**: 1.3.0
**Last Updated**: 2026-01-30
**Status**: Production

This document describes how data flows through the DevSkyy platform for key operations.

---

## Table of Contents

1. [HTTP Request Flow](#http-request-flow)
2. [Authentication Flow](#authentication-flow)
3. [Agent Execution Flow](#agent-execution-flow)
4. [RAG Pipeline Flow](#rag-pipeline-flow)
5. [WordPress Sync Workflow](#wordpress-sync-workflow)
6. [3D Generation Pipeline](#3d-generation-pipeline)
7. [Virtual Try-On Flow](#virtual-try-on-flow)

---

## HTTP Request Flow

Every HTTP request follows this path through the system:

```mermaid
sequenceDiagram
    participant Client
    participant CORS as CORS Middleware
    participant Security as Security Layer
    participant Router as FastAPI Router
    participant Agent as Agent/Handler
    participant Orchestration
    participant Services
    participant Database

    Client->>CORS: HTTP Request
    CORS->>CORS: Validate Origin
    CORS->>Security: Forward Request

    Security->>Security: Extract JWT Token
    Security->>Security: Validate Token
    Security->>Security: Check Rate Limit
    Security->>Security: Sanitize Input
    Security->>Security: Log Audit Event

    alt Invalid Token
        Security-->>Client: 401 Unauthorized
    end

    alt Rate Limited
        Security-->>Client: 429 Too Many Requests
    end

    Security->>Router: Authenticated Request
    Router->>Router: Route to Handler

    Router->>Agent: Dispatch to Agent
    Agent->>Orchestration: Get Context/Route LLM
    Orchestration->>Services: Execute Business Logic
    Services->>Database: Read/Write Data

    Database-->>Services: Data Response
    Services-->>Orchestration: Service Result
    Orchestration-->>Agent: Context/LLM Response
    Agent-->>Router: Agent Result

    Router-->>Security: Response
    Security->>Security: Mask Sensitive Data
    Security-->>Client: HTTP Response
```

### Request Processing Steps

| Step | Component | Actions |
|------|-----------|---------|
| 1 | CORS Middleware | Validate `Origin` header, add CORS headers |
| 2 | Correlation ID | Generate/extract `X-Correlation-ID` |
| 3 | JWT Validation | Decode token, verify signature, check expiry |
| 4 | Rate Limiting | Check request count against tier limits |
| 5 | Input Sanitization | XSS/SQLi prevention, HTML cleaning |
| 6 | Audit Logging | Log request details (sanitized) |
| 7 | Route Dispatch | Match URL to handler function |
| 8 | Business Logic | Execute handler with validated input |
| 9 | Response Masking | Redact sensitive fields in response |
| 10 | Response | Return JSON with correlation ID |

---

## Authentication Flow

### Login Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as /auth/login
    participant AuthProvider as JWTAuthProvider
    participant PasswordHasher as Argon2Hasher
    participant TokenBlacklist
    participant Database

    Client->>API: POST {username, password}
    API->>API: Validate Input Schema

    API->>Database: Find User by Username
    Database-->>API: User Record

    alt User Not Found
        API-->>Client: 401 Invalid Credentials
    end

    API->>PasswordHasher: Verify Password
    PasswordHasher-->>API: Match Result

    alt Password Mismatch
        API->>Database: Increment Failed Attempts
        API-->>Client: 401 Invalid Credentials
    end

    alt Account Locked
        API-->>Client: 403 Account Locked
    end

    API->>AuthProvider: Generate Token Pair
    AuthProvider->>AuthProvider: Create Access Token (15 min)
    AuthProvider->>AuthProvider: Create Refresh Token (7 days)
    AuthProvider-->>API: TokenResponse

    API->>Database: Update Last Login
    API-->>Client: {access_token, refresh_token, expires_in}
```

### Token Refresh Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as /auth/refresh
    participant Validator as TokenValidator
    participant Blacklist as TokenBlacklist
    participant AuthProvider

    Client->>API: POST {refresh_token}

    API->>Validator: Validate Refresh Token
    Validator->>Validator: Decode JWT
    Validator->>Validator: Check Token Type

    alt Invalid Token Type
        Validator-->>Client: 401 Invalid Token
    end

    Validator->>Blacklist: Check if Revoked
    Blacklist-->>Validator: Revocation Status

    alt Token Revoked
        Validator-->>Client: 401 Token Revoked
    end

    Validator-->>API: TokenPayload

    API->>AuthProvider: Generate New Tokens
    Note over AuthProvider: Implements Token Rotation
    AuthProvider->>Blacklist: Revoke Old Refresh Token
    AuthProvider-->>API: New TokenResponse

    API-->>Client: {access_token, refresh_token, expires_in}
```

---

## Agent Execution Flow

### SuperAgent Plan-Execute-Validate Pattern

```mermaid
flowchart TB
    subgraph Input
        REQ[User Request]
        CTX[Correlation ID]
    end

    subgraph Plan["1. PLAN Phase"]
        TECH[Select Prompt Technique]
        STEPS[Generate Plan Steps]
    end

    subgraph Retrieve["2. RETRIEVE Phase"]
        RAG[RAG Context Manager]
        BRAND[Brand Context]
        TOOLS[Tool Registry]
    end

    subgraph Execute["3. EXECUTE Phase"]
        LLM[LLM Router]
        TOOL_EXEC[Tool Execution]
        MULTI[Parallel Step Execution]
    end

    subgraph Validate["4. VALIDATE Phase"]
        SCHEMA[Schema Validation]
        QUALITY[Quality Checks]
        SAFETY[Safety Filters]
    end

    subgraph Emit["5. EMIT Phase"]
        FORMAT[Format Response]
        AUDIT[Audit Log]
        RESULT[Return Result]
    end

    REQ --> TECH
    CTX --> TECH
    TECH --> STEPS
    STEPS --> RAG
    RAG --> BRAND
    BRAND --> TOOLS
    TOOLS --> LLM
    LLM --> TOOL_EXEC
    TOOL_EXEC --> MULTI
    MULTI --> SCHEMA
    SCHEMA --> QUALITY
    QUALITY --> SAFETY
    SAFETY --> FORMAT
    FORMAT --> AUDIT
    AUDIT --> RESULT
```

### Prompt Technique Selection

The SuperAgent selects from 17 prompt techniques based on task classification:

| Technique | Use Case | Task Types |
|-----------|----------|------------|
| Chain of Thought | Complex reasoning | Analysis, planning |
| Few-Shot | Pattern matching | Classification |
| Tree of Thought | Multi-path exploration | Creative, research |
| ReAct | Tool-using tasks | Actions, integrations |
| Self-Consistency | High-stakes decisions | Validation |
| Persona | Role-based responses | Customer service |
| Structured Output | Data extraction | Forms, APIs |

---

## RAG Pipeline Flow

### Document Retrieval Flow

```mermaid
flowchart TB
    subgraph Query["Query Processing"]
        Q[User Query]
        QR[Query Rewriter]
        EXP[Expanded Queries]
    end

    subgraph Retrieval["Retrieval"]
        EMB[Embedding Engine]
        VS[Vector Store]
        CANDS[Candidate Documents]
    end

    subgraph Reranking["Reranking"]
        RR[Cross-Encoder Reranker]
        TOP[Top-K Results]
    end

    subgraph Context["Context Assembly"]
        BC[Brand Context]
        CTX[RAG Context]
    end

    Q --> QR
    QR --> EXP
    EXP --> EMB
    EMB --> VS
    VS --> CANDS
    CANDS --> RR
    RR --> TOP
    TOP --> BC
    BC --> CTX
```

### RAG Pipeline Components

```
orchestration/
  rag_context_manager.py    # Orchestrates retrieval
      |
      +-- query_rewriter.py      # Expands user queries
      +-- embedding_engine.py    # Text to vectors
      +-- vector_store.py        # ChromaDB/FAISS
      +-- reranker.py            # Cross-encoder scoring
      +-- brand_context.py       # SkyyRose DNA
```

### Query Expansion Example

```python
# Input Query
"What rose gold accessories do you have?"

# Expanded Queries (via QueryRewriter)
[
    "rose gold accessories jewelry fashion",
    "gold-toned accessories SkyyRose collection",
    "metallic rose accessories luxury fashion",
]

# Retrieved Documents (Top 5 after reranking)
1. "Rose Gold Heart Earrings - Signature Collection" (score: 0.94)
2. "Rose Gold Charm Bracelet - Love Hurts" (score: 0.91)
3. "SkyyRose Rose Gold Design Philosophy" (score: 0.87)
...
```

---

## WordPress Sync Workflow

### Product Sync Flow

```mermaid
sequenceDiagram
    participant API as DevSkyy API
    participant Sync as Sync Pipeline
    participant Transform as Data Transformer
    participant WP as WordPress/WooCommerce
    participant R2 as Cloudflare R2

    API->>Sync: Trigger Product Sync
    Sync->>Sync: Load Pending Products

    loop For Each Product
        Sync->>Transform: Transform to WC Format
        Transform->>Transform: Map Categories
        Transform->>Transform: Format Prices
        Transform->>Transform: Generate SEO

        alt Has New Images
            Sync->>R2: Upload Product Images
            R2-->>Sync: CDN URLs
        end

        Transform-->>Sync: WC Product Data

        Sync->>WP: POST /wp-json/wc/v3/products
        WP-->>Sync: Product Response

        alt Sync Failed
            Sync->>Sync: Queue for Retry
            Sync->>API: Report Error
        end

        Sync->>API: Update Local Record
    end

    Sync-->>API: Sync Summary
```

### WordPress API Integration

```
DevSkyy                          WordPress
   |                                 |
   |  POST /index.php?rest_route=   |
   |  /wc/v3/products               |
   |------------------------------->|
   |                                 |
   |  WooCommerce Product ID        |
   |<-------------------------------|
   |                                 |
   |  POST /wp-json/wp/v2/media     |
   |------------------------------->|
   |                                 |
   |  Media Attachment ID           |
   |<-------------------------------|
```

**Important**: WordPress.com uses `index.php?rest_route=` prefix, NOT `/wp-json/`.

---

## 3D Generation Pipeline

### Tripo3D Generation Flow

```mermaid
flowchart TB
    subgraph Input["Input Processing"]
        PROMPT[Text Prompt]
        REF[Reference Image]
        OPTS[Generation Options]
    end

    subgraph Generation["3D Generation"]
        TRIPO[Tripo3D API]
        TASK[Task Creation]
        POLL[Status Polling]
        MODEL[Raw 3D Model]
    end

    subgraph Optimization["Mesh Optimization"]
        DECIMATE[Vertex Decimation]
        NORMAL[Normal Recalculation]
        UV[UV Unwrapping]
    end

    subgraph Export["Export & Quality"]
        GLB[glTF/GLB Export]
        THUMB[Thumbnail Generation]
        SCORE[Fidelity Scoring]
    end

    subgraph Storage["Storage & Delivery"]
        R2[Cloudflare R2]
        CDN[CDN Distribution]
        META[Metadata Storage]
    end

    PROMPT --> TRIPO
    REF --> TRIPO
    OPTS --> TRIPO
    TRIPO --> TASK
    TASK --> POLL
    POLL --> MODEL
    MODEL --> DECIMATE
    DECIMATE --> NORMAL
    NORMAL --> UV
    UV --> GLB
    GLB --> THUMB
    THUMB --> SCORE
    SCORE --> R2
    R2 --> CDN
    CDN --> META
```

### Quality Targets

| Metric | Target | Enforcement |
|--------|--------|-------------|
| Fidelity Score | > 0.95 | Quality gate blocks low-quality assets |
| Generation Time | < 30s | Timeout with retry |
| Vertex Count | < 100k | Automatic decimation |
| File Size | < 10MB | Compression applied |

### Pipeline Error Handling

```python
async def generate_3d_model(prompt: str, reference_image: str | None = None):
    """3D generation with retry and fallback"""
    max_retries = 3
    base_delay = 2.0

    for attempt in range(max_retries):
        try:
            task = await tripo_client.create_task(
                prompt=prompt,
                image_url=reference_image,
            )
            result = await wait_for_task(task.id, timeout=60)

            if result.fidelity_score < 0.95:
                raise QualityGateError("Fidelity below threshold")

            return result

        except (TimeoutError, QualityGateError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
            raise

    raise MaxRetriesExceededError("3D generation failed after retries")
```

---

## Virtual Try-On Flow

### FASHN API Integration

```mermaid
sequenceDiagram
    participant User
    participant API as Try-On API
    participant Agent as FASHN Agent
    participant FASHN as FASHN API
    participant Storage as R2 Storage

    User->>API: POST /virtual-tryon
    Note over API: {model_image, garment_image}

    API->>Agent: Process Try-On Request
    Agent->>Storage: Validate/Upload Images
    Storage-->>Agent: Image URLs

    Agent->>FASHN: POST /try-on
    Note over FASHN: {model_url, garment_url, category}

    FASHN->>FASHN: Generate Try-On
    Note over FASHN: ~10-30 seconds

    FASHN-->>Agent: Try-On Result
    Note over Agent: {result_url, confidence}

    Agent->>Storage: Store Result Image
    Storage-->>Agent: Permanent URL

    Agent-->>API: TryOnResult
    API-->>User: {result_url, confidence, metadata}
```

### Try-On Categories

| Category | Description | Garment Types |
|----------|-------------|---------------|
| tops | Upper body | Shirts, blouses, jackets |
| bottoms | Lower body | Pants, skirts, shorts |
| dresses | Full body | Dresses, jumpsuits |
| outerwear | Outer layer | Coats, blazers |

---

## Data Flow Summary

### Request Types and Paths

| Request Type | Entry Point | Key Components | Data Stores |
|--------------|-------------|----------------|-------------|
| Auth | `/auth/*` | Security Layer | PostgreSQL, Redis |
| Agent Task | `/api/v1/agents/*` | SuperAgent, LLM Router | Vector Store, LLM APIs |
| RAG Query | `/api/v1/rag/*` | RAG Pipeline | ChromaDB, Embeddings |
| WordPress Sync | `/api/v1/wordpress/*` | Sync Pipeline | WooCommerce API, R2 |
| 3D Generation | `/api/v1/3d/*` | Tripo Pipeline | Tripo API, R2, PostgreSQL |
| Virtual Try-On | `/api/v1/tryon/*` | FASHN Agent | FASHN API, R2 |

---

## See Also

- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) - Layer responsibilities
- [COMPONENTS.md](./COMPONENTS.md) - Component details
- [../RAG_INTEGRATION.md](../RAG_INTEGRATION.md) - RAG setup guide
- [../3D_GENERATION_PIPELINE.md](../3D_GENERATION_PIPELINE.md) - 3D pipeline details
