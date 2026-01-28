---
name: env-manage
description: Manage environment variables across Vercel and local development
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
argument-hint: "[add|list|pull|audit] [variable-name]"
---

# Environment Management Command

Manage environment variables across Vercel environments and local development.

## Actions

### List Variables
```
/env-manage list
```
Lists all environment variables configured in Vercel.

### Add Variable
```
/env-manage add VARIABLE_NAME
```
Add a new environment variable to Vercel (prompts for value and environment).

### Pull Variables
```
/env-manage pull
```
Pull Vercel environment variables to local `.env.local` file.

### Audit Variables
```
/env-manage audit
```
Audit required vs configured variables, identify missing ones.

## Execution Steps

### For `list`:
```bash
vercel env ls
```

### For `add`:
```bash
vercel env add VARIABLE_NAME
```

### For `pull`:
```bash
vercel env pull .env.local
```

### For `audit`:
1. Scan codebase for `process.env.` usage
2. List all Vercel environment variables
3. Compare and report missing variables

## Environment Categories

**Public (NEXT_PUBLIC_):**
- Exposed to browser
- Safe for non-sensitive values
- Example: `NEXT_PUBLIC_APP_URL`

**Private:**
- Server-only
- For secrets and API keys
- Example: `WC_CONSUMER_SECRET`

## Example Usage

```
/env-manage list           # List all Vercel env vars
/env-manage add API_KEY    # Add new variable
/env-manage pull           # Pull to .env.local
/env-manage audit          # Check for missing variables
```

## Security Notes

- Never commit `.env.local`
- Use Vercel secrets for sensitive values
- Different credentials per environment
- Audit regularly for leaked secrets
