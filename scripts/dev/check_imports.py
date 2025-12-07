#!/usr/bin/env python3
"""
Import Syntax Verification Script
Verifies that all import statements are syntactically correct
without actually executing them
"""

import ast
from pathlib import Path
import sys


# Critical files to verify
CRITICAL_FILES = [
    "main.py",
    "database.py",
    "config/unified_config.py",
    "core/error_ledger.py",
    "core/exceptions.py",
    "api/v1/agents.py",
    "api/v1/dashboard.py",
    "api/v1/luxury_fashion_automation.py",
    "agent/modules/backend/self_learning_system.py",
    "agent/modules/backend/cache_manager.py",
    "api/training_data_interface.py",
]


def extract_imports(file_path: Path) -> tuple[bool, list[str], str]:
    """
    Extract and verify all import statements from a Python file.
    Returns (success, imports_list, error_message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the file into an AST
        tree = ast.parse(content, filename=str(file_path))

        imports = []

        # Extract all import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        f"from {module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                    )

        return True, imports, ""

    except SyntaxError as e:
        return False, [], f"Syntax error: Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, [], f"Error: {e!s}"


def check_common_issues(imports: list[str]) -> list[str]:
    """Check for common import issues"""
    issues = []

    # Check for potential import shadowing
    import_names = []
    for imp in imports:
        if " as " in imp:
            name = imp.split(" as ")[1].strip()
        elif "import " in imp:
            name = imp.split("import ")[1].split(",")[0].strip()
        else:
            continue

        if name in import_names:
            issues.append(f"Potential duplicate import: {name}")
        import_names.append(name)

    return issues


def main():
    """Main verification function"""

    base_path = Path("/home/user/DevSkyy")
    passed = 0
    failed = 0
    total_imports = 0

    for file_path in CRITICAL_FILES:
        full_path = base_path / file_path

        if not full_path.exists():
            failed += 1
            continue

        success, imports, _error = extract_imports(full_path)

        if success:
            issues = check_common_issues(imports)

            if issues:
                for _issue in issues:
                    pass
            else:
                pass

            passed += 1
            total_imports += len(imports)
        else:
            failed += 1

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
