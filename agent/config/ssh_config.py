
"""SSH configuration for DevSkyy automated operations."""

import os
from typing import Dict, Any

class SSHConfig:
    """Manage SSH configuration for automated Git operations."""
    
    def __init__(self):
        self.ssh_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILxlL+avzP/mDnUbjYchtc4A3d1uosaYu9jme7YvfQYK"
        self.ssh_key_path = os.path.expanduser("~/.ssh/devskyy_key")
        
    def setup_ssh_key(self) -> Dict[str, Any]:
        """Set up SSH key for Git operations."""
        try:
            # Create .ssh directory if it doesn't exist
            ssh_dir = os.path.expanduser("~/.ssh")
            os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
            
            # Write SSH key to file
            with open(self.ssh_key_path, 'w') as f:
                f.write(self.ssh_key + "\n")
            
            # Set proper permissions
            os.chmod(self.ssh_key_path, 0o600)
            
            return {
                "status": "success",
                "ssh_key_path": self.ssh_key_path,
                "message": "SSH key configured successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to configure SSH key"
            }
    
    def get_git_ssh_command(self) -> str:
        """Get Git SSH command with custom key."""
        return f"ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no"

# Initialize SSH configuration
ssh_config = SSHConfig()
