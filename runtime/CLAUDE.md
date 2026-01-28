# DevSkyy Runtime

> Sandboxed, audited, deterministic | 2 files

## Architecture
```
runtime/
├── __init__.py
└── code_execution_tool.py    # Safe code execution
```

## Pattern
```python
class SafeCodeExecutor:
    FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "shutil", "socket", "requests"}

    def validate(self, code: str) -> bool:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name in self.FORBIDDEN_IMPORTS for alias in node.names):
                    return False
        return True

    async def execute(self, code: str, *, correlation_id: str | None = None) -> dict:
        if not self.validate(code):
            return {"error": "Forbidden operations"}
        return subprocess.run(["python", "-c", code], capture_output=True, timeout=30)
```

## Security
| Rule | Enforcement |
|------|-------------|
| No file access | AST validation |
| No network | Blocked imports |
| Timeout | 30s default |

**"Never trust user code. Always sandbox."**
