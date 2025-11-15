# DevSkyy Documentation

**Welcome to the DevSkyy Enterprise Platform documentation.**

This documentation hub provides comprehensive guides, references, and resources for developers, administrators, and users of the DevSkyy AI platform.

---

## 🚀 Quick Links

- **[Main README](../README.md)** - Project overview and quick start
- **[CHANGELOG](../CHANGELOG.md)** - Version history and release notes
- **[SECURITY](../SECURITY.md)** - Security policy and reporting
- **[CONTRIBUTING](../CONTRIBUTING.md)** - Development guidelines
- **[LICENSE](../LICENSE)** - Project license

---

## 📖 Documentation Index

### Getting Started

| Guide | Description | Time Required |
|-------|-------------|---------------|
| [Quick Start](setup/quickstart.md) | Get up and running in 5 minutes | 5 min |
| [Environment Setup](setup/environment.md) | Configure your development environment | 15 min |
| [Database Setup](setup/database.md) | PostgreSQL and SQLite configuration | 10 min |

### Architecture & Design

| Document | Description | Audience |
|----------|-------------|----------|
| [Architecture Overview](ARCHITECTURE.md) | System design, diagrams, and data flow | Architects, Developers |
| [Agent System](../AGENTS.md) | Multi-agent architecture (57 agents) | Developers, AI Engineers |
| [API Design](API.md) | RESTful API structure and conventions | API Developers |
| [Database Schema](database/schema.md) | Data models and relationships | Backend Developers |

### Development

| Guide | Description | Level |
|-------|-------------|-------|
| [Code Quality Standards](development/code-quality.md) | Coding standards and best practices | All Developers |
| [Docstring Guide](development/docstrings.md) | Documentation standards (Google style) | All Developers |
| [Testing Guide](development/testing.md) | Unit, integration, and security testing | All Developers |
| [CI/CD Pipeline](development/cicd.md) | GitHub Actions workflows | DevOps |

### Deployment

| Document | Description | Environment |
|----------|-------------|-------------|
| [Deployment Guide](deployment/guide.md) | Production deployment procedures | Production |
| [Deployment Runbook](deployment/runbook.md) | Step-by-step deployment checklist | Production |
| [Security Guide](deployment/security.md) | Production security hardening | Production |
| [Docker Deployment](deployment/docker.md) | Container deployment | All |
| [Kubernetes Deployment](deployment/kubernetes.md) | K8s orchestration | Production |

### API Documentation

