# DevSkyy MCP Quick Reference

## 🚀 Quick Start

```bash
# 1. Run setup script
./scripts/setup_mcp.sh

# 2. Configure API keys
nano .env.mcp

# 3. Add to shell profile
cat .env.mcp >> ~/.zshrc
source ~/.zshrc

# 4. Restart Claude Desktop
```

## 📋 Configured MCP Servers

| Server | Purpose | Key Features |
|--------|---------|--------------|
| **devskyy-openai** | OpenAI models | GPT-4o, vision, code gen, function calling |
| **devskyy-main** | 54-agent ecosystem | WordPress, SEO, content, analytics, ML |
| **filesystem** | File operations | Read, write, search files |
| **git** | Version control | Status, diff, commit, branch |
| **github** | GitHub API | Issues, PRs, workflows |
| **postgres** | Database | Queries, schema, migrations |
| **sequential-thinking** | Complex reasoning | Multi-step analysis, planning |
| **brave-search** | Web search | Research, documentation lookup |
| **fetch** | Web content | HTTP requests, API calls |
| **memory** | Persistent context | Cross-conversation memory |

## 🔑 Required Environment Variables

```bash
# Essential
export OPENAI_API_KEY="sk-..."           # For devskyy-openai
export DEVSKYY_API_KEY="..."             # For devskyy-main

# Optional
export ANTHROPIC_API_KEY="sk-ant-..."    # For Claude API
export GITHUB_TOKEN="ghp_..."            # For github server
export BRAVE_API_KEY="..."               # For brave-search
```

## 💡 Common Use Cases

### WordPress Product Creation
```
Ask Claude: "Create a WooCommerce product for the Heart aRose Bomber"

Uses:
- devskyy-main → wordpress_agent
- filesystem → Read templates
- memory → Store product details
```

### Code Review
```
Ask Claude: "Review recent authentication changes"

Uses:
- git → View commits and diffs
- filesystem → Read files
- sequential-thinking → Analyze security
- github → Check related PRs
```

### Database Schema Update
```
Ask Claude: "Add customer preferences table"

Uses:
- postgres → Inspect schema
- filesystem → Create migration
- git → Commit changes
```

### Image Analysis
```
Ask Claude: "Analyze this product photo"

Uses:
- devskyy-openai → vision_analysis (GPT-4o)
- devskyy-main → seo_agent for alt text
```

## 🛠️ DevSkyy Agent Tools

### Available via `devskyy-main` server:

| Agent Type | Capabilities |
|------------|--------------|
| **wordpress_agent** | Theme gen, product upload, page creation |
| **seo_agent** | Keyword research, meta tags, optimization |
| **content_agent** | Blog posts, product descriptions, copy |
| **social_media_agent** | Post scheduling, content creation |
| **analytics_agent** | Reports, insights, predictions |
| **security_agent** | Vulnerability scanning, audits |
| **database_agent** | Queries, migrations, backups |
| **ml_agent** | Predictions, recommendations, analysis |

## 🔧 Troubleshooting

### Server Not Starting
```bash
# Check dependencies
pip install -r mcp/requirements.txt

# Test manually
python mcp/openai_server.py
```

### Environment Variables Not Set
```bash
# Verify
echo $OPENAI_API_KEY

# Reload shell
source ~/.zshrc
```

### Claude Desktop Not Detecting Servers
```bash
# Check config location
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# View logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

## 📊 Performance Tips

1. **Enable only needed servers** - Comment out unused ones
2. **Use caching** - Memory server reduces redundant operations
3. **Monitor resources** - Each server runs as separate process
4. **Set timeouts** - Default 60s, adjust as needed

## 🔒 Security Best Practices

1. ✅ Never commit API keys to git
2. ✅ Use environment variables for secrets
3. ✅ Rotate keys every 90 days
4. ✅ Limit GitHub token scope
5. ✅ Use read-only DB connections when possible

## 📚 Documentation

- **Full Guide**: `docs/MCP_CONFIGURATION_GUIDE.md`
- **MCP Directory**: `mcp/README.md`
- **Setup Script**: `scripts/setup_mcp.sh`
- **Example Config**: `config/claude/desktop.example.json`

## 🆘 Support

1. Check logs: `~/Library/Logs/Claude/mcp*.log`
2. Test servers: `python mcp/openai_server.py`
3. Review docs: `docs/MCP_CONFIGURATION_GUIDE.md`
4. GitHub Issues: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

**Quick Links**:
- MCP Spec: https://modelcontextprotocol.io/specification/2025-06-18
- FastMCP: https://gofastmcp.com
- MCP Servers: https://github.com/modelcontextprotocol/servers

**Version**: 1.0.0 | **Updated**: 2025-12-16

