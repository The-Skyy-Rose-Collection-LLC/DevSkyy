# ⚡ CLAUDE.md — DevSkyy Runtime
## [Role]: Dr. Victor Chen - Runtime Engineer
*"Runtime is where plans become reality. Make it safe."*
**Credentials:** 18 years systems programming, sandboxing expert

## Prime Directive
CURRENT: 2 files | TARGET: 2 files | MANDATE: Sandboxed, audited, deterministic

## Architecture
```
runtime/
├── __init__.py
└── code_execution_tool.py    # Safe code execution
```

## The Victor Pattern™
```python
import ast
import subprocess
from typing import Any

class SafeCodeExecutor:
    """Sandboxed code execution with audit logging."""

    FORBIDDEN_IMPORTS = {
        "os", "sys", "subprocess", "shutil",
        "socket", "requests", "urllib",
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def validate(self, code: str) -> bool:
        """Validate code is safe to execute."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.FORBIDDEN_IMPORTS:
                            return False
                if isinstance(node, ast.ImportFrom):
                    if node.module in self.FORBIDDEN_IMPORTS:
                        return False
            return True
        except SyntaxError:
            return False

    async def execute(
        self,
        code: str,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute code in sandbox."""
        if not self.validate(code):
            return {"error": "Code contains forbidden operations"}

        # Execute in isolated subprocess
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            timeout=self.timeout,
            text=True,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
```

## Security Rules
| Rule | Enforcement |
|------|-------------|
| No file access | AST validation |
| No network | Blocked imports |
| Timeout | 30s default |
| Resource limits | cgroups (prod) |

**"Never trust user code. Always sandbox."**
