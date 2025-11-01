# OpenAI Codex Integration with AI-Powered Code Healing

**Modern GPT-4/GPT-3.5-turbo powered code generation and intelligent code healing orchestration**

## Overview

The DevSkyy Codex Integration provides enterprise-grade code generation and AI-powered code healing capabilities using OpenAI's latest models. This replaces the deprecated Codex API (sunset March 2023) with superior GPT-4 and GPT-3.5-turbo models.

### Key Features

- **Code Generation**: Generate production-ready code from natural language descriptions
- **Code Completion**: GitHub Copilot-style intelligent code completion
- **Code Review**: Automated security, bug, and performance analysis
- **Code Healing**: AI-orchestrated multi-agent code fixing
- **Documentation**: Automatic generation of comprehensive documentation
- **Optimization**: Performance and readability improvements
- **Multi-Language**: Python, JavaScript, TypeScript, Java, Go, Rust

---

## Architecture

### Components

#### 1. **Codex Integration** (`ml/codex_integration.py`)
Core code generation engine using OpenAI GPT models.

```python
from ml.codex_integration import codex

# Generate code
result = await codex.generate_code(
    prompt="Create a FastAPI endpoint for user authentication",
    language="python",
    model="gpt-4"
)

# Complete code
completion = await codex.complete_code(
    code_prefix="def calculate_fibonacci(n):\n    ",
    language="python"
)

# Review code
review = await codex.review_code(
    code=my_code,
    language="python"
)
```

#### 2. **Code Healing Orchestrator** (`ml/codex_orchestrator.py`)
AI-powered orchestration of multiple healing agents.

```python
from ml.codex_orchestrator import codex_orchestrator

# Heal code with AI orchestration
result = await codex_orchestrator.heal_code(
    code=buggy_code,
    language="python",
    auto_apply=False  # Manual review recommended
)
```

---

## API Endpoints

### Code Generation

#### `POST /api/v1/codex/generate`
Generate code from natural language description.

**Request:**
```json
{
    "prompt": "Create a function that validates email addresses with regex",
    "language": "python",
    "model": "gpt-4",
    "max_tokens": 2048,
    "temperature": 0.2,
    "context": [
        "Using FastAPI framework",
        "Include error handling"
    ]
}
```

**Response:**
```json
{
    "status": "success",
    "code": "import re\nfrom fastapi import HTTPException\n\ndef validate_email(email: str) -> bool:\n    ...",
    "language": "python",
    "model": "gpt-4-turbo-preview",
    "tokens_used": 256,
    "timestamp": "2025-10-18T03:00:00Z"
}
```

---

### Code Completion

#### `POST /api/v1/codex/complete`
Complete partial code (GitHub Copilot-style).

**Request:**
```json
{
    "code_prefix": "def quicksort(arr):\n    if len(arr) <= 1:\n        ",
    "language": "python",
    "model": "gpt-3.5"
}
```

**Response:**
```json
{
    "status": "success",
    "completions": [
        {
            "code": "return arr\n    pivot = arr[len(arr) // 2]\n    ...",
            "finish_reason": "stop"
        }
    ],
    "language": "python",
    "tokens_used": 128
}
```

---

### Code Explanation

#### `POST /api/v1/codex/explain`
Generate detailed explanation of code.

**Request:**
```json
{
    "code": "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = func(*args)\n        return cache[args]\n    return wrapper",
    "language": "python"
}
```

**Response:**
```json
{
    "status": "success",
    "explanation": "This is a memoization decorator that caches function results...",
    "language": "python",
    "tokens_used": 512
}
```

---

### Code Review

#### `POST /api/v1/codex/review`
Comprehensive code review for bugs, security, and performance.

**Request:**
```json
{
    "code": "user_input = request.args.get('query')\nresult = db.execute(user_input)",
    "language": "python"
}
```

**Response:**
```json
{
    "status": "success",
    "review": "**CRITICAL SECURITY ISSUE**: SQL Injection vulnerability...\n\nRecommendations:\n1. Use parameterized queries\n2. Implement input validation\n...",
    "language": "python",
    "tokens_used": 768
}
```

---

### Documentation Generation

#### `POST /api/v1/codex/document`
Generate comprehensive documentation.

**Request:**
```json
{
    "code": "def process_payment(amount, currency, user_id):\n    pass",
    "language": "python"
}
```

