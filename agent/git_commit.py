
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def commit_fixes(fixed_code: Dict[str, Any]) -> Dict[str, Any]:
    """Commit fixes to git repository."""
    try:
        # Add all changes
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # Create commit message
        commit_message = f"DevSkyy Auto-Fix: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if isinstance(fixed_code, dict) and "fixes_applied" in fixed_code:
            fixes = fixed_code["fixes_applied"]
            if fixes:
                commit_message += f" - Applied: {', '.join(fixes)}"
        
        # Commit changes
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info(f"✅ Successfully committed fixes: {commit_message}")
        return {
            "status": "success",
            "commit_message": commit_message,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️ Git commit failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error during commit: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def commit_all_changes() -> Dict[str, Any]:
    """Commit all current changes to git repository."""
    try:
        # Check if there are changes to commit
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        )
        
        if not status_result.stdout.strip():
            return {
                "status": "no_changes",
                "message": "No changes to commit",
                "timestamp": datetime.now().isoformat()
            }
        
        # Add all changes
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # Create commit message
        commit_message = f"DevSkyy Platform Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Commit changes
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Try to push to origin
        try:
            push_result = subprocess.run(
                ["git", "push", "origin", "main"],
                check=True,
                capture_output=True,
                text=True
            )
            push_status = "success"
        except subprocess.CalledProcessError as push_error:
            logger.warning(f"⚠️ Git push failed: {push_error}")
            push_status = "push_failed"
        
        logger.info(f"✅ Successfully committed all changes: {commit_message}")
        return {
            "status": "success",
            "commit_message": commit_message,
            "push_status": push_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️ Git operation failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error during commit: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
