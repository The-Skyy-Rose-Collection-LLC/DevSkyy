# Testing Frameworks

This skill provides comprehensive knowledge of testing frameworks across multiple languages. It activates when users mention "pytest", "jest", "vitest", "mocha", "go test", "cargo test", "unittest", "testing-library", or need to write, run, or debug tests.

---

## Framework Detection

Detect testing framework by project files:

| File/Pattern | Framework | Language |
|--------------|-----------|----------|
| `pytest.ini`, `conftest.py`, `test_*.py` | pytest | Python |
| `setup.cfg` with `[tool:pytest]` | pytest | Python |
| `pyproject.toml` with `[tool.pytest]` | pytest | Python |
| `jest.config.js`, `*.test.js`, `*.spec.js` | Jest | JavaScript |
| `vitest.config.ts`, `*.test.ts` | Vitest | TypeScript |
| `*_test.go` | go test | Go |
| `*_test.rs`, `Cargo.toml` | cargo test | Rust |
| `*.test.tsx`, `*.spec.tsx` | Jest/Vitest | React |

## pytest (Python)

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_endpoint_health

# Run with coverage
pytest --cov=src --cov-report=html

# Run failed tests only
pytest --lf

# Run tests matching pattern
pytest -k "test_user"

# Stop on first failure
pytest -x

# Parallel execution
pytest -n auto
```

### Test Structure
```python
import pytest
from mymodule import MyClass

class TestMyClass:
    """Test suite for MyClass."""

    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return MyClass()

    def test_initialization(self, instance):
        """Test that instance initializes correctly."""
        assert instance is not None
        assert instance.value == 0

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (0, 0),
    ])
    def test_double(self, instance, input, expected):
        """Test double method with various inputs."""
        assert instance.double(input) == expected

    @pytest.mark.asyncio
    async def test_async_operation(self, instance):
        """Test async method."""
        result = await instance.async_fetch()
        assert result is not None
```

### Common Fixtures
```python
@pytest.fixture
def mock_db(mocker):
    """Mock database connection."""
    return mocker.patch('mymodule.db.connect')

@pytest.fixture
def temp_file(tmp_path):
    """Create temporary test file."""
    file = tmp_path / "test.txt"
    file.write_text("test content")
    return file

@pytest.fixture(scope="session")
def app():
    """Create test application."""
    from myapp import create_app
    return create_app(testing=True)
```

## Jest (JavaScript/TypeScript)

### Running Tests
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific file
npm test -- tests/api.test.js

# Watch mode
npm test -- --watch

# Update snapshots
npm test -- -u

# Run tests matching pattern
npm test -- -t "user login"
```

### Test Structure
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
  });

  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const onClick = jest.fn();
    render(<MyComponent onClick={onClick} />);

    fireEvent.click(screen.getByRole('button'));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('fetches data on mount', async () => {
    render(<MyComponent />);

    await screen.findByText('Loaded');

    expect(screen.getByTestId('data')).toHaveTextContent('result');
  });
});
```

### Mocking
```javascript
// Mock module
jest.mock('./api', () => ({
  fetchUser: jest.fn(() => Promise.resolve({ name: 'Test' })),
}));

// Mock implementation
const mockFn = jest.fn().mockImplementation(() => 'mocked');

// Spy on method
const spy = jest.spyOn(object, 'method');
```

## Vitest (TypeScript/Vite)

### Running Tests
```bash
# Run all tests
npx vitest

# Run with UI
npx vitest --ui

# Run with coverage
npx vitest --coverage

# Watch mode (default)
npx vitest

# Run once
npx vitest run
```

### Test Structure
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { myFunction } from './myModule';

describe('myFunction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns expected value', () => {
    expect(myFunction(1)).toBe(2);
  });

  it('handles async operations', async () => {
    const result = await myFunction.async();
    expect(result).toBeDefined();
  });
});
```

## Go Testing

### Running Tests
```bash
# Run all tests
go test ./...

# Run with verbose
go test -v ./...

# Run specific package
go test ./pkg/api

# Run with coverage
go test -cover ./...

# Run benchmarks
go test -bench=. ./...

# Run with race detector
go test -race ./...
```

### Test Structure
```go
package mypackage

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestMyFunction(t *testing.T) {
    result := MyFunction(1)
    assert.Equal(t, 2, result)
}

func TestMyFunction_EdgeCase(t *testing.T) {
    result := MyFunction(0)
    assert.Equal(t, 0, result)
}

// Table-driven tests
func TestMyFunction_Multiple(t *testing.T) {
    tests := []struct {
        name     string
        input    int
        expected int
    }{
        {"positive", 1, 2},
        {"zero", 0, 0},
        {"negative", -1, -2},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := MyFunction(tt.input)
            assert.Equal(t, tt.expected, result)
        })
    }
}
```

## Rust Testing

### Running Tests
```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run ignored tests
cargo test -- --ignored

# Run doc tests
cargo test --doc
```

### Test Structure
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        assert_eq!(my_function(1), 2);
    }

    #[test]
    #[should_panic(expected = "division by zero")]
    fn test_panic() {
        divide(1, 0);
    }

    #[test]
    fn test_result() -> Result<(), String> {
        let result = my_fallible_function()?;
        assert_eq!(result, expected);
        Ok(())
    }
}
```

## Common Testing Patterns

### Arrange-Act-Assert (AAA)
```python
def test_user_creation():
    # Arrange
    email = "test@example.com"
    password = "secure123"

    # Act
    user = create_user(email, password)

    # Assert
    assert user.email == email
    assert user.is_active
```

### Given-When-Then (BDD)
```javascript
describe('User Login', () => {
  it('should authenticate valid credentials', () => {
    // Given
    const credentials = { email: 'test@example.com', password: 'valid' };

    // When
    const result = authenticate(credentials);

    // Then
    expect(result.success).toBe(true);
  });
});
```

## Test File Naming Conventions

| Language | Pattern | Example |
|----------|---------|---------|
| Python | `test_*.py` or `*_test.py` | `test_api.py` |
| JavaScript | `*.test.js` or `*.spec.js` | `api.test.js` |
| TypeScript | `*.test.ts` or `*.spec.ts` | `api.test.ts` |
| Go | `*_test.go` | `api_test.go` |
| Rust | Inside `#[cfg(test)]` module | `mod tests` |
