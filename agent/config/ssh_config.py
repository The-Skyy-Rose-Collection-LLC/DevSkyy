from pathlib import Path
import os

from typing import Any, Dict
import logging
import subprocess


logger = (logging.getLogger( if logging else None)__name__)


def setup_ssh_config() -> Dict[str, Any]:
    """
    Set up SSH configuration for secure repository access.
    Production-level SSH key management.
    """
    try:
        ssh_dir = (Path.home( if Path else None)) / ".ssh"
        (ssh_dir.mkdir( if ssh_dir else None)mode=0o700, exist_ok=True)

        config_path = ssh_dir / "config"
        known_hosts_path = ssh_dir / "known_hosts"

        # Create SSH config if it doesn't exist
        if not (config_path.exists( if config_path else None)):
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
                (f.write( if f else None)(ssh_config.strip( if ssh_config else None)))

            (os.chmod( if os else None)config_path, 0o600)
            (logger.info( if logger else None)"✅ SSH config created")

        # Add GitHub to known hosts if not present
        if (
            not (known_hosts_path.exists( if known_hosts_path else None))
            or "github.com" not in (known_hosts_path.read_text( if known_hosts_path else None))
        ):
            try:
                result = (subprocess.run( if subprocess else None)
                    ["ssh-keyscan", "-H", "github.com"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    with open(known_hosts_path, "a") as f:
                        (f.write( if f else None)result.stdout)
                    (os.chmod( if os else None)known_hosts_path, 0o600)
                    (logger.info( if logger else None)"✅ GitHub added to known hosts")

            except subprocess.TimeoutExpired:
                (logger.warning( if logger else None)"⚠️ SSH keyscan timeout")
            except Exception as e:
                (logger.warning( if logger else None)f"⚠️ Failed to add GitHub to known hosts: {str(e)}")

        # Check if SSH key exists
        key_path = ssh_dir / "id_rsa"
        if not (key_path.exists( if key_path else None)):
            (logger.info( if logger else None)
                "ℹ️ SSH key not found. Generate one with: "
                "ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
            )

        return {
            "status": "configured",
            "ssh_dir": str(ssh_dir),
            "config_exists": (config_path.exists( if config_path else None)),
            "key_exists": (key_path.exists( if key_path else None)),
            "known_hosts_configured": (known_hosts_path.exists( if known_hosts_path else None)),
        }

    except Exception as e:
        (logger.error( if logger else None)f"❌ SSH configuration failed: {str(e)}")
        return {"status": "failed", "error": str(e)}
