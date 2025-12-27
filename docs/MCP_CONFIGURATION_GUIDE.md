# DevSkyy MCP Server Configuration Guide

## Overview

This guide explains how to configure Model Context Protocol (MCP) servers for the DevSkyy Enterprise Platform. MCP enables AI assistants like Claude to interact with your development environment, databases, APIs, and custom tools.

## Quick Start

### 1. Install Prerequisites

```bash
# Ensure Node.js and npm are installed
node --version  # Should be v18+
npm --version

# Install Python dependencies for DevSkyy MCP servers
cd /Users/coreyfoster/DevSkyy
pip install -r mcp/requirements.txt
```

### 2. Configure Claude Desktop

Copy the example configuration:

```bash
cp config/claude/desktop.example.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 3. Set Environment Variables

Create a `.env` file in your home directory or add to your shell profile:

```bash
# ~/.zshrc or ~/.bash_profile
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
export DEVSKYY_API_KEY="your-devskyy-api-key"
export GITHUB_TOKEN="ghp_your-github-token"
export BRAVE_API_KEY="your-brave-search-key"  # Optional
```

### 4. Restart Claude Desktop

After configuration, restart Claude Desktop to load the MCP servers.

## Configured MCP Servers

### DevSkyy Custom Servers

#### 1. **devskyy-openai** - OpenAI Integration

- **Purpose**: GPT-4o, GPT-4o-mini, o1-preview model access
- **Capabilities**:
  - Text completion and generation
  - Vision analysis (GPT-4o)
  - Code generation with DevSkyy best practices
  - Function calling and structured outputs
  - Model selection recommendations
  - Agent orchestration
- **Location**: `mcp/openai_server.py`
- **Use Cases**:
  - Complex reasoning tasks
  - Image analysis for product photos
  - Code generation for agents
  - Multi-step workflows

#### 2. **devskyy-main** - 54-Agent Ecosystem

- **Purpose**: Access to DevSkyy's specialized AI agents
- **Capabilities**:
  - WordPress/WooCommerce automation
  - SEO optimization
  - Content generation
  - Social media management
  - Analytics and reporting
  - Security scanning
  - Database operations
  - ML predictions
- **Location**: `devskyy_mcp.py`
- **Use Cases**:
  - E-commerce automation
  - Content creation workflows
  - Product management
  - Theme generation

### Standard MCP Servers

#### 3. **filesystem** - File Operations

- **Purpose**: Read, write, search files in DevSkyy repository
- **Capabilities**:
  - Read file contents
  - Write/edit files
  - Search files by pattern
  - List directory contents
  - Create/delete files and directories
- **Scope**: `/Users/coreyfoster/DevSkyy`
- **Use Cases**:
  - Code editing and refactoring
  - Configuration updates
  - Documentation generation
  - File organization

#### 4. **git** - Version Control

- **Purpose**: Git operations on DevSkyy repository
- **Capabilities**:
  - Check status and diff
  - View commit history
  - Create branches
  - Stage and commit changes
  - View file history
- **Repository**: `/Users/coreyfoster/DevSkyy`
- **Use Cases**:
  - Code review
  - Change tracking
  - Branch management
  - Commit history analysis

#### 5. **github** - GitHub API

- **Purpose**: Interact with GitHub repositories
- **Capabilities**:
  - Create/manage issues
  - Create/review pull requests
  - Manage workflows
  - Repository operations
  - Search code and commits
- **Authentication**: Requires `GITHUB_TOKEN`
- **Use Cases**:
  - Issue tracking
  - PR automation
  - CI/CD management
  - Code search

#### 6. **postgres** - Database Operations

- **Purpose**: PostgreSQL database access
- **Capabilities**:
  - Execute queries
  - Schema inspection
  - Data analysis
  - Database migrations
- **Connection**: `postgresql://localhost/devskyy`
- **Use Cases**:
  - Data queries
  - Schema updates
  - Performance analysis
  - Data migrations

#### 7. **sequential-thinking** - Complex Reasoning

- **Purpose**: Extended chain-of-thought for complex problems
- **Capabilities**:
  - Multi-step reasoning
  - Problem decomposition
  - Decision analysis

## Usage Examples

### Example 1: WordPress Product Creation with DevSkyy Agents

```
User: Create a new WooCommerce product for the "Heart aRose Bomber" jacket

Claude will use:
1. devskyy-main server → wordpress_agent tool
2. filesystem server → Read product templates
3. memory server → Remember product details for future updates
```

### Example 2: Code Review with Git Integration

```
User: Review the recent changes to the authentication system

Claude will use:
1. git server → View recent commits and diffs
2. filesystem server → Read modified files
3. sequential-thinking → Analyze security implications
4. github server → Check related issues/PRs
```

### Example 3: Database Schema Update

```
User: Add a new table for tracking customer preferences

Claude will use:
1. postgres server → Inspect current schema
2. filesystem server → Create migration file
3. git server → Commit the migration
4. sequential-thinking → Plan rollback strategy
```

### Example 4: AI-Powered Image Analysis

```
User: Analyze this product photo and suggest improvements

Claude will use:
1. devskyy-openai server → vision_analysis tool (GPT-4o)
2. devskyy-main server → seo_agent for alt text
3. memory server → Store analysis for future reference
```

## Configuration Best Practices

### Security

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate keys regularly** (every 90 days recommended)
4. **Limit GitHub token scope** to only required permissions
5. **Use read-only database connections** when possible

### Performance

1. **Enable only needed servers** - Comment out unused servers
2. **Set appropriate timeouts** - Default is 60 seconds
3. **Monitor resource usage** - MCP servers run as separate processes
4. **Use caching** - Memory server helps reduce redundant operations

