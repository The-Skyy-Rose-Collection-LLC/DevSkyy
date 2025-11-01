from pathlib import Path
import os

from typing import Any, Dict
import logging
import subprocess

logger = logging.getLogger(__name__)


def setup_ssh_config() -> Dict[str, Any]:
    """
    Set up SSH configuration for secure repository access.
    Production-level SSH key management.
    """
    try:
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)

        config_path = ssh_dir / "config"
        known_hosts_path = ssh_dir / "known_hosts"

        # Create SSH config if it doesn't exist
        if not config_path.exists():
            ssh_config = """
# DevSkyy Enhanced Platform SSH Configuration
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking yes

Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    """

            with open(config_path, "w") as f:
                f.write(ssh_config.strip())

            os.chmod(config_path, 0o600)
            logger.info("✅ SSH config created")

        # Add GitHub to known hosts if not present
        if not known_hosts_path.exists() or "github.com" not in known_hosts_path.read_text():
            try:
                result = subprocess.run(
                    ["ssh-keyscan", "-H", "github.com"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    with open(known_hosts_path, "a") as f:
                        f.write(result.stdout)
                    os.chmod(known_hosts_path, 0o600)
                    logger.info("✅ GitHub added to known hosts")

            except subprocess.TimeoutExpired:
                logger.warning("⚠️ SSH keyscan timeout")
            except Exception as e:
                logger.warning(f"⚠️ Failed to add GitHub to known hosts: {str(e)}")

        # Check if SSH key exists
        key_path = ssh_dir / "id_rsa"
        if not key_path.exists():
            logger.info(
                "ℹ️ SSH key not found. Generate one with: " "ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
            )

        return {
            "status": "configured",
            "ssh_dir": str(ssh_dir),
            "config_exists": config_path.exists(),
            "key_exists": key_path.exists(),
            "known_hosts_configured": known_hosts_path.exists(),
        }

    except Exception as e:
        logger.error(f"❌ SSH configuration failed: {str(e)}")
        return {"status": "failed", "error": str(e)}