| Resource | Description | Format |
|----------|-------------|--------|
| [Swagger UI](http://localhost:8000/docs) | Interactive API documentation | HTML |
| [ReDoc](http://localhost:8000/redoc) | Alternative API documentation | HTML |
| [OpenAPI Spec](../artifacts/openapi.json) | Machine-readable API spec | JSON |
| [API Authentication](API_AUTHENTICATION_DOCUMENTATION.md) | Auth flows and examples | Markdown |

### Integration Guides

| Guide | Technology | Difficulty |
|-------|-----------|------------|
| [Auth0 Integration](guides/auth0-integration.md) | OAuth2/OIDC SSO | Medium |
| [MCP Configuration](guides/mcp-configuration.md) | Model Context Protocol | Advanced |
| [WordPress Integration](guides/wordpress-integration.md) | Theme builder API | Medium |
| [E-commerce Automation](ECOMMERCE_AUTOMATION.md) | Fashion automation | Advanced |

### Security & Compliance

| Document | Topic | Standard |
|----------|-------|----------|
| [Security Policy](../SECURITY.md) | Security practices and reporting | OWASP |
| [Authentication Security](AUTHENTICATION_SECURITY_GUIDE.md) | JWT, OAuth2, MFA | RFC 7519 |
| [GDPR Compliance](security/gdpr.md) | Data protection compliance | GDPR |
| [Security Audit](SECURITY_AUDIT_2025-11-10.md) | Latest security audit | SOC2 |

### Machine Learning

| Guide | Topic | Audience |
|-------|-------|----------|
| [ML Infrastructure](ml/infrastructure.md) | Model registry, caching, explainability | ML Engineers |
| [Hugging Face Best Practices](HUGGINGFACE_BEST_PRACTICES.md) | Transformer model usage | ML Engineers |
| [Model Training](ml/training.md) | Training and deployment pipeline | Data Scientists |
| [Model Explainability](ml/explainability.md) | SHAP-based interpretability | ML Engineers |

---

## 🔍 Search by Topic

### Authentication & Authorization
- [JWT Authentication](AUTHENTICATION_SECURITY_GUIDE.md#jwt-authentication)
- [RBAC (5-tier system)](../SECURITY.md#rbac)
- [OAuth2 Integration](guides/auth0-integration.md)
- [API Key Management](../SECURITY.md#api-key-management)

### Database & Data
- [PostgreSQL Setup](setup/database.md#postgresql)
- [SQLite Setup](setup/database.md#sqlite)
- [Database Migrations](development/migrations.md)
- [GDPR Data Export](../SECURITY.md#gdpr-compliance)

### Deployment & Operations
- [Docker Compose](deployment/docker.md#docker-compose)
- [Kubernetes Manifests](deployment/kubernetes.md)
- [Production Checklist](deployment/guide.md#checklist)
- [Health Monitoring](deployment/monitoring.md)

### Development Workflow
- [Pre-commit Hooks](../CONTRIBUTING.md#pre-commit-checks)
- [Testing Strategy](development/testing.md)
- [Code Review Process](../CONTRIBUTING.md#pull-request-process)
- [Release Process](development/releases.md)

---

## 🛠️ Tools & References

### Development Tools

```bash
# Code Quality
make lint          # Run linters (Ruff, Flake8, Black)
make format        # Auto-format code
make type-check    # MyPy type checking

# Testing
make test          # Run all tests
make test-coverage # Generate coverage report
make test-security # Security-specific tests

# Documentation
make docs          # Generate documentation
make docs-serve    # Serve docs locally
```

### API Tools

```bash
# Generate OpenAPI spec
python -c "from main import app; from agent.utils import export_openapi; export_openapi(app)"

# Generate SBOM
cyclonedx-py -i requirements.txt -o artifacts/sbom.json

# Validate API
openapi-spec-validator artifacts/openapi.json
```

### Useful Commands

```bash
# Database
alembic upgrade head              # Apply migrations
alembic revision --autogenerate   # Create migration

# Docker
docker-compose up -d              # Start services
docker-compose logs -f api        # View logs

# Kubernetes
kubectl apply -f k8s/             # Deploy to K8s
kubectl get pods                  # Check pods
```

---

## 📊 Metrics & Monitoring

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| P95 Latency | < 200ms | ~175ms | ✅ |
| Uptime | 99.9% | 99.95% | ✅ |
| Test Coverage | ≥ 90% | 92% | ✅ |
| Error Rate | < 0.5% | 0.2% | ✅ |
| Security Vulns | 0 | 0 | ✅ |

### Monitoring Resources

- **Prometheus:** [http://localhost:9090](http://localhost:9090)
- **Grafana:** [http://localhost:3000](http://localhost:3000)
- **Health Check:** [http://localhost:8000/api/v1/monitoring/health](http://localhost:8000/api/v1/monitoring/health)

---

## 🆘 Support & Resources

### Getting Help

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| [GitHub Issues](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues) | Bug reports, feature requests | 24-48 hours |
| [GitHub Discussions](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/discussions) | General questions | 1-3 days |
| support@skyyrose.com | Technical support | 1 business day |
| security@skyyrose.com | Security issues | 48 hours |

### Community Resources

- **Blog:** https://devskyy.com/blog
- **Status Page:** https://status.devskyy.com
- **API Status:** https://api.devskyy.com/health
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)

### Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
- [Anthropic API Reference](https://docs.anthropic.com/)

---

## 🔐 Security

### Reporting Security Issues

**DO NOT** create public GitHub issues for security vulnerabilities.

Email security findings to: **security@skyyrose.com**

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

**Response Timeline:**
- Initial response: 48 hours
- Status update: 5 business days
- Fix timeline: 7 days (critical), 14 days (high)

See [SECURITY.md](../SECURITY.md) for full policy.

---

## 📝 Contributing to Documentation

We welcome documentation improvements!

### How to Contribute

1. **Fork the repository**
2. **Make changes** to documentation files
3. **Test locally** (ensure links work)
4. **Submit a pull request**

### Documentation Standards

- Use **Markdown** format
- Follow **Google-style** for docstrings
- Include **code examples** where helpful
- Add **diagrams** for complex concepts (use Mermaid)
- Keep **language clear** and concise

### Documentation Checklist

- [ ] Spell check completed
- [ ] Links validated
- [ ] Code examples tested
- [ ] Screenshots current (if applicable)
- [ ] Diagrams use Mermaid format
- [ ] Updates reflected in this index

---

## 📂 Documentation Structure

```
docs/
├── README.md                     ← You are here
├── ARCHITECTURE.md               ← System architecture
├── API.md                        ← API documentation
│
├── setup/                        ← Getting started
│   ├── quickstart.md
│   ├── environment.md
│   └── database.md
│
├── deployment/                   ← Deployment guides
│   ├── guide.md
│   ├── runbook.md
│   ├── security.md
│   ├── docker.md
│   └── kubernetes.md
│
├── development/                  ← Development guides
│   ├── code-quality.md
│   ├── docstrings.md
│   ├── testing.md
│   ├── cicd.md
│   └── releases.md
│
├── guides/                       ← Integration guides
│   ├── auth0-integration.md
│   ├── mcp-configuration.md
│   └── wordpress-integration.md
│
├── security/                     ← Security documentation
│   ├── gdpr.md
│   └── compliance.md
│
└── ml/                          ← Machine learning
    ├── infrastructure.md
    ├── training.md
    └── explainability.md
```

---

## 🏆 Best Practices

### For Developers

✅ **DO:**
- Follow code quality standards
- Write comprehensive tests (≥90% coverage)
- Document all public functions
- Use type hints
- Follow Git commit conventions

❌ **DON'T:**
- Commit secrets or API keys
- Skip pre-commit hooks
- Merge without tests passing
- Deploy without validation

### For Operators

✅ **DO:**
- Monitor system health continuously
- Apply security patches promptly
- Back up data regularly
- Test disaster recovery
- Document incidents

❌ **DON'T:**
- Disable security features
- Skip health checks
- Deploy without validation
- Ignore alerts

---

## 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-15 | Initial documentation hub |

---

## 📄 License

This documentation is part of the DevSkyy project.

**License:** Proprietary - All Rights Reserved
© 2024 The Skyy Rose Collection LLC

---

**Last Updated:** 2025-11-15
**Documentation Version:** 1.0.0
**Maintained By:** DevSkyy Documentation Team

For questions or feedback about this documentation, please open an issue or contact support@skyyrose.com.