**Response:**
```json
{
    "status": "success",
    "documentation": "```python\ndef process_payment(amount: float, currency: str, user_id: int) -> Dict[str, Any]:\n    \"\"\"\n    Process a payment transaction...\n    \"\"\"",
    "language": "python"
}
```

---

### Code Optimization

#### `POST /api/v1/codex/optimize`
Optimize code for performance and readability.

**Request:**
```json
{
    "code": "result = []\nfor i in range(len(items)):\n    result.append(items[i] * 2)",
    "language": "python"
}
```

**Response:**
```json
{
    "status": "success",
    "optimized_code": "result = [item * 2 for item in items]",
    "explanation": "Replaced inefficient loop with list comprehension...",
    "original_code": "result = []\nfor i in range(len(items)):\n    result.append(items[i] * 2)"
}
```

---

## AI-Powered Code Healing

### Overview

The Code Healing Orchestrator uses GPT-4 to intelligently coordinate multiple healing agents for comprehensive code fixing.

### 5-Phase Healing Process

1. **Scan**: Detect issues (security, bugs, performance)
2. **Analyze**: GPT-4 generates optimal healing strategy
3. **Fix**: Generate AI-powered fixes using Codex
4. **Validate**: Ensure fixes are safe and don't break functionality
5. **Learn**: Store successful patterns for future improvements

### Healing Endpoint

#### `POST /api/v1/codex/heal`
AI-orchestrated code healing with multi-agent coordination.

**Request:**
```json
{
    "code": "def process_user_input(data):\n    result = eval(data)\n    return result",
    "language": "python",
    "auto_apply": false,
    "context": {
        "file_path": "app/utils.py",
        "framework": "FastAPI"
    }
}
```

**Response:**
```json
{
    "status": "success",
    "original_code": "def process_user_input(data):\n    result = eval(data)\n    return result",
    "healed_code": "import json\nfrom fastapi import HTTPException\n\ndef process_user_input(data: str) -> dict:\n    try:\n        return json.loads(data)\n    except json.JSONDecodeError:\n        raise HTTPException(status_code=400, detail=\"Invalid JSON\")",
    "issues_found": 3,
    "issues": [
        {
            "type": "security",
            "severity": "critical",
            "description": "Arbitrary code execution via eval()",
            "line": 2
        },
        {
            "type": "security",
            "severity": "high",
            "description": "No input validation",
            "line": null
        },
        {
            "type": "general",
            "severity": "medium",
            "description": "Missing type hints",
            "line": 1
        }
    ],
    "strategy": {
        "strategy": "1. Replace eval() with safe JSON parsing\n2. Add input validation\n3. Add type hints and error handling\n4. Implement proper exception handling",
        "priority_issues": [...],
        "estimated_fix_time": 90
    },
    "validation": {
        "safe": true,
        "validation_report": "Fixes successfully address all critical issues...",
        "fixes_validated": 1,
        "recommended_action": "apply"
    },
    "applied": false
}
```

### Healing Statistics

#### `GET /api/v1/codex/healing/stats`
Get healing operation statistics.

**Response:**
```json
{
    "total_healings": 42,
    "successful": 38,
    "success_rate": 90.48,
    "recent_healings": [
        {
            "strategy": "Replace eval() with safe JSON parsing...",
            "num_fixes": 1,
            "success": true,
            "timestamp": "2025-10-18T03:00:00Z"
        }
    ]
}
```

---

## Configuration

### Environment Variables

```bash
# Required for Codex features
OPENAI_API_KEY=sk-your-openai-api-key

# Optional - defaults to environment
OPENAI_ORG_ID=org-your-org-id
```

### Model Configuration

The integration uses two models with different use cases:

| Model | Use Case | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| **GPT-4** | Complex generation, analysis, healing | Slower | Highest | Higher |
| **GPT-3.5** | Code completion, simple tasks | Faster | Good | Lower |

**Default Configuration:**
- Code Generation: `gpt-4` (temperature: 0.2)
- Code Completion: `gpt-3.5` (temperature: 0.1)
- Code Review: `gpt-4` (temperature: 0.2)
- Code Healing: `gpt-4` (temperature: 0.2)

---

## Supported Languages

- **Python** - Frameworks: FastAPI, Django, Flask, SQLAlchemy
- **JavaScript** - Frameworks: React, Node.js, Express, Next.js
- **TypeScript** - Frameworks: React, Angular, NestJS
- **Java** - Frameworks: Spring, Hibernate
- **Go** - Frameworks: Gin, Echo, GORM
- **Rust** - Frameworks: Actix, Rocket, Tokio

---

## Usage Examples

### Example 1: Generate FastAPI Endpoint

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/codex/generate",
        json={
            "prompt": "Create a FastAPI endpoint that returns user profile with JWT authentication",
            "language": "python",
            "model": "gpt-4",
            "context": [
                "Using SQLAlchemy for database",
                "Include error handling for user not found",
                "Return JSON response with user details"
            ]
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )

    result = response.json()
    print(result["code"])
```

