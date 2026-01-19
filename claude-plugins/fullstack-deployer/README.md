# Fullstack Deployer

An autonomous full-stack deployment plugin for Claude Code that handles Vercel, Next.js, WordPress, and WooCommerce deployments with self-learning capabilities.

## Features

- **Autonomous Deployment**: Deploy to Vercel with automatic error handling and recovery
- **Self-Learning**: Uses Context7 MCP to fetch official documentation when encountering errors
- **Full Stack Support**: Handles Next.js frontend, WordPress headless CMS, and WooCommerce e-commerce
- **Comprehensive Testing**: Pre and post-deployment validation, E2E tests, health checks
- **Code Quality**: Integrated linting, type checking, and auto-fixing
- **Environment Management**: Manage environment variables across all platforms

## Installation

```bash
# Add to Claude Code plugins
claude --plugin-dir /path/to/fullstack-deployer
```

## Commands

| Command | Description |
|---------|-------------|
| `/deploy` | Deploy to Vercel with validation |
| `/rollback` | Rollback to previous deployment |
| `/env-manage` | Manage environment variables |
| `/wp-sync` | Sync WordPress/WooCommerce data |
| `/deploy-status` | Check deployment and service health |
| `/validate` | Run full validation suite |
| `/lint` | Run code quality checks |

## Agents

The plugin includes 7 autonomous agents that work together:

| Agent | Purpose |
|-------|---------|
| `deployment-orchestrator` | Coordinates full deployment workflow |
| `error-resolver` | Diagnoses and fixes errors using documentation |
| `env-manager` | Manages environment variables |
| `wordpress-sync` | Syncs headless CMS data |
| `rollback-agent` | Handles deployment rollbacks |
| `test-validator` | Runs tests and validates deployments |
| `code-quality-checker` | Ensures code meets quality standards |

## Skills

Comprehensive knowledge base covering:

- **Vercel Deployment** - CLI commands, configuration, common errors
- **Next.js Patterns** - App Router, Server Components, data fetching
- **WordPress Headless** - REST API, ACF, custom post types
- **WooCommerce API** - Products, cart, checkout, webhooks
- **Dashboard Config** - Environment management, multi-environment setup
- **Testing & Validation** - Jest, Playwright, health checks
- **Code Quality** - ESLint, Prettier, TypeScript

## Prerequisites

- Node.js 18+
- Vercel CLI (`npm i -g vercel`)
- Authenticated with Vercel (`vercel login`)
- WordPress site with REST API enabled
- WooCommerce with API credentials (for e-commerce features)

## Environment Variables

Create a `.env.local` file or configure in Vercel:

```bash
# Required
NEXT_PUBLIC_APP_URL=https://your-site.com
WORDPRESS_API_URL=https://your-wordpress-site.com

# For WooCommerce
WOOCOMMERCE_API_URL=https://your-wordpress-site.com
WC_CONSUMER_KEY=ck_your_key
WC_CONSUMER_SECRET=cs_your_secret

# Optional
NEXT_PUBLIC_ENABLE_WOOCOMMERCE=true
NEXT_PUBLIC_ENABLE_BLOG=true
```

## Usage Examples

### Deploy to Production
```
/deploy --prod
```

### Check Deployment Status
```
/deploy-status --verbose
```

### Sync WordPress Content
```
/wp-sync check
```

### Run Full Validation
```
/validate --full
```

### Fix Code Quality Issues
```
/lint --fix
```

## Autonomous Behavior

When you run a command like `/deploy`, the plugin will:

1. Run all pre-deployment checks
2. If checks fail, automatically diagnose and fix issues
3. Fetch documentation from Context7 when needed
4. Retry failed operations after applying fixes
5. Continue until deployment succeeds or definitively fails
6. Validate the deployment after completion

You don't need to intervene - the agents handle everything autonomously.

## Context7 Integration

The plugin uses Context7 MCP to fetch official documentation when errors occur:

- Vercel CLI documentation
- Next.js framework docs
- WordPress REST API docs
- WooCommerce API docs
- TypeScript handbook
- ESLint rule documentation

This enables the agents to find solutions to problems without user intervention.

## Hooks

The plugin includes hooks for:

- **Pre-deployment**: Validates code before production deploys
- **Post-deployment**: Verifies deployment health after deploy

## License

MIT
