<claude-mem-context>

</claude-mem-context>

# agents/wordpress_theme_builder/ — WordPress theme builder (Claude Agent SDK, TypeScript)

Claude Agent SDK TypeScript agent that builds, evaluates, and deploys the SkyyRose WordPress theme. Exposes a `theme-build` MCP tool backed by `scripts/theme-build.sh`. Distinct from `agents/elite_web_builder/` (Python Director system) — this is the SDK integration layer for interactive CLI use.

## Key files

- `agent.ts` — Single-file agent. Uses `query`, `tool`, `createSdkMcpServer` from `@anthropic-ai/claude-agent-sdk`. Defines the `theme-build` MCP tool and registers 5 capabilities: `theme_build`, `theme_deploy`, `theme_evaluate`, `woocommerce_integration`, `theme_verification`. Entry point: `npx tsx agents/wordpress_theme_builder/agent.ts`.
- `scripts/theme-build.sh` — Shell script wrapped by the `theme-build` MCP tool. Runs lint, build, and asset pipeline for the WordPress theme.

## Conventions

- The `theme-build` MCP tool wraps `scripts/theme-build.sh` — all build logic stays in the shell script. The agent does NOT inline build commands.
- `theme_deploy` capability maps to `scripts/deploy-theme.sh` — **STOP AND SHOW required before dispatch**. The agent must print the exact deploy target and file count and wait for user confirmation.
- `theme_evaluate` scores against ThemeForest quality criteria — output is a structured JSON report, not prose.
- `woocommerce_integration` uses `api/v1/woocommerce/` REST endpoints — no direct DB access.
- Launch: `npx tsx agents/wordpress_theme_builder/agent.ts`. Requires Node.js 22 + `@anthropic-ai/claude-agent-sdk` installed.

## Don't

- Don't add a second entry point file — `agent.ts` is the single file. Keep capabilities in the same file as the tool registration.
- Don't call `scripts/deploy-theme.sh` without the STOP AND SHOW confirmation block — this is a production deploy.
- Don't mix this agent with the `elite_web_builder/` Python Director system. They are separate layers: this agent is for interactive CLI use; the Director is for autonomous PRD-driven story execution.

## Related

- `scripts/theme-build.sh` — shell script called by the `theme-build` MCP tool
- `scripts/deploy-theme.sh` — deploy script (requires explicit user confirmation before dispatch)
- `agents/elite_web_builder/` — Python Director system (separate; not imported by this agent)
- `wordpress-theme/skyyrose-flagship/` — theme source consumed by the build script
- `CLAUDE.md` → STOP AND SHOW section — the non-negotiable confirmation protocol for deploy actions