### Example 2: Heal Insecure Code

```python
insecure_code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    user = db.execute(query)
    return user
"""

response = await client.post(
    "http://localhost:8000/api/v1/codex/heal",
    json={
        "code": insecure_code,
        "language": "python",
        "auto_apply": False  # Review fixes manually
    },
    headers={"Authorization": f"Bearer {access_token}"}
)

healing_result = response.json()
print(f"Issues found: {healing_result['issues_found']}")
print(f"Healed code:\n{healing_result['healed_code']}")
```

### Example 3: Code Review Pipeline

```python
# Automated code review in CI/CD
def review_pull_request(code_changes):
    reviews = []

    for file_path, code in code_changes.items():
        response = await client.post(
            "http://localhost:8000/api/v1/codex/review",
            json={"code": code, "language": "python"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        reviews.append({
            "file": file_path,
            "review": response.json()["review"]
        })

    return reviews
```

---

## Best Practices

### 1. Code Generation

✅ **DO:**
- Provide clear, specific prompts
- Include context (framework, dependencies)
- Review generated code before use
- Test generated code thoroughly

❌ **DON'T:**
- Use vague or ambiguous prompts
- Blindly trust generated code
- Skip testing and validation

### 2. Code Healing

✅ **DO:**
- Set `auto_apply=false` initially
- Review AI-generated fixes
- Test healed code before deployment
- Use healing stats to monitor effectiveness

❌ **DON'T:**
- Enable auto-apply without review
- Skip validation step
- Ignore security warnings

### 3. Model Selection

- **Use GPT-4 for:**
  - Complex algorithms
  - Security-critical code
  - Code review and healing
  - Architecture decisions

- **Use GPT-3.5 for:**
  - Simple completions
  - Basic refactoring
  - Documentation
  - Faster iterations

---

## Security Considerations

### API Key Management
- Store OpenAI API key in environment variables
- Never commit API keys to version control
- Rotate keys regularly
- Monitor API usage and costs

### Code Review
- Always review AI-generated code
- Validate security-critical code manually
- Test all generated code before production
- Use code scanning tools (bandit, safety)

### Auto-Apply Safety
- Default: `auto_apply=false`
- Only enable for non-critical code
- Always validate fixes first
- Monitor healing statistics

---

## Troubleshooting

### "OpenAI API key not configured"
```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-api-key

# Or in .env file
echo "OPENAI_API_KEY=sk-your-api-key" >> .env
```

### "Rate limit exceeded"
- Implement exponential backoff
- Use GPT-3.5 for less critical tasks
- Monitor usage at https://platform.openai.com/usage

### "Model not available"
```python
# Check available models
response = await client.get(
    "http://localhost:8000/api/v1/codex/models",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(response.json())
```

---

## Performance Optimization

### Token Management
- Use `max_tokens` to limit response size
- Monitor token usage per request
- Cache common code patterns

### Model Selection
- GPT-3.5: ~10x faster, ~10x cheaper
- Use for simple tasks and iterations
- Switch to GPT-4 for final production code

### Caching
- Cache common code generation patterns
- Store successful healing strategies
- Reuse validated fixes

---

## Monitoring & Analytics

### Healing Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/codex/healing/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### Usage Tracking
- Monitor OpenAI API usage
- Track healing success rates
- Analyze common issue patterns
- Measure time saved by automation

---

## Migration from Original Codex

The original OpenAI Codex API was deprecated in March 2023. This integration provides superior functionality:

| Feature | Original Codex | DevSkyy Codex |
|---------|---------------|---------------|
| Models | code-davinci-002 | GPT-4, GPT-3.5-turbo |
| Quality | Good | Excellent |
| Context | 8K tokens | 128K tokens (GPT-4) |
| Features | Code completion | Complete suite |
| Orchestration | No | Yes (AI-powered) |
| Healing | No | Yes (multi-agent) |
| Status | Deprecated ❌ | Active ✅ |

---

## Support & Resources

- **Documentation**: `/docs` endpoint
- **API Reference**: `http://localhost:8000/docs`
- **OpenAI Docs**: https://platform.openai.com/docs
- **GitHub Issues**: Report bugs and feature requests
- **Status**: Monitor healing stats endpoint

---

## License & Attribution

Built with OpenAI GPT-4 and GPT-3.5-turbo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-18
**Status**: Production Ready ✅
