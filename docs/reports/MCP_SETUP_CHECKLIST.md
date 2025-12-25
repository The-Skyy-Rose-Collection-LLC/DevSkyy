# DevSkyy MCP Setup Checklist

Use this checklist to track your MCP server configuration progress.

## ✅ Prerequisites

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Claude Desktop installed (optional but recommended)
- [ ] Git installed and configured

## 📦 Installation

- [ ] Run setup script: `./scripts/setup_mcp.sh`
- [ ] Install Python dependencies: `pip install -r mcp/requirements.txt`
- [ ] Verify MCP package: `python3 -c "import mcp; print('MCP OK')"`

## 🔑 API Keys Configuration

### Required Keys

- [ ] **OPENAI_API_KEY** - Get from https://platform.openai.com/api-keys
  - [ ] Key obtained
  - [ ] Added to `.env.mcp`
  - [ ] Added to `~/.zshrc` or `~/.bash_profile`
  - [ ] Verified: `echo $OPENAI_API_KEY`

- [ ] **DEVSKYY_API_KEY** - Your DevSkyy platform API key
  - [ ] Key obtained/generated
  - [ ] Added to `.env.mcp`
  - [ ] Added to shell profile
  - [ ] Verified: `echo $DEVSKYY_API_KEY`

### Optional Keys

- [ ] **GITHUB_TOKEN** - Get from https://github.com/settings/tokens
  - [ ] Token created with appropriate scopes (repo, workflow)
  - [ ] Added to `.env.mcp`
  - [ ] Added to shell profile
  - [ ] Verified: `echo $GITHUB_TOKEN`

- [ ] **BRAVE_API_KEY** - Get from https://brave.com/search/api/
  - [ ] Key obtained
  - [ ] Added to `.env.mcp`
  - [ ] Added to shell profile

- [ ] **ANTHROPIC_API_KEY** - Get from https://console.anthropic.com/
  - [ ] Key obtained
  - [ ] Added to `.env.mcp`
  - [ ] Added to shell profile

## 🔧 Claude Desktop Configuration

- [ ] Claude Desktop installed
- [ ] Backup existing config (if any):
  ```bash
  cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
     ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup
  ```
- [ ] Copy example config:
  ```bash
  cp config/claude/desktop.example.json \
     ~/Library/Application\ Support/Claude/claude_desktop_config.json
  ```
- [ ] Update paths in config to match your system
- [ ] Verify config is valid JSON:
  ```bash
  python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
  ```

## 🧪 Testing

- [ ] Run test script: `python3 scripts/test_mcp_servers.py`
- [ ] All tests pass (4/4)
- [ ] Test DevSkyy OpenAI server:
  ```bash
  timeout 5 python3 mcp/openai_server.py || echo "Server started OK"
  ```
- [ ] Test DevSkyy Main server:
  ```bash
  timeout 5 python3 devskyy_mcp.py || echo "Server started OK"
  ```

## 🚀 Activation

- [ ] Restart Claude Desktop (Quit and reopen)
- [ ] Verify MCP servers loaded in Claude Desktop
- [ ] Test a simple command in Claude:
  ```
  "List the files in the DevSkyy repository"
  ```
- [ ] Test DevSkyy agent:
  ```
  "What agents are available in the DevSkyy platform?"
  ```

## 📚 Documentation Review

- [ ] Read `docs/MCP_CONFIGURATION_GUIDE.md`
- [ ] Review `docs/MCP_QUICK_REFERENCE.md`
- [ ] Understand `docs/MCP_ARCHITECTURE.md`
- [ ] Check `mcp/README.md`

## 🔒 Security Verification

- [ ] API keys NOT committed to git
- [ ] `.env.mcp` added to `.gitignore`
- [ ] Environment variables set in shell profile only
- [ ] File permissions correct on sensitive files:
  ```bash
  chmod 600 .env.mcp
  ```
- [ ] GitHub token has minimal required scopes
- [ ] Database connection uses appropriate permissions

## 🎯 Functional Testing

### Test Each MCP Server

- [ ] **filesystem** - Ask Claude to read a file
- [ ] **git** - Ask Claude to show git status
- [ ] **github** - Ask Claude to list recent issues
- [ ] **postgres** - Ask Claude to describe database schema
- [ ] **devskyy-openai** - Ask Claude to generate code
- [ ] **devskyy-main** - Ask Claude about available agents
- [ ] **sequential-thinking** - Ask Claude to solve a complex problem
- [ ] **brave-search** - Ask Claude to search for information
- [ ] **fetch** - Ask Claude to fetch a webpage
- [ ] **memory** - Ask Claude to remember something for later

## 📊 Performance Verification

- [ ] MCP servers start within 5 seconds
- [ ] Response time < 2 seconds for simple queries
- [ ] No memory leaks (check with `ps aux | grep mcp`)
- [ ] Logs are being written: `ls -la ~/Library/Logs/Claude/`

## 🐛 Troubleshooting Completed

If you encountered issues, mark what you fixed:

- [ ] Fixed Python dependency issues
- [ ] Fixed environment variable issues
- [ ] Fixed Claude Desktop config issues
- [ ] Fixed permission issues
- [ ] Fixed API key issues
- [ ] Fixed network/connectivity issues

## ✨ Optional Enhancements

- [ ] Set up multi-environment configs (dev/prod)
- [ ] Configure custom MCP server
- [ ] Set up monitoring and alerting
- [ ] Create custom agent workflows
- [ ] Integrate with CI/CD pipeline

## 📝 Notes

Use this space to track any custom configurations or issues:

```
Date: _______________

Notes:
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
```

## ✅ Final Verification

- [ ] All 10 MCP servers configured
- [ ] All required API keys set
- [ ] Claude Desktop integration working
- [ ] Test script passes (4/4)
- [ ] Documentation reviewed
- [ ] Security verified
- [ ] Functional tests passed

---

**Setup Complete!** 🎉

You now have a fully configured MCP environment for DevSkyy!

**Next Steps:**
1. Start using Claude Desktop with MCP servers
2. Explore the 54-agent ecosystem
3. Automate your WordPress workflows
4. Build custom integrations

**Resources:**
- Quick Reference: `docs/MCP_QUICK_REFERENCE.md`
- Full Guide: `docs/MCP_CONFIGURATION_GUIDE.md`
- Support: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

