# DevSkyy Claude Code Plugin

Official Claude Code plugin for DevSkyy AI platform development.

## Overview

This plugin provides specialized skills, hooks, and automation for developing with the DevSkyy AI platform,
including SuperAgents, MCP servers, 3D pipelines, SkyyRose brand integration, and WordPress/Elementor workflows.

## Features

### 6 Specialized Skills

1. **DevSkyy Agent Development** (`devskyy-agent-development`)
   - SuperAgent architecture and patterns
   - LLM Round Table integration
   - Tool Registry usage
   - Agent coordination workflows

2. **DevSkyy MCP Server** (`devskyy-mcp-server`)
   - FastMCP tool development
   - Tool schema definitions
   - Resource exposure patterns
   - Multi-server orchestration

3. **3D Pipeline Workflow** (`3d-pipeline-workflow`)
   - Tripo3D integration
   - Text-to-3D and Image-to-3D generation
   - Asset optimization and validation
   - WordPress/WooCommerce 3D integration

4. **SkyyRose Brand Integration** (`skyyrose-brand-integration`)
   - Brand DNA and collection aesthetics
   - Brand-consistent content generation
   - Collection-specific presets (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
   - Visual generation guidelines

5. **WordPress Elementor Integration** (`wordpress-elementor-integration`)
   - Theme development and customization
   - Elementor page layouts
   - WooCommerce product management
   - Media uploads and deployment

6. **Research and Documentation** (`research-and-documentation`)
   - Context7 documentation queries
   - Structured note-taking
   - Source citation
   - Component research patterns

### Automated Hooks

- **PreToolUse**: Context7 prompts for code writing, brand consistency checks for visual generation
- **PostToolUse**: Test coverage reminders after code changes
- **Stop**: Completion verification checklist
- **SessionStart**: DevSkyy memory loading

## Installation

1. Copy the `devskyy` directory to Claude Code plugins location:

   ```bash
   cp -r claude-plugins/devskyy ~/.claude/plugins/
   ```

2. Restart Claude Code to load the plugin

3. Skills will be auto-discovered and available immediately

## Usage

### Skill Invocation

Skills are automatically invoked when you mention their trigger phrases:

- "create an agent" → devskyy-agent-development
- "generate 3D model" → 3d-pipeline-workflow
- "SkyyRose brand guidelines" → skyyrose-brand-integration
- "WordPress deployment" → wordpress-elementor-integration
- "research API documentation" → research-and-documentation

### Manual Skill Reference

You can explicitly reference a skill:

```text
Use the devskyy-agent-development skill to understand SuperAgent patterns
```

### Hook Behavior

Hooks run automatically:

- Before writing code: Context7 documentation check
- Before visual generation: Brand consistency validation
- After code changes: Test coverage reminder
- At session start: Memory loading prompt
- At session end: Completion verification

## Plugin Structure

```text
devskyy/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest
├── skills/                             # 6 specialized skills
│   ├── devskyy-agent-development/
│   │   ├── SKILL.md                   # Agent patterns
│   │   ├── references/                # Deep-dive docs
│   │   └── examples/                  # Code examples
│   ├── devskyy-mcp-server/
│   │   └── SKILL.md                   # MCP development
│   ├── 3d-pipeline-workflow/
│   │   └── SKILL.md                   # 3D generation
│   ├── skyyrose-brand-integration/
│   │   └── SKILL.md                   # Brand guidelines
│   ├── wordpress-elementor-integration/
│   │   └── SKILL.md                   # WordPress workflows
│   └── research-and-documentation/
│       └── SKILL.md                   # Documentation research
├── hooks/
│   └── hooks.json                     # Automated workflows
├── README.md                          # This file
└── LICENSE                            # MIT License
```

## Requirements

- Claude Code CLI (v0.1.0+)
- Context7 MCP plugin (for documentation queries)
- Serena MCP plugin (for memory management)
- DevSkyy repository access

## Configuration

### Required Environment Variables

For full functionality, set these in your environment:

```bash
# DevSkyy API
export DEVSKYY_API_KEY="sk-..."  # pragma: allowlist secret

# LLM Providers
export OPENAI_API_KEY="sk-..."  # pragma: allowlist secret
export ANTHROPIC_API_KEY="sk-ant-..."  # pragma: allowlist secret
export GOOGLE_AI_API_KEY="..."  # pragma: allowlist secret

# 3D Generation
export TRIPO_API_KEY="..."  # pragma: allowlist secret

# WordPress
export WORDPRESS_URL="https://skyyrose.com"
export WOOCOMMERCE_KEY="ck_..."  # pragma: allowlist secret
export WOOCOMMERCE_SECRET="cs_..."  # pragma: allowlist secret
```

## Examples

### Example 1: Create New SuperAgent

```text
Create a new DiscoveryAgent that helps users explore product collections
```

The `devskyy-agent-development` skill will provide:

- SuperAgent base class pattern
- Tool Registry integration
- LLM Round Table setup
- Testing patterns

### Example 2: Generate 3D Product Model

```text
Generate a 3D model of a SkyyRose hoodie in BLACK_ROSE style
```

The `3d-pipeline-workflow` skill provides:

- Tripo3D API usage
- Collection-specific presets
- Asset validation
- WordPress upload workflow

### Example 3: Research API Documentation

```text
Research the latest FastMCP patterns for creating MCP tools
```

The `research-and-documentation` skill will:

- Query Context7 for FastMCP docs
- Structure findings
- Cite sources
- Save to Serena memory

## Development

### Adding New Skills

1. Create skill directory: `skills/your-skill-name/`
2. Add `SKILL.md` with YAML frontmatter
3. Optional: Add `references/`, `examples/`, `scripts/`
4. Skills are auto-discovered on restart

### Modifying Hooks

Edit `hooks/hooks.json` to add/modify automated workflows.

Hook types:

- `prompt`: Inject prompt into Claude's context
- `command`: Execute shell command

### Testing

Test plugin installation:

```bash
claude-code --list-plugins
claude-code --list-skills
```

Test skill invocation:

```bash
claude-code "Create a new SuperAgent"
```

## Troubleshooting

### Skills Not Loading

1. Check plugin directory location: `~/.claude/plugins/devskyy/`
2. Verify `plugin.json` exists and is valid JSON
3. Restart Claude Code
4. Check logs: `~/.claude/logs/`

### Hooks Not Firing

1. Verify `hooks/hooks.json` syntax
2. Check matcher patterns (regex)
3. Test with `claude-code --debug`

### Context7 Not Working

1. Ensure Context7 MCP plugin is installed
2. Check MCP server configuration
3. Verify internet connectivity

## Contributing

This plugin is maintained by the DevSkyy team. For issues or contributions:

1. Fork the DevSkyy repository
2. Create a feature branch
3. Make changes in `claude-plugins/devskyy/`
4. Submit pull request

## License

MIT License - See LICENSE file

## Support

- **Documentation**: `docs/` directory in DevSkyy repo
- **Issues**: GitHub Issues
- **Email**: <support@skyyrose.com>

## Version History

- **1.0.0** (2026-01-07): Initial release
  - 6 specialized skills
  - Automated hooks
  - Context7 integration
  - Serena memory integration

## Acknowledgments

- Built with [Claude Code](https://claude.com/claude-code)
- Uses [Context7](https://context7.com) for documentation queries
- Powered by [DevSkyy AI Platform](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy)
