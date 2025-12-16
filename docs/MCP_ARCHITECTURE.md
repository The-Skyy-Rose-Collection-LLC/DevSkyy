# DevSkyy MCP Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Assistants Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Claude     │  │   ChatGPT    │  │  Other MCP   │          │
│  │   Desktop    │  │   Desktop    │  │   Clients    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    Model Context Protocol
                             │
┌─────────────────────────────┴─────────────────────────────────┐
│                      MCP Servers Layer                         │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           DevSkyy Custom MCP Servers                   │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │ devskyy-openai   │    │  devskyy-main    │         │   │
│  │  │                  │    │                  │         │   │
│  │  │ • GPT-4o         │    │ • 54 AI Agents   │         │   │
│  │  │ • Vision         │    │ • WordPress      │         │   │
│  │  │ • Code Gen       │    │ • WooCommerce    │         │   │
│  │  │ • Functions      │    │ • SEO/Content    │         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           Standard MCP Servers                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │filesystem│ │   git    │ │  github  │ │ postgres │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │sequential│ │  brave   │ │  fetch   │ │  memory  │  │   │
│  │  │ thinking │ │  search  │ │          │ │          │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────────┐
│                    DevSkyy Platform Layer                      │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Core Platform Services                    │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │  FastAPI Server  │    │  Agent Registry  │         │   │
│  │  │  (Port 8000)     │    │  (54 Agents)     │         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │  LLM Orchestrator│    │  WordPress Client│         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Data & Storage Layer                      │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │   PostgreSQL     │    │      Redis       │         │   │
│  │  │   Database       │    │      Cache       │         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Example: WordPress Product Creation

```
1. User Request (Claude Desktop)
   ↓
2. MCP Protocol
   ↓
3. devskyy-main Server
   ↓
4. wordpress_agent Tool
   ↓
5. DevSkyy FastAPI Server
   ↓
6. WordPress REST API
   ↓
7. WooCommerce Product Created
   ↓
8. Response → MCP → Claude → User
```

### Example: Code Generation with Vision

```
1. User: "Analyze this design and generate code"
   ↓
2. MCP Protocol
   ↓
3. devskyy-openai Server
   ↓
4. GPT-4o Vision Analysis
   ↓
5. Code Generation Tool
   ↓
6. filesystem Server (write code)
   ↓
7. git Server (commit changes)
   ↓
8. Response → MCP → Claude → User
```

## MCP Server Details

### DevSkyy Custom Servers

#### devskyy-openai
- **Technology**: FastMCP + OpenAI SDK
- **Models**: GPT-4o, GPT-4o-mini, o1-preview
- **Port**: stdio (MCP standard)
- **Tools**: 7 specialized tools
- **Use Cases**: Complex reasoning, vision, code generation

#### devskyy-main
- **Technology**: FastMCP + DevSkyy API
- **Agents**: 54 specialized agents
- **Port**: stdio (MCP standard)
- **Tools**: 20+ agent tools
- **Use Cases**: E-commerce automation, content creation

### Standard MCP Servers

#### filesystem
- **Provider**: @modelcontextprotocol/server-filesystem
- **Scope**: /Users/coreyfoster/DevSkyy
- **Operations**: read, write, search, list
- **Security**: Sandboxed to project directory

#### git
- **Provider**: @modelcontextprotocol/server-git
- **Repository**: /Users/coreyfoster/DevSkyy
- **Operations**: status, diff, log, commit, branch
- **Security**: Read-only by default

#### github
- **Provider**: @modelcontextprotocol/server-github
- **Authentication**: GitHub Personal Access Token
- **Operations**: issues, PRs, workflows, search
- **Rate Limits**: GitHub API limits apply

#### postgres
- **Provider**: @modelcontextprotocol/server-postgres
- **Connection**: postgresql://localhost/devskyy
- **Operations**: queries, schema inspection
- **Security**: Configurable read-only mode

#### sequential-thinking
- **Provider**: @modelcontextprotocol/server-sequential-thinking
- **Purpose**: Extended chain-of-thought reasoning
- **Use Cases**: Complex problem solving, planning

#### brave-search
- **Provider**: @modelcontextprotocol/server-brave-search
- **Authentication**: Brave API Key
- **Operations**: web search, news search
- **Rate Limits**: Brave API limits apply

#### fetch
- **Provider**: @modelcontextprotocol/server-fetch
- **Operations**: HTTP requests, web scraping
- **Security**: Configurable allowed domains

#### memory
- **Provider**: @modelcontextprotocol/server-memory
- **Storage**: Persistent across conversations
- **Use Cases**: Context retention, preferences

## Security Architecture

### Authentication Flow

```
┌──────────────┐
│ AI Assistant │
└──────┬───────┘
       │ 1. Request with env vars
       ↓
┌──────────────┐
│  MCP Server  │
└──────┬───────┘
       │ 2. Validate API keys
       ↓
┌──────────────┐
│ DevSkyy API  │
└──────┬───────┘
       │ 3. JWT authentication
       ↓
┌──────────────┐
│   Resource   │
└──────────────┘
```

### Security Layers

1. **Environment Variables**: API keys stored securely
2. **MCP Protocol**: Encrypted communication
3. **JWT Tokens**: API authentication
4. **RBAC**: Role-based access control
5. **Rate Limiting**: Prevent abuse
6. **Sandboxing**: Filesystem access restricted

## Performance Optimization

### Caching Strategy

```
┌─────────────┐
│ AI Request  │
└──────┬──────┘
       │
       ↓
┌─────────────┐     Cache Hit
│   Memory    │────────────────→ Fast Response
│   Server    │
└──────┬──────┘
       │ Cache Miss
       ↓
┌─────────────┐
│ MCP Server  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  DevSkyy    │
│  Platform   │
└─────────────┘
```

### Load Balancing

- **Concurrent Requests**: Up to 5 per server
- **Timeout**: 60 seconds default
- **Retry Logic**: 3 attempts with exponential backoff
- **Circuit Breaker**: Automatic failover

## Monitoring & Observability

### Metrics Collected

- Request count per server
- Response time (p50, p95, p99)
- Error rate
- Memory usage
- Active connections

### Logging

```
~/Library/Logs/Claude/
├── mcp-devskyy-openai.log
├── mcp-devskyy-main.log
├── mcp-filesystem.log
├── mcp-git.log
└── mcp-*.log
```

### Health Checks

- **Endpoint**: /health (where applicable)
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## Deployment Scenarios

### Development
- Local MCP servers
- Claude Desktop integration
- Hot reload enabled
- Debug logging

### Production
- Containerized MCP servers
- Load balancer
- Production logging
- Monitoring enabled

### CI/CD
- Automated testing
- MCP server validation
- Integration tests
- Performance benchmarks

---

**Version**: 1.0.0  
**Last Updated**: 2025-12-16  
**Maintained by**: The Skyy Rose Collection LLC