### Troubleshooting

#### MCP Server Not Starting

```bash
# Check if Python dependencies are installed
cd /Users/coreyfoster/DevSkyy
pip install -r mcp/requirements.txt

# Test server manually
python mcp/openai_server.py
python devskyy_mcp.py
```

#### Environment Variables Not Loading

```bash
# Verify environment variables are set
echo $OPENAI_API_KEY
echo $DEVSKYY_API_KEY

# Reload shell configuration
source ~/.zshrc  # or ~/.bash_profile
```

#### Permission Errors

```bash
# Ensure scripts are executable
chmod +x mcp/openai_server.py
chmod +x devskyy_mcp.py

# Check file ownership
ls -la /Users/coreyfoster/DevSkyy/mcp/
```

## Advanced Configuration

### Custom MCP Server Development

Create your own MCP server for specialized DevSkyy operations:

```python
# custom_mcp_server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("custom_devskyy_server")

@mcp.tool()
async def custom_operation(
    param: str = Field(description="Operation parameter")
) -> str:
    """Custom DevSkyy operation"""
    # Your custom logic here
    return f"Processed: {param}"

if __name__ == "__main__":
    mcp.run()
```

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "custom-devskyy": {
      "command": "python",
      "args": ["/Users/coreyfoster/DevSkyy/custom_mcp_server.py"],
      "description": "Custom DevSkyy operations"
    }
  }
}
```

### Multi-Environment Setup

Create environment-specific configurations:

```bash
# Development
~/Library/Application Support/Claude/claude_desktop_config.dev.json

# Production
~/Library/Application Support/Claude/claude_desktop_config.prod.json

# Switch environments
ln -sf claude_desktop_config.dev.json claude_desktop_config.json
```

### Server Prioritization

Order servers by usage frequency for better performance:

```json
{
  "mcpServers": {
    "filesystem": { ... },      // Most used
    "git": { ... },             // Frequently used
    "devskyy-main": { ... },    // Project-specific
    "postgres": { ... },        // As needed
    "brave-search": { ... }     // Occasional
  }
}
```

## Integration with DevSkyy Workflows

### Agent Development Workflow

1. **Design**: Use sequential-thinking for architecture
2. **Code**: Use filesystem + devskyy-openai for code generation
3. **Test**: Use postgres for data validation
4. **Review**: Use git + github for code review
5. **Deploy**: Use devskyy-main agents for deployment

### E-Commerce Operations

1. **Product Research**: brave-search + fetch for market analysis
2. **Content Creation**: devskyy-main content_agent
3. **Image Processing**: devskyy-openai vision_analysis
4. **WordPress Upload**: devskyy-main wordpress_agent
5. **SEO Optimization**: devskyy-main seo_agent
6. **Analytics**: postgres + devskyy-main analytics_agent

### Security Auditing

1. **Code Scan**: filesystem + devskyy-main security_agent
2. **Dependency Check**: fetch + github for vulnerability databases
3. **Database Audit**: postgres for security checks
4. **Git History**: git for sensitive data leaks
5. **Report Generation**: filesystem for documentation

## Monitoring and Maintenance

### Health Checks

```bash
# Check MCP server status
ps aux | grep mcp

# View MCP logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Test individual servers
python -c "from mcp.server.fastmcp import FastMCP; print('MCP OK')"
```

### Performance Metrics

Monitor these metrics for optimal performance:

- **Response Time**: < 2 seconds for most operations
- **Memory Usage**: < 500MB per server
- **Error Rate**: < 1% of requests
- **Uptime**: > 99.9%

### Update Schedule

- **Weekly**: Check for MCP package updates
- **Monthly**: Review and rotate API keys
- **Quarterly**: Audit server usage and remove unused servers
- **Annually**: Major version upgrades and security review

## Resources

- **MCP Specification**: <https://modelcontextprotocol.io/specification/2025-06-18>
- **FastMCP Documentation**: <https://gofastmcp.com>
- **DevSkyy Documentation**: `/Users/coreyfoster/DevSkyy/docs/`
- **MCP Server Registry**: <https://github.com/modelcontextprotocol/servers>

## Support

For issues or questions:

1. Check logs: `~/Library/Logs/Claude/mcp*.log`
2. Review documentation: `docs/MCP_CONFIGURATION_GUIDE.md`
3. Test servers manually: `python mcp/openai_server.py`
4. GitHub Issues: <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues>

---

**Last Updated**: 2025-12-16
**Version**: 1.0.0
**Maintained by**: The Skyy Rose Collection LLC

- System design
- Strategic planning

#### 8. **brave-search** - Web Search

- **Purpose**: Real-time web search capabilities
- **Capabilities**:
  - Web search
  - News search
  - Technical documentation lookup
  - API reference search
- **Authentication**: Requires `BRAVE_API_KEY` (optional)
- **Use Cases**:
  - Research
  - Documentation lookup
  - Technology trends
  - Competitor analysis

#### 9. **fetch** - Web Content

- **Purpose**: Fetch and process web content
- **Capabilities**:
  - HTTP requests
  - API calls
  - Web scraping
  - Content extraction
- **Use Cases**:
  - API testing
  - Documentation fetching
  - Data collection
  - Integration testing

#### 10. **memory** - Persistent Context

- **Purpose**: Maintain context across conversations
- **Capabilities**:
  - Store conversation context
  - Retrieve past interactions
  - Maintain project state
  - Remember preferences
- **Use Cases**:
  - Long-term projects
  - Context retention
  - Preference learning
  - Workflow continuity
