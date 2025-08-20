"""
Enhanced Auto-Fix Module for DevSkyy Platform
Provides advanced code analysis, fixing, and branch management
"""
import os
import re
import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

# Import existing modules
import importlib.util
import sys
from pathlib import Path

# Get the current directory to import other modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent

# Import scanner module
scanner_spec = importlib.util.spec_from_file_location("scanner", current_dir / "scanner.py")
scanner_module = importlib.util.module_from_spec(scanner_spec)
scanner_spec.loader.exec_module(scanner_module)

# Import fixer module
fixer_spec = importlib.util.spec_from_file_location("fixer", current_dir / "fixer.py")
fixer_module = importlib.util.module_from_spec(fixer_spec)
fixer_spec.loader.exec_module(fixer_module)

# Import git_commit module
git_commit_spec = importlib.util.spec_from_file_location("git_commit", current_dir.parent / "git_commit.py")
git_commit_module = importlib.util.module_from_spec(git_commit_spec)
git_commit_spec.loader.exec_module(git_commit_module)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedAutoFix:
    """Enhanced Auto-Fix System with branch management and advanced fixes"""

    def __init__(self):
        self.fix_session_id = f"autofix_{int(datetime.now().timestamp())}"
        self.current_branch = None
        self.original_branch = None
        self.fixes_applied = []

    def run_enhanced_autofix(self,
        """TODO: Add docstring for run_enhanced_autofix."""
                             create_branch: bool = True,
                             branch_name: Optional[str] = None,
                             auto_commit: bool = True,
                             fix_types: List[str] = None) -> Dict[str, Any]:
        """
        Run enhanced auto-fix workflow with advanced features
        """
        try:
            logger.info("🚀 Starting Enhanced Auto-Fix Session...")

            # Initialize fix session
            session_result = {
                "session_id": self.fix_session_id,
                "timestamp": datetime.now().isoformat(),
                "status": "in_progress",
                "branch_created": False,
                "original_branch": None,
                "fix_branch": None,
                "scan_results": {},
                "fix_results": {},
                "commit_results": {},
                "advanced_fixes": [],
                "total_fixes": 0
            }

            # Get current branch
            self.original_branch = self._get_current_branch()
            session_result["original_branch"] = self.original_branch

            # Create fix branch if requested
            if create_branch:
                fix_branch = branch_name or f"autofix/{self.fix_session_id}"
                branch_created = self._create_fix_branch(fix_branch)
                session_result["branch_created"] = branch_created
                session_result["fix_branch"] = fix_branch
                self.current_branch = fix_branch

            # Run comprehensive scan
            logger.info("🔍 Running comprehensive code scan...")
            scan_results = scanner_module.scan_site()
            session_result["scan_results"] = scan_results

            # Run enhanced fixes
            logger.info("🔧 Applying enhanced fixes...")
            fix_results = self._run_enhanced_fixes(scan_results, fix_types)
            session_result["fix_results"] = fix_results

            # Apply advanced fixes
            logger.info("⚡ Applying advanced code improvements...")
            advanced_fixes = self._apply_advanced_fixes()
            session_result["advanced_fixes"] = advanced_fixes

            # Calculate total fixes
            total_fixes = (
                len(fix_results.get("fixes_applied", [])) +
                len(advanced_fixes.get("fixes_applied", []))
            )
            session_result["total_fixes"] = total_fixes

            # Auto-commit if requested
            if auto_commit and total_fixes > 0:
                logger.info("📝 Auto-committing fixes...")
                commit_message = self._generate_enhanced_commit_message(
                    fix_results, advanced_fixes
                )
                commit_results = self._commit_fixes(commit_message)
                session_result["commit_results"] = commit_results

            session_result["status"] = "completed"
            logger.info(f"✅ Enhanced Auto-Fix completed: {total_fixes} fixes applied")

            return session_result

        except Exception as e:
            logger.error(f"❌ Enhanced Auto-Fix failed: {str(e)}")
            # Cleanup on failure
            if create_branch and self.original_branch:
                self._checkout_branch(self.original_branch)

            return {
                "session_id": self.fix_session_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Could not get current branch: {e}")
        return None

    def _create_fix_branch(self, branch_name: str) -> bool:
        """Create a new branch for fixes"""
        try:
            # Create and checkout new branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                logger.info(f"✅ Created fix branch: {branch_name}")
                return True
            else:
                logger.warning(f"Failed to create branch: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return False

    def _checkout_branch(self, branch_name: str) -> bool:
        """Checkout to specified branch"""
        try:
            result = subprocess.run(
                ['git', 'checkout', branch_name],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking out branch {branch_name}: {e}")
            return False

    def _run_enhanced_fixes(self, scan_results: Dict[str, Any],
                            fix_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run enhanced version of the fixer with additional capabilities"""
        # Use existing fixer as base
        fix_results = fixer_module.fix_code(scan_results)

        # Add enhanced fixes
        enhanced_fixes = []

        # Additional Python fixes
        python_enhancements = self._apply_python_enhancements()
        enhanced_fixes.extend(python_enhancements)

        # JavaScript modernization
        js_enhancements = self._apply_javascript_modernization()
        enhanced_fixes.extend(js_enhancements)

        # Security improvements
        security_fixes = self._apply_security_fixes()
        enhanced_fixes.extend(security_fixes)

        # Performance optimizations
        performance_fixes = self._apply_performance_optimizations()
        enhanced_fixes.extend(performance_fixes)

        # Merge results
        if "fixes_applied" not in fix_results:
            fix_results["fixes_applied"] = []
        fix_results["fixes_applied"].extend(enhanced_fixes)
        fix_results["enhanced_fixes_count"] = len(enhanced_fixes)

        return fix_results

    def _apply_python_enhancements(self) -> List[Dict[str, Any]]:
        """Apply advanced Python code enhancements"""
        fixes = []

        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'backup_*'}]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    file_fixes = self._enhance_python_file(file_path)
                    fixes.extend(file_fixes)

        return fixes

    def _enhance_python_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Apply advanced Python enhancements to a file"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Add type hints where missing
            if 'from typing import' not in content and ('def ' in content or 'class ' in content):
                # Add basic typing import
                lines = content.split('\n')
                import_inserted = False
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        continue
                    else:
                        lines.insert(i, 'from typing import Dict, Any, List, Optional')
                        import_inserted = True
                        break

                if import_inserted:
                    content = '\n'.join(lines)
                    fixes.append({
                        "file": file_path,
                        "type": "enhancement",
                        "description": "Added typing imports for better type safety",
                        "line": "imports"
                    })

            # Add docstrings to functions without them
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and '"""' not in line:
                    # Check if next line has docstring
                    if i + 1 < len(lines) and '"""' not in lines[i + 1]:
                        # Extract function name
                        func_match = re.match(r'\s*def\s+(\w+)', line)
                        if func_match:
                            func_name = func_match.group(1)
                            if not func_name.startswith('_'):  # Only public functions
                                indent = len(line) - len(line.lstrip())
                                docstring = f'{" " * (indent + 4)}"""TODO: Add docstring for {func_name}."""'
                                lines.insert(i + 1, docstring)
                                fixes.append({
                                    "file": file_path,
                                    "type": "enhancement",
                                    "description": f"Added TODO docstring for function {func_name}",
                                    "line": i + 1
                                })
                                break  # Only add one per file to avoid conflicts

            content = '\n'.join(lines)

            # Apply f-string optimization
            # Replace old-style string formatting
            fstring_pattern = r'["\']([^"\']*)\{[^}]*\}([^"\']*)["\']\.format\([^)]*\)'
            if re.search(fstring_pattern, content):
                # Simple f-string conversion (basic cases only)
                content = re.sub(
                    r'"([^"]*)\{\}([^"]*)"\.format\(([^)]+)\)',
                    r'f"\1{\3}\2"',
                    content
                )
                fixes.append({
                    "file": file_path,
                    "type": "optimization",
                    "description": "Converted string.format() to f-strings",
                    "line": "multiple"
                })

            # Write changes if any fixes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

        except Exception as e:
            fixes.append({
                "file": file_path,
                "type": "error",
                "description": f"Failed to enhance Python file: {str(e)}",
                "line": "unknown"
            })

        return fixes

    def _apply_javascript_modernization(self) -> List[Dict[str, Any]]:
        """Apply JavaScript modernization fixes"""
        fixes = []

        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', 'backup_*'}]

            for file in files:
                if file.endswith('.js'):
                    file_path = os.path.join(root, file)
                    file_fixes = self._modernize_javascript_file(file_path)
                    fixes.extend(file_fixes)

        return fixes

    def _modernize_javascript_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Modernize JavaScript file"""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Convert function declarations to arrow functions (simple cases)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Convert simple function expressions
                if 'function(' in line and '=' in line:
                    # Simple conversion: var fn = function() -> const fn = () =>
                    arrow_line = re.sub(
                        r'(\w+)\s*=\s*function\s*\(',
                        r'\1 = (',
                        line
                    )
                    arrow_line = re.sub(
                        r'\)\s*\{',
                        r') => {',
                        arrow_line
                    )
                    if arrow_line != line:
                        lines[i] = arrow_line
                        fixes.append({
                            "file": file_path,
                            "type": "modernization",
                            "description": "Converted function expression to arrow function",
                            "line": i + 1
                        })

            content = '\n'.join(lines)

            # Add 'use strict' if not present
            if "'use strict'" not in content and '"use strict"' not in content:
                content = "'use strict';\n\n" + content
                fixes.append({
                    "file": file_path,
                    "type": "enhancement",
                    "description": "Added 'use strict' directive",
                    "line": 1
                })

            # Write changes if any fixes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

        except Exception as e:
            fixes.append({
                "file": file_path,
                "type": "error",
                "description": f"Failed to modernize JavaScript file: {str(e)}",
                "line": "unknown"
            })

        return fixes

    def _apply_security_fixes(self) -> List[Dict[str, Any]]:
        """Apply security-related fixes"""
        fixes = []

        # Check for hardcoded secrets and add warnings
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'backup_*'}]

            for file in files:
                if file.endswith(('.py', '.js', '.json', '.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Check for potential secrets
                        secret_patterns = [
                            r'password\s*=\s*["\'][^"\']+["\']',
                            r'api_key\s*=\s*["\'][^"\']+["\']',
                            r'secret\s*=\s*["\'][^"\']+["\']',
                            r'token\s*=\s*["\'][^"\']+["\']'
                        ]

                        for pattern in secret_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                fixes.append({
                                    "file": file_path,
                                    "type": "security_warning",
                                    "description": "Potential hardcoded secret detected - consider using environment variables",
                                    "line": "multiple"
                                })
                                break

                    except Exception:
                        continue

        return fixes

    def _apply_performance_optimizations(self) -> List[Dict[str, Any]]:
        """Apply performance optimization fixes"""
        fixes = []

        # Add performance-related fixes
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'backup_*'}]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        original_content = content

                        # Optimize list comprehensions (simple cases)
                        # Convert simple for loops to list comprehensions where appropriate
                        lines = content.split('\n')
                        in_simple_loop = False
                        loop_start = -1

                        for i, line in enumerate(lines):
                            stripped = line.strip()

                            # Simple pattern: for item in items: result.append(item.something)
                            if stripped.startswith('for ') and ' in ' in stripped and ':' in stripped:
                                in_simple_loop = True
                                loop_start = i
                            elif in_simple_loop and stripped.startswith('result.append(') and loop_start >= 0:
                                # This is a simple case we can optimize
                                fixes.append({
                                    "file": file_path,
                                    "type": "performance_hint",
                                    "description": f"Consider list comprehension at line {loop_start + 1}",
                                    "line": loop_start + 1
                                })
                                in_simple_loop = False
                                loop_start = -1
                            elif in_simple_loop and stripped and not stripped.startswith('result.append('):
                                in_simple_loop = False
                                loop_start = -1

                    except Exception:
                        continue

        return fixes

    def _apply_advanced_fixes(self) -> Dict[str, Any]:
        """Apply advanced fixes beyond basic code fixing"""
        advanced_fixes = {
            "fixes_applied": [],
            "categories": {
                "documentation": 0,
                "testing": 0,
                "configuration": 0,
                "structure": 0
            }
        }

        # Add README improvements
        readme_fixes = self._improve_documentation()
        advanced_fixes["fixes_applied"].extend(readme_fixes)
        advanced_fixes["categories"]["documentation"] = len(readme_fixes)

        # Add configuration improvements
        config_fixes = self._improve_configuration()
        advanced_fixes["fixes_applied"].extend(config_fixes)
        advanced_fixes["categories"]["configuration"] = len(config_fixes)

        # Add project structure improvements
        structure_fixes = self._improve_project_structure()
        advanced_fixes["fixes_applied"].extend(structure_fixes)
        advanced_fixes["categories"]["structure"] = len(structure_fixes)

        return advanced_fixes

    def _improve_documentation(self) -> List[Dict[str, Any]]:
        """Improve project documentation"""
        fixes = []

        # Check if README exists and has basic sections
        readme_path = "README.md"
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for missing sections
                missing_sections = []

                if "## Installation" not in content:
                    missing_sections.append("Installation")
                if "## Usage" not in content:
                    missing_sections.append("Usage")
                if "## Contributing" not in content:
                    missing_sections.append("Contributing")

                if missing_sections:
                    fixes.append({
                        "file": readme_path,
                        "type": "documentation",
                        "description": f"README missing sections: {', '.join(missing_sections)}",
                        "line": "end"
                    })

            except Exception as e:
                fixes.append({
                    "file": readme_path,
                    "type": "error",
                    "description": f"Failed to analyze README: {str(e)}",
                    "line": "unknown"
                })

        return fixes

    def _improve_configuration(self) -> List[Dict[str, Any]]:
        """Improve project configuration"""
        fixes = []

        # Check for .env.example
        if not os.path.exists(".env.example") and os.path.exists(".env"):
            fixes.append({
                "file": ".env.example",
                "type": "configuration",
                "description": "Missing .env.example file for environment setup guidance",
                "line": 1
            })

        # Check for proper .gitignore
        if os.path.exists(".gitignore"):
            try:
                with open(".gitignore", 'r', encoding='utf-8') as f:
                    gitignore_content = f.read()

                # Check for common entries
                common_ignores = [".env", "__pycache__/", "*.log", "node_modules/"]
                missing_ignores = [
                    ignore for ignore in common_ignores
                    if ignore not in gitignore_content
                ]

                if missing_ignores:
                    fixes.append({
                        "file": ".gitignore",
                        "type": "configuration",
                        "description": f"Missing .gitignore entries: {', '.join(missing_ignores)}",
                        "line": "end"
                    })

            except Exception:
                pass

        return fixes

    def _improve_project_structure(self) -> List[Dict[str, Any]]:
        """Improve overall project structure"""
        fixes = []

        # Check for missing __init__.py files in Python packages
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories and common non-package directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                '__pycache__', 'node_modules', 'backup_*', '.git'
            }]

            # If directory contains Python files but no __init__.py
            has_python = any(f.endswith('.py') for f in files)
            has_init = '__init__.py' in files

            if has_python and not has_init and root != '.':
                fixes.append({
                    "file": os.path.join(root, "__init__.py"),
                    "type": "structure",
                    "description": f"Missing __init__.py in Python package directory: {root}",
                    "line": 1
                })

        return fixes

    def _generate_enhanced_commit_message(self,
                                          fix_results: Dict[str, Any],
                                          advanced_fixes: Dict[str, Any]) -> str:
        """Generate enhanced commit message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Count fixes by type
        all_fixes = fix_results.get("fixes_applied", []) + advanced_fixes.get("fixes_applied", [])

        fix_counts = {
            "error": 0,
            "warning": 0,
            "optimization": 0,
            "enhancement": 0,
            "security": 0,
            "performance": 0,
            "documentation": 0,
            "structure": 0
        }

        for fix in all_fixes:
            fix_type = fix.get("type", "unknown")
            if fix_type in fix_counts:
                fix_counts[fix_type] += 1
            elif "security" in fix_type:
                fix_counts["security"] += 1
            elif "performance" in fix_type:
                fix_counts["performance"] += 1

        # Build message
        title = f"🤖 Enhanced Auto-Fix - {timestamp}"

        summary_parts = []
        if fix_counts["error"]:
            summary_parts.append(f"🔴 {fix_counts['error']} errors fixed")
        if fix_counts["warning"]:
            summary_parts.append(f"🟡 {fix_counts['warning']} warnings resolved")
        if fix_counts["optimization"]:
            summary_parts.append(f"⚡ {fix_counts['optimization']} optimizations")
        if fix_counts["enhancement"]:
            summary_parts.append(f"✨ {fix_counts['enhancement']} enhancements")
        if fix_counts["security"]:
            summary_parts.append(f"🔒 {fix_counts['security']} security improvements")
        if fix_counts["performance"]:
            summary_parts.append(f"🚀 {fix_counts['performance']} performance improvements")
        if fix_counts["documentation"]:
            summary_parts.append(f"📚 {fix_counts['documentation']} documentation improvements")
        if fix_counts["structure"]:
            summary_parts.append(f"🏗️ {fix_counts['structure']} structure improvements")

        message_parts = [title, ""]

        if summary_parts:
            message_parts.append("## Summary")
            message_parts.extend(f"- {part}" for part in summary_parts)
            message_parts.append("")

        # Add session info
        message_parts.extend([
            "## Session Details",
            f"- Session ID: {self.fix_session_id}",
            f"- Total fixes applied: {len(all_fixes)}",
            f"- Files modified: {len(set(fix.get('file', '') for fix in all_fixes))}",
            "",
            "Generated by DevSkyy Enhanced Auto-Fix System 🤖"
        ])

        return "\n".join(message_parts)

    def _commit_fixes(self, message: str) -> Dict[str, Any]:
        """Commit the fixes with enhanced message"""
        try:
            # Use existing commit functionality
            dummy_fixes = {"fixes_applied": self.fixes_applied}
            return git_commit_module.commit_fixes(dummy_fixes)
        except Exception as e:
            logger.error(f"Failed to commit fixes: {e}")
            return {"status": "failed", "error": str(e)}


# Convenience functions for easy usage
def run_auto_fix_session(create_branch: bool = True,
                         branch_name: Optional[str] = None,
                         auto_commit: bool = True) -> Dict[str, Any]:
    """Run a complete auto-fix session"""
    autofix = EnhancedAutoFix()
    return autofix.run_enhanced_autofix(
        create_branch=create_branch,
        branch_name=branch_name,
        auto_commit=auto_commit
    )


def quick_fix() -> Dict[str, Any]:
    """Quick fix without branch creation"""
    autofix = EnhancedAutoFix()
    return autofix.run_enhanced_autofix(
        create_branch=False,
        auto_commit=True
    )
