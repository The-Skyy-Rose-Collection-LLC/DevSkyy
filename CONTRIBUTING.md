# Contributing to DevSkyy

Thank you for your interest in contributing to DevSkyy! This document provides guidelines and information for contributors.

## 🎯 Overview

DevSkyy is a luxury fashion AI platform with a multi-AI orchestration system. We welcome contributions that enhance the platform's capabilities, improve code quality, or expand documentation.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for containerized development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SkyyRoseLLC/DevSkyy.git
   cd DevSkyy
   ```

2. **Install development dependencies**
   ```bash
   make dev-install
   ```

3. **Run tests to verify setup**
   ```bash
   make test
   ```

4. **Start the development server**
   ```bash
   make run
   ```

## 📋 Development Workflow

### Code Quality Standards

We maintain high code quality standards inspired by the SkyyRoseLLC/transformers repository:

- **Line Length**: 119 characters (professional standard)
- **Formatting**: Ruff (primary), Black (backup)
- **Linting**: Ruff with comprehensive rules
- **Type Checking**: MyPy for type safety
- **Testing**: Pytest with 90%+ coverage requirement

### Pre-commit Checks

Before committing, run:
```bash
make pre-commit
```

This will:
- Format code with Ruff
- Fix linting issues automatically
- Run fast tests
- Ensure code quality standards

### Full Quality Check

For comprehensive validation:
```bash
make check
```

This runs:
- Code quality checks (linting, formatting, type checking)
- Full test suite with coverage
- Security checks (bandit, safety, pip-audit)

## 🧪 Testing Guidelines

### Test Categories

We use pytest markers to organize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Long-running tests

### Running Specific Tests

```bash
# Unit tests only
make test-unit

# API tests only
make test-api

# Security tests only
make test-security

# Fast tests (excluding slow)
make test-fast

# With coverage report
make test-coverage
```

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source structure in test organization
- Use descriptive test names
- Include docstrings for complex test scenarios
- Mock external dependencies
- Aim for 90%+ code coverage

## 🔒 Security Guidelines

### Security Requirements

- All API endpoints must have authentication
- Input validation using Pydantic models
- No sensitive data in logs or error messages
- Regular security dependency updates

### Security Testing

```bash
# Run security checks
make security

# Generate security report
bandit -r agent api security infrastructure ml ai_orchestration -f html -o security-report.html
```

## 📝 Documentation Standards

### Code Documentation

- Use clear, descriptive docstrings
- Follow Google-style docstring format
- Include type hints for all functions
- Document complex business logic

### API Documentation

- All endpoints must have comprehensive docstrings
- Include request/response examples
- Document authentication requirements
- Specify error conditions

### Example Docstring

```python
async def create_partnership(
    partnership_data: PartnershipCreate,
    current_user: User = Depends(get_current_user)
) -> Partnership:
    """Create a new partnership in the orchestration system.

    Args:
        partnership_data: Partnership creation data including name, type, and configuration
        current_user: Authenticated user making the request

    Returns:
        Partnership: Created partnership object with generated ID and metadata

    Raises:
        HTTPException: 400 if partnership data is invalid
        HTTPException: 403 if user lacks permission
        HTTPException: 409 if partnership already exists

    Example:
        ```python
        partnership = await create_partnership(
            PartnershipCreate(name="AI Assistant", type="technical"),
            current_user
        )
        ```
    """
```

## 🏗️ Architecture Guidelines

### Project Structure

Follow the established structure:

```
DevSkyy/
├── agent/                 # AI agent modules
├── api/                   # API endpoints and routers
├── security/              # Authentication and security
├── infrastructure/        # Infrastructure components
├── ml/                    # Machine learning modules
├── ai_orchestration/      # Orchestration system
├── database/              # Database utilities
├── monitoring/            # Monitoring and metrics
├── architecture/          # Architecture patterns
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

### Coding Standards

- Use type hints consistently
- Follow single responsibility principle
- Implement proper error handling
- Use dependency injection for testability
- Follow RESTful API design principles

## 🔄 Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   make check
   ```

4. **Commit with descriptive messages**
   ```bash
   git commit -m "feat: add partnership metrics endpoint

   - Implement GET /api/v1/orchestration/partnerships/{id}/metrics
   - Add comprehensive error handling and validation
   - Include unit and integration tests
   - Update API documentation"
   ```

### Pull Request Guidelines

- **Title**: Use conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
- **Description**: Clearly explain what changes were made and why
- **Testing**: Describe how the changes were tested
- **Breaking Changes**: Highlight any breaking changes
- **Screenshots**: Include screenshots for UI changes

### Review Process

1. Automated checks must pass (CI/CD pipeline)
2. Code review by at least one maintainer
3. Security review for security-related changes
4. Performance review for performance-critical changes

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues to avoid duplicates
2. Verify the bug with the latest version
3. Gather relevant information (logs, environment, steps to reproduce)

### Bug Report Template

```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.11.5]
- DevSkyy Version: [e.g. 1.0.0]

**Additional Context**
Any other context about the problem.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the use case and why this feature would be valuable.

**Proposed Solution**
If you have ideas on how to implement this, please describe.

**Alternatives Considered**
Any alternative solutions or features you've considered.

**Additional Context**
Any other context or screenshots about the feature request.
```

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Email**: dev@skyyrose.co for private inquiries

### Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Annual contributor appreciation

## 📄 License

By contributing to DevSkyy, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to DevSkyy! Your efforts help make luxury fashion AI more accessible and powerful. 🚀
