---
name: security-review
description: Security checklist for auth, APIs, user input, and sensitive data.
---

# Security Review

## Critical Checks

**Secrets** - Never hardcode, use env vars:
```typescript
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) throw new Error('API key not configured')
```

**Input Validation** - Always validate with schemas:
```typescript
const schema = z.object({ email: z.string().email() })
const validated = schema.parse(input)
```

**SQL Injection** - Parameterized queries only:
```typescript
await db.query('SELECT * FROM users WHERE id = $1', [userId])
```

**XSS** - Sanitize user HTML:
```typescript
const clean = DOMPurify.sanitize(userHtml)
```

**Auth** - httpOnly cookies, not localStorage:
```typescript
res.setHeader('Set-Cookie', `token=${token}; HttpOnly; Secure; SameSite=Strict`)
```

## Pre-Deploy Checklist

- [ ] No hardcoded secrets
- [ ] All inputs validated
- [ ] Queries parameterized
- [ ] Rate limiting enabled
- [ ] Error messages generic
- [ ] Dependencies audited (`npm audit`)

## Related Tools
- **Agent**: `security-reviewer` | **Command**: `/verify` | **MCP**: `security_scan`
