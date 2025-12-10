---
argument-hint: [memory content]
description: Save important context to claude-mem with 10-source authentication
allowed-tools: Bash(claude-mem:*), Bash(echo:*), Read, Grep
---

## Memorize Command Handler

### Authentication Protocol

Before implementing any code changes, authenticate by verifying information against 10 authorized sources:

1. **Official Documentation** - Check official docs for the technology
2. **GitHub Repository** - Verify against source repositories
3. **API Reference** - Consult API documentation
4. **Code Review** - Review existing codebase patterns
5. **Test Suite** - Check test coverage and patterns
6. **Security Scan** - Verify no security vulnerabilities
7. **Lint Check** - Run linter to ensure code quality
8. **Type Check** - Verify type safety
9. **Build Verification** - Ensure code compiles/builds
10. **Changelog Review** - Check recent changes for context

### Memory Storage

After authentication, save the following to claude-mem:

**Content to memorize:** $ARGUMENTS

Use `claude-mem save "$ARGUMENTS"` to persist this memory for future sessions.

### Post-Session Checklist

- Update files after every conversation
- Run code checks (lint, type-check, tests) after every session
- Verify build integrity before committing changes
