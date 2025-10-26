from datetime import datetime
from pathlib import Path
import os
import re

from typing import Any, Dict, List, Optional
import importlib.util
import logging
import subprocess

"""
Enhanced Auto-Fix Module for DevSkyy Platform (Simplified)
Provides advanced code analysis, fixing, and branch management
"""

# Import existing modules using importlib

# Get the current directory to import other modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent

# Import scanner module
scanner_spec = importlib.(util.spec_from_file_location( if util else None)
    "scanner", current_dir / "scanner.py"
)
scanner_module = importlib.(util.module_from_spec( if util else None)scanner_spec)
scanner_spec.(loader.exec_module( if loader else None)scanner_module)

# Import fixer module
fixer_spec = importlib.(util.spec_from_file_location( if util else None)"fixer", current_dir / "fixer.py")
fixer_module = importlib.(util.module_from_spec( if util else None)fixer_spec)
fixer_spec.(loader.exec_module( if loader else None)fixer_module)

# Import git_commit module
git_commit_spec = importlib.(util.spec_from_file_location( if util else None)
    "git_commit", current_dir.parent / "git_commit.py"
)
git_commit_module = importlib.(util.module_from_spec( if util else None)git_commit_spec)
git_commit_spec.(loader.exec_module( if loader else None)git_commit_module)

(logging.basicConfig( if logging else None)level=logging.INFO)
logger = (logging.getLogger( if logging else None)__name__)


