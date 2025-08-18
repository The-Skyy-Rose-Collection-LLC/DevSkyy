
import subprocess
import os
from datetime import datetime
from typing import Dict, Any

def commit_fixes(fixed_code: Dict[str, Any]) -> Dict[str, Any]:
    """Commit fixes to git repository."""
    try:
        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True, cwd='.')
        
        # Create commit message
        commit_message = f"DevSkyy fixes applied: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if 'fixes_applied' in fixed_code:
            commit_message += f" - {', '.join(fixed_code['fixes_applied'])}"
        
        # Commit changes
        result = subprocess.run(['git', 'commit', '-m', commit_message], 
                              capture_output=True, text=True, cwd='.')
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "commit_message": commit_message,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "failed",
            "error": str(e),
            "output": getattr(e, 'output', '')
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def commit_all_changes() -> Dict[str, Any]:
    """Commit all current changes to git."""
    try:
        # Check if there are changes
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                     capture_output=True, text=True, cwd='.')
        
        if not status_result.stdout.strip():
            return {
                "status": "no_changes",
                "message": "No changes to commit"
            }
        
        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True, cwd='.')
        
        # Commit with timestamp
        commit_message = f"DevSkyy automated commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        commit_result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                     capture_output=True, text=True, cwd='.')
        
        # Push to origin
        push_result = subprocess.run(['git', 'push', 'origin', 'main'], 
                                   capture_output=True, text=True, cwd='.')
        
        return {
            "status": "success",
            "commit_message": commit_message,
            "commit_output": commit_result.stdout,
            "push_output": push_result.stdout,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "failed",
            "error": str(e),
            "output": getattr(e, 'output', '')
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

def get_git_status() -> Dict[str, Any]:
    """Get current git repository status."""
    try:
        # Get status
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                     capture_output=True, text=True, cwd='.')
        
        # Get log
        log_result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                  capture_output=True, text=True, cwd='.')
        
        return {
            "status": "success",
            "changes": status_result.stdout.strip().split('\n') if status_result.stdout.strip() else [],
            "recent_commits": log_result.stdout.strip().split('\n') if log_result.stdout.strip() else [],
            "has_changes": bool(status_result.stdout.strip())
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
