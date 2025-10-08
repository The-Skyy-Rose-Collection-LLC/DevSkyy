# Contributing to DevSkyy

Thank you for your interest in contributing to DevSkyy! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- MongoDB 4.4 or higher
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/SkyyRoseLLC/DevSkyy.git
cd DevSkyy

# Install Python dependencies
make install

# Install frontend dependencies
make frontend-install

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Run tests to verify setup
make test
```

## Development Workflow

1. **Fork the Repository**: Create your own fork of the project
2. **Create a Branch**: Create a feature branch from `develop`
   ```bash
   git checkout -b feature/your-feature-name develop
   ```
3. **Make Changes**: Implement your changes following our code standards
4. **Test**: Ensure all tests pass and add new tests for your changes
5. **Commit**: Write clear, descriptive commit messages
6. **Push**: Push your changes to your fork
7. **Pull Request**: Open a pull request to the `develop` branch

## Code Standards

### Python

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Maximum line length: 120 characters
- Use meaningful variable and function names
- Add docstrings to all public functions and classes

```python
def process_order(order_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Process a customer order.
    
    Args:
        order_id: Unique order identifier
        customer_id: Customer identifier
        
    Returns:
        Dictionary containing order processing results
        
    Raises:
        OrderNotFoundException: If order is not found
        ValidationException: If order data is invalid
    """
    pass
```

### TypeScript/JavaScript

- Use TypeScript for all new frontend code
- Follow ESLint and Prettier configurations
- Use functional components with hooks for React
- Add proper type definitions for all props and functions

```typescript
interface ProductCardProps {
  product: Product
  onAddToCart: (productId: string) => void
}

const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart }) => {
  // Component implementation
}
```

### Code Formatting

We use automated formatters to ensure consistent code style:

```bash
# Format Python code
make format

# Format frontend code
make frontend-format

# Check formatting without making changes
make lint
make frontend-lint
```

## Testing

### Backend Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_agents.py -v
```

### Frontend Tests

```bash
# Run frontend tests
cd frontend && npm test

# Run with coverage
cd frontend && npm test -- --coverage
```

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage (target: >80%)
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert

```python
def test_create_product_success():
    # Arrange
    product_data = {"name": "Test Product", "price": 99.99}
    
    # Act
    result = create_product(product_data)
    
    # Assert
    assert result["success"] is True
    assert result["data"]["name"] == "Test Product"
```

## Pull Request Process

1. **Update Documentation**: Update README.md and relevant docs if needed
2. **Add Tests**: Include tests for new functionality
3. **Update Changelog**: Add entry to CHANGELOG.md
4. **Run Checks**: Ensure all checks pass:
   ```bash
   make pre-commit
   ```
5. **Write Description**: Provide clear description of changes
6. **Link Issues**: Reference any related issues
7. **Request Review**: Request review from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

## Commit Messages

Follow conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Examples:
```
feat(agents): add new fashion vision agent
fix(api): resolve timeout issue in product endpoint
docs(readme): update installation instructions
```

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Questions?

If you have questions:
- Check existing issues and discussions
- Create a new issue with the `question` label
- Contact: support@skyyrose.com

Thank you for contributing to DevSkyy! 🚀