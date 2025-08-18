from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def commit_fixes(content: str, filename: str = "fixed_code.txt") -> None:
    """Write ``content`` to ``filename`` and commit it to git.

    The function stages the file and creates a commit with a timestamped
    message. It assumes the current working directory is a Git repository.
    """
    path = Path(filename)
    path.write_text(content, encoding="utf-8")

    subprocess.run(["git", "add", str(path)], check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"chore: automated fix ({datetime.utcnow().isoformat(timespec='seconds')})",
        ],
        check=True,
    )
    
    # Push changes to GitHub
    try:
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Changes pushed to GitHub successfully")
    except subprocess.CalledProcessError:
        try:
            subprocess.run(["git", "push", "origin", "master"], check=True)
            print("✅ Changes pushed to GitHub successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to push to GitHub - please check your remote configuration")


def commit_all_changes() -> None:
    """Commit all current changes to git and push to GitHub."""
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"feat: DevSkyy agents update ({datetime.utcnow().isoformat(timespec='seconds')})",
            ],
            check=True,
        )
        
        # Push changes to GitHub
        try:
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ All changes pushed to GitHub successfully")
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["git", "push", "origin", "master"], check=True)
                print("✅ All changes pushed to GitHub successfully")
            except subprocess.CalledProcessError:
                print("❌ Failed to push to GitHub - please check your remote configuration")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
