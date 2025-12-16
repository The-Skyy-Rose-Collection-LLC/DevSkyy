# DevSkyy Documentation

Comprehensive documentation for the DevSkyy Enterprise Platform - AI-driven multi-agent orchestration platform for enterprise e-commerce automation.

## 📚 Documentation Structure

### 🤖 [Agents](./agents/)
Documentation for all AI agents in the DevSkyy ecosystem
- **[AGENTS.md](./agents/AGENTS.md)** - Complete agent overview and specifications

### 🏗️ [Architecture](./architecture/)
System architecture and design documentation
- **[DEVSKYY_MASTER_PLAN.md](./architecture/DEVSKYY_MASTER_PLAN.md)** - Master architectural plan

### 🚀 [Deployment](./deployment/)
Deployment guides and production setup
- **[DEPLOYMENT_GUIDE.md](./deployment/DEPLOYMENT_GUIDE.md)** - Main deployment guide
- **[PUSH_INSTRUCTIONS.md](./deployment/PUSH_INSTRUCTIONS.md)** - Git workflow instructions
- **[Production_Grade_WordPress_Elementor_Automation_Guide.md](./deployment/Production_Grade_WordPress_Elementor_Automation_Guide.md)** - WordPress automation setup

### 📖 [Guides](./guides/)
Developer guides and tutorials
- **[QUICKSTART.md](./guides/QUICKSTART.md)** - 5-minute setup guide
- **[DEVELOPER_QUICKREF.md](./guides/DEVELOPER_QUICKREF.md)** - Daily workflow commands
- **[SERVER_README.md](./guides/SERVER_README.md)** - MCP server documentation
- **[ADVANCED_TOOL_USE_DEVSKYY.md](./guides/ADVANCED_TOOL_USE_DEVSKYY.md)** - Advanced tool usage
- **[CLAUDE.md](./guides/CLAUDE.md)** - Claude integration guide
- **[DevSky_Enterprise_Platform_Development_Guide.md](./guides/DevSky_Enterprise_Platform_Development_Guide.md)** - Platform development guide
- **[Enterprise_FastAPI_Platform_Implementation_Guide.md](./guides/Enterprise_FastAPI_Platform_Implementation_Guide.md)** - FastAPI implementation guide

### 📊 [Reports](./reports/)
Analysis and gap reports
- **[GAP_ANALYSIS.md](./reports/GAP_ANALYSIS.md)** - Feature gap analysis

### 🔒 [Security](./security/)
Security documentation and compliance
- **[CLEAN_CODING_AGENTS.md](./security/CLEAN_CODING_AGENTS.md)** - Clean coding compliance system

### 🧪 [Testing](./testing/)
Testing documentation and procedures
- Test specifications and procedures (coming soon)

## 🚀 Quick Start

1. **New to DevSkyy?** Start with [QUICKSTART.md](./guides/QUICKSTART.md)
2. **Daily Development?** Use [DEVELOPER_QUICKREF.md](./guides/DEVELOPER_QUICKREF.md)
3. **Deploying?** Follow [DEPLOYMENT_GUIDE.md](./deployment/DEPLOYMENT_GUIDE.md)
4. **Understanding Agents?** Read [AGENTS.md](./agents/AGENTS.md)

## 🔧 Development Workflow

```bash
# Setup (one-time)
./setup_compliance.sh

# Daily workflow
git add .
git commit -m "feat: new feature"  # Pre-commit runs automatically
git push                           # CI/CD validates

# Manual quality checks
pre-commit run --all-files
pytest --cov
```

## 📋 Key Features

- **54 AI Agents** - Specialized agents for different business functions
- **WordPress Integration** - Full WooCommerce automation
- **3D Asset Generation** - Tripo AI integration for product visualization
- **Security First** - AES-256-GCM encryption, JWT OAuth2
- **Clean Code** - Automated quality enforcement with 20+ checks
- **MCP Integration** - Model Context Protocol for AI assistants
- **Enterprise Ready** - GDPR compliance, audit trails, monitoring

## 🏢 Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   TypeScript    │    │   FastAPI        │    │   6 Core        │
│   SDK           │───►│   Backend        │───►│   AI Agents     │
│   (Frontend)    │    │   (API Layer)    │    │   Ecosystem     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WordPress     │    │   PostgreSQL     │    │   External      │
│   Management    │    │   Database       │    │   APIs          │
│   (Automation)  │    │   (Data Layer)   │    │   (Integrations)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🤝 Contributing

1. Read the [DEVELOPER_QUICKREF.md](./guides/DEVELOPER_QUICKREF.md)
2. Follow the clean coding standards in [CLEAN_CODING_AGENTS.md](./security/CLEAN_CODING_AGENTS.md)
3. All commits must pass pre-commit hooks
4. Maintain >80% test coverage
5. Update documentation for new features

## 📞 Support

- **Documentation Issues**: Create an issue with the `documentation` label
- **Feature Requests**: Use the feature request template
- **Bug Reports**: Include reproduction steps and environment details

---

**Last Updated**: December 2025
**Version**: 3.0.0
**License**: MIT