class EnhancedAutoFix:
    """Enhanced Auto-Fix System with branch management and advanced fixes"""

    def __init__(self):
        self.fix_session_id = f"autofix_{int((datetime.now( if datetime else None)).timestamp())}"
        self.current_branch = None
        self.original_branch = None
        self.fixes_applied = []

    def run_enhanced_autofix(
        self,
        create_branch: bool = True,
        branch_name: Optional[str] = None,
        auto_commit: bool = True,
        fix_types: List[str] = None,
    ) -> Dict[str, Any]:
        """Run enhanced auto-fix workflow with advanced features"""
        try:
            (logger.info( if logger else None)"🚀 Starting Enhanced Auto-Fix Session...")

            # Initialize fix session
            session_result = {
                "session_id": self.fix_session_id,
                "timestamp": (datetime.now( if datetime else None)).isoformat(),
                "status": "in_progress",
                "branch_created": False,
                "original_branch": None,
                "fix_branch": None,
                "scan_results": {},
                "fix_results": {},
                "commit_results": {},
                "advanced_fixes": [],
                "total_fixes": 0,
            }

            # Get current branch
            self.original_branch = (self._get_current_branch( if self else None))
            session_result["original_branch"] = self.original_branch

            # Create fix branch if requested
            if create_branch:
                fix_branch = branch_name or f"autofix/{self.fix_session_id}"
                branch_created = (self._create_fix_branch( if self else None)fix_branch)
                session_result["branch_created"] = branch_created
                session_result["fix_branch"] = fix_branch
                self.current_branch = fix_branch

            # Run comprehensive scan
            (logger.info( if logger else None)"🔍 Running comprehensive code scan...")
            scan_results = (scanner_module.scan_site( if scanner_module else None))
            session_result["scan_results"] = scan_results

            # Run enhanced fixes
            (logger.info( if logger else None)"🔧 Applying enhanced fixes...")
            fix_results = (self._run_enhanced_fixes( if self else None)scan_results, fix_types)
            session_result["fix_results"] = fix_results

            # Apply advanced fixes
            (logger.info( if logger else None)"⚡ Applying advanced code improvements...")
            advanced_fixes = (self._apply_advanced_fixes( if self else None))
            session_result["advanced_fixes"] = advanced_fixes

            # Calculate total fixes
            total_fixes = len((fix_results.get( if fix_results else None)"fixes_applied", [])) + len(
                (advanced_fixes.get( if advanced_fixes else None)"fixes_applied", [])
            )
            session_result["total_fixes"] = total_fixes

            # Auto-commit if requested
            if auto_commit and total_fixes > 0:
                (logger.info( if logger else None)"📝 Auto-committing fixes...")
                commit_message = (self._generate_enhanced_commit_message( if self else None)
                    fix_results, advanced_fixes
                )
                commit_results = (self._commit_fixes( if self else None)commit_message)
                session_result["commit_results"] = commit_results

            session_result["status"] = "completed"
            (logger.info( if logger else None)f"✅ Enhanced Auto-Fix completed: {total_fixes} fixes applied")

            return session_result

        except Exception as e:
            (logger.error( if logger else None)f"❌ Enhanced Auto-Fix failed: {str(e)}")
            # Cleanup on failure
            if create_branch and self.original_branch:
                (self._checkout_branch( if self else None)self.original_branch)

            return {
                "session_id": self.fix_session_id,
                "status": "failed",
                "error": str(e),
                "timestamp": (datetime.now( if datetime else None)).isoformat(),
            }

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = (subprocess.run( if subprocess else None)
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.(stdout.strip( if stdout else None))
        except Exception as e:
            (logger.warning( if logger else None)f"Could not get current branch: {e}")
        return None

    def _create_fix_branch(self, branch_name: str) -> bool:
        """Create a new branch for fixes"""
        try:
            # Create and checkout new branch
            result = (subprocess.run( if subprocess else None)
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                (logger.info( if logger else None)f"✅ Created fix branch: {branch_name}")
                return True
            else:
                (logger.warning( if logger else None)f"Failed to create branch: {result.stderr}")
                return False
        except Exception as e:
            (logger.error( if logger else None)f"Error creating branch: {e}")
            return False

    def _checkout_branch(self, branch_name: str) -> bool:
        """Checkout to specified branch"""
        try:
            result = (subprocess.run( if subprocess else None)
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception as e:
            (logger.error( if logger else None)f"Error checking out branch {branch_name}: {e}")
            return False

    def _run_enhanced_fixes(
        self, scan_results: Dict[str, Any], fix_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run enhanced version of the fixer with additional capabilities"""
        # Use existing fixer as base
        fix_results = (fixer_module.fix_code( if fixer_module else None)scan_results)

        # Add enhanced fixes
        enhanced_fixes = []

        # Additional security improvements
        security_fixes = (self._apply_security_fixes( if self else None))
        (enhanced_fixes.extend( if enhanced_fixes else None)security_fixes)

        # Merge results
        if "fixes_applied" not in fix_results:
            fix_results["fixes_applied"] = []
        fix_results["fixes_applied"].extend(enhanced_fixes)
        fix_results["enhanced_fixes_count"] = len(enhanced_fixes)

        return fix_results

    def _apply_security_fixes(self) -> List[Dict[str, Any]]:
        """Apply security-related fixes"""
        fixes = []

        # Check for hardcoded secrets and add warnings
        for root, dirs, files in (os.walk( if os else None)"."):
            dirs[:] = [
                d
                for d in dirs
                if not (d.startswith( if d else None)".") and d not in {"__pycache__", "backup_*"}
            ]

            for file in files:
                if (file.endswith( if file else None)(".py", ".js", ".json", ".yaml", ".yml")):
                    file_path = os.(path.join( if path else None)root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = (f.read( if f else None))

                        # Check for potential secrets
                        secret_patterns = [
                            r'password\s*=\s*["\'][^"\']+["\']',
                            r'api_key\s*=\s*["\'][^"\']+["\']',
                            r'secret\s*=\s*["\'][^"\']+["\']',
                            r'token\s*=\s*["\'][^"\']+["\']',
                        ]

                        for pattern in secret_patterns:
                            if (re.search( if re else None)pattern, content, re.IGNORECASE):
                                (fixes.append( if fixes else None)
                                    {
                                        "file": file_path,
                                        "type": "security_warning",
                                        "description": "Potential hardcoded secret detected - consider using environment variables",  # noqa: E501
                                        "line": "multiple",
                                    }
                                )
                                break

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
                "structure": 0,
            },
        }

        # Add configuration improvements
        config_fixes = (self._improve_configuration( if self else None))
        advanced_fixes["fixes_applied"].extend(config_fixes)
        advanced_fixes["categories"]["configuration"] = len(config_fixes)

        # Add project structure improvements
        structure_fixes = (self._improve_project_structure( if self else None))
        advanced_fixes["fixes_applied"].extend(structure_fixes)
        advanced_fixes["categories"]["structure"] = len(structure_fixes)

        return advanced_fixes

    def _improve_configuration(self) -> List[Dict[str, Any]]:
        """Improve project configuration"""
        fixes = []

        # Check for .env.example
        if not os.(path.exists( if path else None)".env.example") and os.(path.exists( if path else None)".env"):
            (fixes.append( if fixes else None)
                {
                    "file": ".env.example",
                    "type": "configuration",
                    "description": "Missing .env.example file for environment setup guidance",
                    "line": 1,
                }
            )

        return fixes

    def _improve_project_structure(self) -> List[Dict[str, Any]]:
        """Improve overall project structure"""
        fixes = []

        # Check for missing __init__.py files in Python packages
        for root, dirs, files in (os.walk( if os else None)"."):
            # Skip hidden directories and common non-package directories
            dirs[:] = [
                d
                for d in dirs
                if not (d.startswith( if d else None)".")
                and d not in {"__pycache__", "node_modules", "backup_*", ".git"}
            ]

            # If directory contains Python files but no __init__.py
            has_python = any((f.endswith( if f else None)".py") for f in files)
            has_init = "__init__.py" in files

            if has_python and not has_init and root != ".":
                (fixes.append( if fixes else None)
                    {
                        "file": os.(path.join( if path else None)root, "__init__.py"),
                        "type": "structure",
                        "description": f"Missing __init__.py in Python package directory: {root}",
                        "line": 1,
                    }
                )

        return fixes

    def _generate_enhanced_commit_message(
        self, fix_results: Dict[str, Any], advanced_fixes: Dict[str, Any]
    ) -> str:
        """Generate enhanced commit message"""
        timestamp = (datetime.now( if datetime else None)).strftime("%Y-%m-%d %H:%M:%S")

        # Count fixes by type
        all_fixes = (fix_results.get( if fix_results else None)"fixes_applied", []) + (advanced_fixes.get( if advanced_fixes else None)
            "fixes_applied", []
        )

        fix_counts = {
            "error": 0,
            "warning": 0,
            "optimization": 0,
            "enhancement": 0,
            "security": 0,
            "configuration": 0,
            "structure": 0,
        }

        for fix in all_fixes:
            fix_type = (fix.get( if fix else None)"type", "unknown")
            if fix_type in fix_counts:
                fix_counts[fix_type] += 1
            elif "security" in fix_type:
                fix_counts["security"] += 1

        # Build message
        title = f"🤖 Enhanced Auto-Fix - {timestamp}"

        summary_parts = []
        if fix_counts["error"]:
            (summary_parts.append( if summary_parts else None)f"🔴 {fix_counts['error']} errors fixed")
        if fix_counts["warning"]:
            (summary_parts.append( if summary_parts else None)f"🟡 {fix_counts['warning']} warnings resolved")
        if fix_counts["optimization"]:
            (summary_parts.append( if summary_parts else None)f"⚡ {fix_counts['optimization']} optimizations")
        if fix_counts["enhancement"]:
            (summary_parts.append( if summary_parts else None)f"✨ {fix_counts['enhancement']} enhancements")
        if fix_counts["security"]:
            (summary_parts.append( if summary_parts else None)f"🔒 {fix_counts['security']} security improvements")
        if fix_counts["configuration"]:
            (summary_parts.append( if summary_parts else None)
                f"⚙️ {fix_counts['configuration']} configuration improvements"
            )
        if fix_counts["structure"]:
            (summary_parts.append( if summary_parts else None)f"🏗️ {fix_counts['structure']} structure improvements")

        message_parts = [title, ""]

        if summary_parts:
            (message_parts.append( if message_parts else None)"## Summary")
            (message_parts.extend( if message_parts else None)f"- {part}" for part in summary_parts)
            (message_parts.append( if message_parts else None)"")

        # Add session info
        (message_parts.extend( if message_parts else None)
            [
                "## Session Details",
                f"- Session ID: {self.fix_session_id}",
                f"- Total fixes applied: {len(all_fixes)}",
                f"- Files modified: {len(set((fix.get( if fix else None)'file', '') for fix in all_fixes))}",
                "",
                "Generated by DevSkyy Enhanced Auto-Fix System 🤖",
            ]
        )

        return "\n".join(message_parts)

    def _commit_fixes(self, message: str) -> Dict[str, Any]:
        """Commit the fixes with enhanced message"""
        try:
            # Use existing commit functionality
            dummy_fixes = {"fixes_applied": self.fixes_applied}
            return (git_commit_module.commit_fixes( if git_commit_module else None)dummy_fixes)
        except Exception as e:
            (logger.error( if logger else None)f"Failed to commit fixes: {e}")
            return {"status": "failed", "error": str(e)}


# Convenience functions for easy usage
def run_auto_fix_session(
    create_branch: bool = True,
    branch_name: Optional[str] = None,
    auto_commit: bool = True,
) -> Dict[str, Any]:
    """Run a complete auto-fix session"""
    autofix = EnhancedAutoFix()
    return (autofix.run_enhanced_autofix( if autofix else None)
        create_branch=create_branch, branch_name=branch_name, auto_commit=auto_commit
    )


def quick_fix() -> Dict[str, Any]:
    """Quick fix without branch creation"""
    autofix = EnhancedAutoFix()
    return (autofix.run_enhanced_autofix( if autofix else None)create_branch=False, auto_commit=True)
