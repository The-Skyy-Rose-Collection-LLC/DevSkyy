# DevSkyy Guides Documentation

Developer guides and tutorials for the DevSkyy Enterprise Platform.

## 📋 Available Guides

### Quick Start Guides
- **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute setup guide for new developers
- **[DEVELOPER_QUICKREF.md](./DEVELOPER_QUICKREF.md)** - Daily workflow commands and shortcuts

### Integration Guides
- **[SERVER_README.md](./SERVER_README.md)** - MCP server setup and integration
- **[CLAUDE.md](./CLAUDE.md)** - Claude AI integration and configuration

### Development Guides
- **[DevSky_Enterprise_Platform_Development_Guide.md](./DevSky_Enterprise_Platform_Development_Guide.md)** - Comprehensive platform development guide
- **[Enterprise_FastAPI_Platform_Implementation_Guide.md](./Enterprise_FastAPI_Platform_Implementation_Guide.md)** - FastAPI implementation best practices

### Advanced Guides
- **[ADVANCED_TOOL_USE_DEVSKYY.md](./ADVANCED_TOOL_USE_DEVSKYY.md)** - Advanced tool usage and customization

## 🚀 Getting Started

### For New Developers
1. Start with [QUICKSTART.md](./QUICKSTART.md) for initial setup
2. Review [DEVELOPER_QUICKREF.md](./DEVELOPER_QUICKREF.md) for daily commands
3. Follow [DevSky_Enterprise_Platform_Development_Guide.md](./DevSky_Enterprise_Platform_Development_Guide.md) for comprehensive understanding

### For Experienced Developers
1. Jump to [DEVELOPER_QUICKREF.md](./DEVELOPER_QUICKREF.md) for command reference
2. Check [ADVANCED_TOOL_USE_DEVSKYY.md](./ADVANCED_TOOL_USE_DEVSKYY.md) for advanced features
3. Review integration guides as needed

## 🔧 Development Workflow

### Daily Commands
```bash
# Setup (one-time)
./setup_compliance.sh

# Development workflow
git add .
git commit -m "feat: new feature"  # Pre-commit runs
git push                           # CI/CD validates

# Quality checks
pre-commit run --all-files
pytest --cov
ruff check . --fix
```

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run tests with verbose output
pytest -v
```

## 🤖 AI Integration

### MCP Server Setup
The Model Context Protocol (MCP) server enables AI assistant integration:

```bash
# Install MCP dependencies
pip install openai mcp pydantic

# Test server
python3 test_server.py

# Run server
python3 server.py
```

### Claude Integration
Configure Claude Desktop for DevSkyy integration:

1. Copy `claude_desktop_config.example.json` to Claude config directory
2. Set environment variables for API keys
3. Restart Claude Desktop
4. Use DevSkyy tools in Claude conversations

## 🏗️ Architecture Understanding

### Core Components
- **ADK (Agent Development Kit)** - Framework for building AI agents
- **Orchestration Engine** - Manages agent workflows
- **Security Layer** - Handles authentication and encryption
- **WordPress Integration** - E-commerce automation

### Key Patterns
- **Async/await** - Non-blocking operations
- **Type hints** - Better code reliability
- **Dependency injection** - Testable code
- **Event-driven** - Reactive architecture

## 📊 Best Practices

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain >80% test coverage
- Use meaningful variable names

### Security
- Never commit secrets to version control
- Validate all user inputs
- Use parameterized queries
- Implement proper error handling
- Follow principle of least privilege

### Performance
- Use async/await for I/O operations
- Implement proper caching strategies
- Optimize database queries
- Monitor resource usage
- Profile critical code paths

## 🔍 Troubleshooting

### Common Issues
1. **Import errors** - Check Python path and dependencies
2. **Database connection** - Verify connection string and credentials
3. **API rate limits** - Implement proper retry logic
4. **Memory issues** - Monitor resource usage and optimize

### Debug Commands
```bash
# Check Python environment
python --version
pip list

# Validate configuration
python -c "import main_enterprise; print('OK')"

# Test database connection
python -c "from database.db import test_connection; test_connection()"

# Check API endpoints
curl http://localhost:8000/health
```

## 📚 Learning Resources

### Internal Documentation
- Architecture documentation in `docs/architecture/`
- Agent documentation in `docs/agents/`
- Security documentation in `docs/security/`

### External Resources
- FastAPI documentation: https://fastapi.tiangolo.com/
- Pydantic documentation: https://pydantic-docs.helpmanual.io/
- SQLAlchemy documentation: https://docs.sqlalchemy.org/

### Community
- GitHub Issues for bug reports and feature requests
- Discussions for questions and ideas
- Wiki for community-contributed guides

---

Choose the appropriate guide based on your experience level and specific needs.
