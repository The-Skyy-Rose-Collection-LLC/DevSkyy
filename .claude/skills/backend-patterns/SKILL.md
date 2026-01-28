---
name: backend-patterns
description: Backend architecture patterns for Node.js, Express, and Next.js API routes.
---

# Backend Development Patterns

## Core Patterns
- **Repository Pattern**: Abstract data access behind interfaces
- **Service Layer**: Business logic separate from data access
- **Middleware**: Request/response processing pipeline
- **Cache-Aside**: Redis caching with fallback to database

## API Design
```
GET    /api/resources          # List
POST   /api/resources          # Create
GET    /api/resources/:id      # Read
PATCH  /api/resources/:id      # Update
DELETE /api/resources/:id      # Delete
```

## Database Best Practices
- Select only needed columns
- Use batch fetching (avoid N+1)
- Use transactions for multi-step ops

## Error Handling
- Custom `ApiError` class with statusCode
- Centralized error handler middleware
- Retry with exponential backoff

## Related Tools
- **Agents**: Use `architect` for design decisions
- **MCP**: `devskyy_mcp.py` for orchestration
- **Skills**: See `security-review` for auth patterns

Run `pytest tests/` after backend changes.
