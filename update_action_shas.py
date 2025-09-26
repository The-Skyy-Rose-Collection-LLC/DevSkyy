#!/usr/bin/env python3
"""
GitHub Actions SHA Updater - Enhanced Security Compliance Script

This script automatically updates GitHub Action version tags to their corresponding
commit SHAs for enhanced security compliance. It provides comprehensive coverage
of all actions used in workflows with safety features like backup and rollback.

Author: DevSkyy Platform Team
License: MIT
"""

import json
import logging
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("sha_update.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class ActionSHAUpdater:
    """Enhanced GitHub Actions SHA updater with comprehensive security features."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the updater with optional configuration."""
        self.workflows_dir = Path(".github/workflows")
        self.backup_dir = Path(".github/workflows_backup")
        self.config = self._load_config(config_file)
        self.github_token = self._get_github_token()
        self.updated_actions = {}
        self.failed_updates = []

    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            "actions_to_update": {
                # Core GitHub Actions
                "actions/checkout": {"versions": ["v4"], "priority": "high"},
                "actions/setup-python": {"versions": ["v4", "v5"], "priority": "high"},
                "actions/setup-node": {"versions": ["v5"], "priority": "high"},
                "actions/github-script": {"versions": ["v6"], "priority": "medium"},
                "actions/upload-artifact": {"versions": ["v4"], "priority": "medium"},
                "actions/stale": {"versions": ["v5"], "priority": "low"},
                # Pages Actions
                "actions/configure-pages": {"versions": ["v5"], "priority": "medium"},
                "actions/deploy-pages": {"versions": ["v4"], "priority": "medium"},
                "actions/jekyll-build-pages": {"versions": ["v1"], "priority": "medium"},
                "actions/upload-pages-artifact": {"versions": ["v3"], "priority": "medium"},
                # Security Actions
                "github/codeql-action/init": {"versions": ["v3"], "priority": "high"},
                "github/codeql-action/analyze": {"versions": ["v3"], "priority": "high"},
                # Third-party Actions
                "codecov/codecov-action": {"versions": ["v3"], "priority": "medium"},
                "docker/build-push-action": {"versions": ["v5"], "priority": "medium"},
                "docker/login-action": {"versions": ["v3"], "priority": "medium"},
                "docker/setup-buildx-action": {"versions": ["v3"], "priority": "medium"},
            },
            "backup_enabled": True,
            "dry_run": False,
            "rate_limit_delay": 1.0,
            "max_retries": 3,
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
                logger.info("Using default configuration")

        return default_config

    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment for API rate limiting."""
        import os

        return os.getenv("GITHUB_TOKEN")

    def _make_github_request(self, url: str) -> Optional[Dict]:
        """Make authenticated GitHub API request with retry logic."""
        headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        for attempt in range(self.config["max_retries"]):
            try:
                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    return None
                elif response.status_code == 403:
                    logger.error("GitHub API rate limit exceeded. Please provide GITHUB_TOKEN.")
                    return None
                else:
                    logger.warning(f"API request failed with status {response.status_code}: {url}")

            except requests.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")

            if attempt < self.config["max_retries"] - 1:
                import time

                time.sleep(self.config["rate_limit_delay"] * (attempt + 1))

        return None

    def get_latest_sha(self, owner: str, repo: str, tag: str) -> Optional[str]:
        """Get the commit SHA for a specific tag with enhanced error handling."""
        logger.debug(f"Fetching SHA for {owner}/{repo}@{tag}")

        # Try getting tag reference first
        url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag}"
        data = self._make_github_request(url)

        if not data:
            return None

        try:
            sha = data["object"]["sha"]

            # If it's a tag object, get the actual commit SHA
            if data["object"]["type"] == "tag":
                tag_url = data["object"]["url"]
                tag_data = self._make_github_request(tag_url)
                if tag_data:
                    sha = tag_data["object"]["sha"]

            logger.debug(f"Found SHA {sha} for {owner}/{repo}@{tag}")
            return sha

        except KeyError as e:
            logger.error(f"Unexpected API response structure for {owner}/{repo}@{tag}: {e}")
            return None

    def _create_backup(self) -> bool:
        """Create backup of workflow files."""
        if not self.config["backup_enabled"]:
            return True

        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)

            shutil.copytree(self.workflows_dir, self.backup_dir)
            logger.info(f"Created backup at {self.backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def _restore_backup(self) -> bool:
        """Restore workflow files from backup."""
        if not self.backup_dir.exists():
            logger.error("No backup found to restore")
            return False

        try:
            # Remove current workflows
            if self.workflows_dir.exists():
                shutil.rmtree(self.workflows_dir)

            # Restore from backup
            shutil.copytree(self.backup_dir, self.workflows_dir)
            logger.info("Successfully restored from backup")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def _detect_actions_in_file(self, file_path: Path) -> Set[str]:
        """Detect all GitHub Actions used in a workflow file."""
        actions = set()

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Find all 'uses:' statements
            uses_pattern = r"uses:\s*([^\s@]+)(@[^\s]+)?"
            matches = re.findall(uses_pattern, content, re.MULTILINE)

            for match in matches:
                action_name = match[0]
                if action_name.startswith("./") or action_name.startswith(".\\"):
                    continue  # Skip local actions
                actions.add(action_name)

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")

        return actions

    def _update_workflow_content(self, content: str, action_updates: Dict[str, str]) -> str:
        """Update workflow content with new SHAs."""
        updated_content = content

        for action_with_version, new_sha in action_updates.items():
            # Create patterns to match the action with any version
            action_name = action_with_version.split("@")[0]

            # Pattern to match: action@version -> action@sha
            patterns = [
                rf"{re.escape(action_name)}@v\d+(\.\d+)*(-[\w\d]+)?",
                rf"{re.escape(action_name)}@\d+(\.\d+)*(-[\w\d]+)?",
                rf"{re.escape(action_name)}@[a-f0-9]{{40}}",  # Already a SHA
            ]

            for pattern in patterns:
                replacement = f"{action_name}@{new_sha}"
                old_content = updated_content
                updated_content = re.sub(pattern, replacement, updated_content)

                if old_content != updated_content:
                    logger.debug(f"Updated {action_name} to SHA {new_sha}")
                    break  # Stop after first successful replacement

        return updated_content

    def update_workflow_files(self) -> bool:
        """Update all workflow files with latest SHAs."""
        logger.info("Starting GitHub Actions SHA update process")

        # Create backup
        if not self._create_backup():
            logger.error("Backup creation failed. Aborting update.")
            return False

        try:
            # Discover all actions in use
            all_detected_actions = set()
            workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))

            for workflow_file in workflow_files:
                detected_actions = self._detect_actions_in_file(workflow_file)
                all_detected_actions.update(detected_actions)
                logger.info(f"Found {len(detected_actions)} actions in {workflow_file.name}")

            logger.info(f"Total unique actions detected: {len(all_detected_actions)}")

            # Get SHAs for all configured actions
            action_updates = {}

            for action_name, action_config in self.config["actions_to_update"].items():
                if action_name not in all_detected_actions:
                    logger.debug(f"Action {action_name} not found in workflows, skipping")
                    continue

                # Parse action owner/repo
                if "/" not in action_name:
                    logger.warning(f"Invalid action format: {action_name}")
                    continue

                parts = action_name.split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], "/".join(parts[1:])  # Handle nested paths like github/codeql-action/init
                else:
                    continue

                # Try each configured version
                sha_found = False
                for version in action_config["versions"]:
                    sha = self.get_latest_sha(owner, repo, version)
                    if sha:
                        action_with_version = f"{action_name}@{version}"
                        action_updates[action_with_version] = sha
                        self.updated_actions[action_with_version] = sha
                        logger.info(f"✅ {action_with_version} -> {sha}")
                        sha_found = True
                        break

                if not sha_found:
                    self.failed_updates.append(action_name)
                    logger.warning(f"❌ Failed to get SHA for {action_name}")

            # Update workflow files
            if not action_updates:
                logger.info("No actions to update")
                return True

            files_updated = 0
            for workflow_file in workflow_files:
                try:
                    original_content = workflow_file.read_text()
                    updated_content = self._update_workflow_content(original_content, action_updates)

                    if original_content != updated_content:
                        if not self.config["dry_run"]:
                            workflow_file.write_text(updated_content)
                            files_updated += 1
                            logger.info(f"Updated {workflow_file.name}")
                        else:
                            logger.info(f"[DRY RUN] Would update {workflow_file.name}")

                except Exception as e:
                    logger.error(f"Failed to update {workflow_file}: {e}")

            # Summary
            logger.info("=" * 60)
            logger.info("SHA UPDATE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Files processed: {len(workflow_files)}")
            logger.info(f"Files updated: {files_updated}")
            logger.info(f"Actions updated: {len(self.updated_actions)}")
            logger.info(f"Failed updates: {len(self.failed_updates)}")

            if self.updated_actions:
                logger.info("\nSuccessfully updated actions:")
                for action, sha in self.updated_actions.items():
                    logger.info(f"  ✅ {action} -> {sha[:8]}...")

            if self.failed_updates:
                logger.warning("\nFailed to update:")
                for action in self.failed_updates:
                    logger.warning(f"  ❌ {action}")

            return len(self.failed_updates) == 0

        except Exception as e:
            logger.error(f"Update process failed: {e}")
            if not self.config["dry_run"]:
                logger.info("Attempting to restore from backup...")
                self._restore_backup()
            return False

    def generate_report(self) -> Dict:
        """Generate a detailed report of the update process."""
        return {
            "timestamp": datetime.now().isoformat(),
            "config": self.config,
            "updated_actions": self.updated_actions,
            "failed_updates": self.failed_updates,
            "summary": {
                "total_updated": len(self.updated_actions),
                "total_failed": len(self.failed_updates),
                "success_rate": (
                    len(self.updated_actions) / (len(self.updated_actions) + len(self.failed_updates)) * 100
                    if (self.updated_actions or self.failed_updates)
                    else 100
                ),
            },
        }


def main():
    """Main execution function with CLI support."""
    import argparse

    parser = argparse.ArgumentParser(description="Update GitHub Actions to use commit SHAs for security compliance")
    parser.add_argument("--config", "-c", help="Configuration file path (JSON format)")
    parser.add_argument(
        "--dry-run", "-d", action="store_true", help="Show what would be updated without making changes"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--report", "-r", help="Generate JSON report to specified file")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize updater
    updater = ActionSHAUpdater(args.config)

    if args.dry_run:
        updater.config["dry_run"] = True
        logger.info("DRY RUN MODE: No files will be modified")

    # Perform update
    success = updater.update_workflow_files()

    # Generate report
    if args.report:
        report = updater.generate_report()
        try:
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {args.report}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
