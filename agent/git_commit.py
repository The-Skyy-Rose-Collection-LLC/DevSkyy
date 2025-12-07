from datetime import datetime
import logging
import os
from pathlib import Path
import subprocess
from typing import Any


logger = logging.getLogger(__name__)


def commit_fixes(fixes_applied: dict[str, Any]) -> dict[str, Any]:
    """
    Commit code fixes to Git repository with detailed commit messages.
    Production-level Git operations with comprehensive error handling.
    """
    try:
        logger.info("📝 Starting Git commit process...")

        # Ensure we're in a Git repository
        if not Path(".git").exists():
            return _init_git_repo()

        # Configure Git if not configured
        _configure_git()

        # Add all changed files
        add_result = _git_add_files()
        if not add_result["success"]:
            return add_result

        # Generate detailed commit message
        commit_message = _generate_commit_message(fixes_applied)

        # Commit changes
        commit_result = _git_commit(commit_message)
        if not commit_result["success"]:
            return commit_result

        # Push to remote if configured
        push_result = _git_push()

        return {
            "status": "success",
            "commit_hash": commit_result.get("commit_hash"),
            "files_committed": add_result.get("files_added", 0),
            "commit_message": commit_message,
            "pushed_to_remote": push_result.get("success", False),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Git commit failed: {e!s}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def commit_all_changes() -> dict[str, Any]:
    """
    Commit all current changes to the repository.
    Used for manual commits and deployment preparation.
    """
    try:
        logger.info("📝 Committing all current changes...")

        # Check Git status
        status_result = _git_status()
        if not status_result["has_changes"]:
            return {
                "status": "no_changes",
                "message": "No changes to commit",
                "timestamp": datetime.now().isoformat(),
            }

        # Ensure Git is configured
        _configure_git()

        # Add all files
        add_result = _git_add_all()
        if not add_result["success"]:
            return add_result

        # Generate commit message for manual commit
        commit_message = (
            f"Manual commit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nUpdated platform with latest changes"
        )

        # Commit
        commit_result = _git_commit(commit_message)
        if not commit_result["success"]:
            return commit_result

        # Push to remote
        push_result = _git_push()

        return {
            "status": "success",
            "commit_hash": commit_result.get("commit_hash"),
            "files_committed": add_result.get("files_added", 0),
            "pushed_to_remote": push_result.get("success", False),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to commit all changes: {e!s}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def _init_git_repo() -> dict[str, Any]:
    """Initialize a new Git repository."""
    try:
        # Initialize repo
        result = subprocess.run(["git", "init"], check=False, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"status": "failed", "error": "Failed to initialize Git repository"}

        # Create initial .gitignore
        gitignore_content = """
# DevSkyy Enhanced Platform - Git Ignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Backups
backup_*/

# Cache
.cache/
.pythonlibs/
        """.strip()

        with open(".gitignore", "w") as f:
            f.write(gitignore_content)

        logger.info("✅ Git repository initialized")
        return {"status": "initialized"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _configure_git() -> None:
    """Configure Git with default settings."""
    try:
        # Check if user.name is configured
        result = subprocess.run(
            ["git", "config", "user.name"], check=False, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            subprocess.run(["git", "config", "user.name", "DevSkyy Enhanced Platform"], check=False, timeout=10)

        # Check if user.email is configured
        result = subprocess.run(
            ["git", "config", "user.email"], check=False, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            subprocess.run(
                ["git", "config", "user.email", "devskyy@theskyy-rose-collection.com"],
                check=False,
                timeout=10,
            )

        logger.info("✅ Git configuration verified")

    except Exception as e:
        logger.warning(f"⚠️ Git configuration warning: {e!s}")


def _git_status() -> dict[str, Any]:
    """Check Git repository status."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], check=False, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"has_changes": False, "error": "Failed to get Git status"}

        changes = result.stdout.strip()
        return {
            "has_changes": bool(changes),
            "changes": changes.split("\n") if changes else [],
            "clean": not bool(changes),
        }

    except Exception as e:
        return {"has_changes": False, "error": str(e)}


def _git_add_files() -> dict[str, Any]:
    """Add modified files to Git staging area."""
    try:
        # Add Python files
        subprocess.run(["git", "add", "*.py"], check=False, capture_output=True, text=True, timeout=30)

        # Add other important files
        important_files = ["main.py", "README.md", ".gitignore"]
        for file in important_files:
            if os.path.exists(file):
                subprocess.run(["git", "add", file], check=False, timeout=10)

        # Get status to count added files
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "--cached"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        files_added = len([line for line in status_result.stdout.strip().split("\n") if line.strip()])

        return {"success": True, "files_added": files_added}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _git_add_all() -> dict[str, Any]:
    """Add all files to Git staging area."""
    try:
        result = subprocess.run(["git", "add", "."], check=False, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"success": False, "error": "Failed to add files to Git"}

        # Get count of staged files
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "--cached"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        files_added = len([line for line in status_result.stdout.strip().split("\n") if line.strip()])

        return {"success": True, "files_added": files_added}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _git_commit(message: str) -> dict[str, Any]:
    """Commit staged changes with the provided message."""
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message], check=False, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            # Check if there are no changes to commit
            if "nothing to commit" in result.stdout.lower():
                return {
                    "success": True,
                    "message": "No changes to commit",
                    "commit_hash": None,
                }
            return {
                "success": False,
                "error": f"Commit failed: {result.stderr or result.stdout}",
            }

        # Extract commit hash with comprehensive error handling
        commit_hash = None
        try:
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"], check=False, capture_output=True, text=True, timeout=10
            )
            if hash_result.returncode == 0:
                commit_hash = hash_result.stdout.strip()[:8]  # Short hash
                logger.debug(f"📋 Extracted commit hash: {commit_hash}")
            else:
                logger.warning(f"⚠️ Failed to extract commit hash: {hash_result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("⏰ Timeout while extracting commit hash")
        except subprocess.CalledProcessError as e:
            logger.warning(f"🚫 Git command failed while extracting hash: {e}")
        except FileNotFoundError:
            logger.warning("🔍 Git command not found in PATH")
        except Exception as e:
            logger.warning(f"❌ Unexpected error extracting commit hash: {e}")

        return {"success": True, "commit_hash": commit_hash, "output": result.stdout}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _git_push() -> dict[str, Any]:
    """Push commits to remote repository."""
    try:
        # Check if remote exists
        result = subprocess.run(["git", "remote"], check=False, capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not result.stdout.strip():
            return {"success": False, "error": "No remote repository configured"}

        # Get current branch name
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if current_branch_result.returncode != 0:
            return {"success": False, "error": "Failed to get current branch name"}

        current_branch = current_branch_result.stdout.strip()
        if not current_branch:
            return {"success": False, "error": "No current branch detected"}

        # Try to push current branch
        result = subprocess.run(
            ["git", "push", "origin", current_branch],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {
                "success": False,
                "error": f"Push failed: {result.stderr or result.stdout}",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _generate_commit_message(fixes_applied: dict[str, Any]) -> str:
    """Generate detailed commit message based on fixes applied."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not fixes_applied or not fixes_applied.get("fixes_applied"):
        return f"DevSkyy Enhanced Platform Update - {timestamp}\n\nGeneral improvements and optimizations"

    fixes = fixes_applied.get("fixes_applied", [])

    # Count fix types
    errors_fixed = sum(1 for fix in fixes if fix.get("type") == "error")
    warnings_fixed = sum(1 for fix in fixes if fix.get("type") == "warning")
    optimizations = sum(1 for fix in fixes if fix.get("type") == "optimization")

    # Build commit message
    title = f"DevSkyy Enhanced Platform Auto-Fix - {timestamp}"

    summary = []
    if errors_fixed:
        summary.append(f"Fixed {errors_fixed} error(s)")
    if warnings_fixed:
        summary.append(f"Resolved {warnings_fixed} warning(s)")
    if optimizations:
        summary.append(f"Applied {optimizations} optimization(s)")

    message_parts = [title, ""]

    if summary:
        message_parts.append("Summary:")
        message_parts.extend(f"- {item}" for item in summary)
        message_parts.append("")

    # Add detailed fixes
    if len(fixes) <= 10:  # Only add details for reasonable number of fixes
        message_parts.append("Details:")
        for fix in fixes[:10]:  # Limit to first 10 fixes
            file_name = fix.get("file", "unknown").split("/")[-1]  # Get just filename
            description = fix.get("description", "Unknown fix")
            message_parts.append(f"- {file_name}: {description}")

        if len(fixes) > 10:
            message_parts.append(f"- ... and {len(fixes) - 10} more fixes")

    message_parts.extend(["", "Auto-generated by DevSkyy Enhanced Platform"])

    return "\n".join(message_parts)
