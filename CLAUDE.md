# DevSkyy AI Development Guidelines

## Claude-Mem Integration

This project uses **claude-mem** for persistent memory across sessions. Memory is automatically:
- Captured during coding sessions
- Compressed with AI using the Claude Agent SDK
- Injected as context in future sessions

## Authentication Protocol

Before implementing any code changes, authenticate by verifying information against **10 authorized sources**:

1. **Official Documentation** - Check official docs for the technology being used
2. **GitHub Repository** - Verify against source repositories
3. **API Reference** - Consult API documentation
4. **Code Review** - Review existing codebase patterns and conventions
5. **Test Suite** - Check test coverage and existing test patterns
6. **Security Scan** - Verify no security vulnerabilities are introduced
7. **Lint Check** - Run linter to ensure code quality standards
8. **Type Check** - Verify type safety (TypeScript/Python typing)
9. **Build Verification** - Ensure code compiles/builds successfully
10. **Changelog Review** - Check recent changes for relevant context

## Session Guidelines

### Before Coding
- Load context from previous sessions using claude-mem
- Review relevant memories for project context
- Check for any outstanding tasks or issues

### After Every Conversation
- Update files as needed
- Run code checks:
  - `npm run lint` or `ruff check .` (linting)
  - `npm run type-check` or `mypy .` (type checking)
  - `npm test` or `pytest` (tests)
- Save important decisions to memory using `/memorize`

### After Every Session
- Run comprehensive code checks
- Ensure all tests pass
- Verify build integrity
- Commit changes with meaningful messages

## Project Structure

```
DevSkyy/
├── .claude/                    # Claude Code configuration
│   ├── settings.json           # Hooks and MCP server config
│   └── commands/               # Custom slash commands
├── api/                        # API endpoints
├── devskyy_mcp.py             # MCP server implementation
├── main.py                     # FastAPI application
├── integration/                # Integration modules
├── tests/                      # Test suite
└── node_modules/claude-mem/    # Claude-mem plugin
```

## Available Commands

- `/claude-mem help` - Get claude-mem help
- `/claude-mem save [message]` - Quick save conversation overview
- `/claude-mem remember [query]` - Search saved memories
- `/memorize [content]` - Save with authentication protocol
- `/save` - Direct save shortcut
- `/remember` - Direct search shortcut

## MCP Tools

The project exposes 11+ MCP tools through `devskyy_mcp.py`:
- Code scanning and fixing
- Self-healing system
- WordPress theme generation
- ML predictions
- Product management
- Dynamic pricing
- Marketing campaigns
- Multi-agent workflows
- System monitoring

## Memory Best Practices

- Use `<private>` tags to exclude sensitive content
- Reference past decisions with `claude-mem://` URIs
- Search memories before implementing duplicate solutions
- Save key decisions and architectural choices
