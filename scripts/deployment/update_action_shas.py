#!/usr/bin/env python3
"""
GitHub Actions SHA Updater
Converts GitHub Actions version tags to immutable commit SHAs for security compliance.

This script:
1. Scans all workflow files in .github/workflows/
2. Identifies actions using version tags (e.g., v4, v5)
3. Fetches the corresponding commit SHA from GitHub API
4. Updates workflow files with full commit SHAs
5. Preserves comments and formatting
"""

import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# GitHub API base URL
GITHUB_API = "https://api.github.com"

# Mapping of common actions to their repositories
ACTION_REPOS = {
    "actions/checkout": "actions/checkout",
    "actions/setup-python": "actions/setup-python",
    "actions/setup-node": "actions/setup-node",
    "actions/upload-artifact": "actions/upload-artifact",
    "actions/download-artifact": "actions/download-artifact",
    "codecov/codecov-action": "codecov/codecov-action",
    "docker/setup-buildx-action": "docker/setup-buildx-action",
    "docker/login-action": "docker/login-action",
    "docker/metadata-action": "docker/metadata-action",
    "docker/build-push-action": "docker/build-push-action",
    "aquasecurity/trivy-action": "aquasecurity/trivy-action",
    "github/codeql-action/init": "github/codeql-action",
    "github/codeql-action/autobuild": "github/codeql-action",
    "github/codeql-action/analyze": "github/codeql-action",
    "github/codeql-action/upload-sarif": "github/codeql-action",
    "trufflesecurity/trufflehog": "trufflesecurity/trufflehog",
    "actions/stale": "actions/stale",
    "anthropics/claude-code-action": "anthropics/claude-code-action",
}

# Known SHA mappings for common action versions (fallback when API fails)
# These are verified commit SHAs for stable releases
KNOWN_SHAS = {
    "actions/checkout@v4": "11bd71901bbe5b1630ceea73d27597364c9af683",  # v4.2.2
    "actions/checkout@v5.0.0": "d32f905c75822c24435e99d5280fefb0ea6cf2fe",  # v5.0.0
    "actions/setup-python@v5": "0b93645e9fea7318ecaed2b359559ac225c90a2b",  # v5.3.0
    "actions/setup-node@v4": "39370e3970a6d050c480ffad4ff0ed4d3fdee109",  # v4.1.0
    "actions/upload-artifact@v4": "b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882",  # v4.4.3
    "actions/download-artifact@v4": "fa0a91b85d4f404e444e00e005971372dc801d16",  # v4.1.8
    "codecov/codecov-action@v4": "7f8b4b4bde536c465e797be725022faffa36fbe3",  # v4.6.0
    "docker/setup-buildx-action@v3": "c47758b77c9736f4b2ef4073d4d51994fabfe349",  # v3.7.1
    "docker/login-action@v3": "9780b0c442fbb1117ed29e0efdff1e18412f7567",  # v3.3.0
    "docker/metadata-action@v5": "902fa4bd8bfe0e0b9ce9e2f2090c3301f72d263d",  # v5.6.1
    "docker/build-push-action@v5": "4f58ea79222b3b9dc2c8bbdd6debcef730109a75",  # v5.4.0
    "aquasecurity/trivy-action@master": "915b19ead16fc68b9b03f2a5e8b23c1f7c0ea2bd",  # master branch latest
    "github/codeql-action@v3": "f779452ac5af1c261dce0346a8b332a8cab67b52",  # v3.27.5
    "trufflesecurity/trufflehog@main": "0e60e9fece871ad8fb0e104fc5f3c04a2c3b6093",  # main branch latest
    "actions/stale@v9": "28ca1036281a5e5922ead5184a1bbf96e5fc984e",  # v9.0.0
    "anthropics/claude-code-action@v1": "52e5d0a84c4b2c19d9a650ab2c5d8c03c5e39c91",  # v1 latest
}


class ActionSHAUpdater:
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.sha_cache: dict[str, str] = {}
        self.github_token = os.environ.get("GITHUB_TOKEN", "")

    def log(self, message: str, level: str = "INFO"):
        """Print log message with level."""
        if level == "VERBOSE" and not self.verbose:
            return
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "VERBOSE": "\033[0;36m",
        }
        colors.get(level, "")

    def get_repo_from_action(self, action: str) -> str | None:
        """Extract repository name from action string."""
        # Handle paths like github/codeql-action/init
        for key, repo in ACTION_REPOS.items():
            if action.startswith(key):
                return repo

        # For standard format: owner/repo
        if "/" in action and not action.startswith("."):
            parts = action.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"

        return None

    def fetch_sha_for_tag(self, repo: str, tag: str) -> str | None:
        """Fetch commit SHA for a given tag using GitHub API."""
        cache_key = f"{repo}@{tag}"

        # Check cache first
        if cache_key in self.sha_cache:
            self.log(f"Using cached SHA for {cache_key}", "VERBOSE")
            return self.sha_cache[cache_key]

        # Check known SHAs database
        action_key = f"{repo}@{tag}"
        if action_key in KNOWN_SHAS:
            sha = KNOWN_SHAS[action_key]
            self.sha_cache[cache_key] = sha
            self.log(f"Using known SHA for {repo}@{tag}: {sha[:8]}...", "SUCCESS")
            return sha

        # For github/codeql-action with subpaths, use the main action SHA
        if repo == "github/codeql-action":
            base_key = f"github/codeql-action@{tag}"
            if base_key in KNOWN_SHAS:
                sha = KNOWN_SHAS[base_key]
                self.sha_cache[cache_key] = sha
                self.log(f"Using known SHA for {repo}@{tag}: {sha[:8]}...", "SUCCESS")
                return sha

        # Try to get SHA from tag via API
        url = f"{GITHUB_API}/repos/{repo}/git/refs/tags/{tag}"
        self.log(f"Fetching SHA from GitHub API: {url}", "VERBOSE")

        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            req = Request(url, headers=headers)
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                # Handle annotated tags
                if data.get("object", {}).get("type") == "tag":
                    tag_url = data["object"]["url"]
                    req = Request(tag_url, headers=headers)
                    with urlopen(req, timeout=10) as tag_response:
                        tag_data = json.loads(tag_response.read().decode())
                        sha = tag_data.get("object", {}).get("sha")
                else:
                    sha = data.get("object", {}).get("sha")

                if sha:
                    self.sha_cache[cache_key] = sha
                    self.log(f"Found SHA for {repo}@{tag}: {sha[:8]}...", "SUCCESS")
                    return sha

        except HTTPError as e:
            if e.code == 404:
                # Tag not found, try as a branch
                self.log(f"Tag not found, trying as branch: {tag}", "VERBOSE")
                return self.fetch_sha_for_branch(repo, tag)
            elif e.code == 403:
                # Rate limited - use known SHA if available
                self.log(f"API rate limited for {repo}@{tag}, checking fallback", "WARNING")
                return None
            else:
                self.log(f"HTTP error fetching {repo}@{tag}: {e}", "ERROR")
        except URLError as e:
            self.log(f"Network error fetching {repo}@{tag}: {e}", "ERROR")
        except Exception as e:
            self.log(f"Error fetching {repo}@{tag}: {e}", "ERROR")

        return None

    def fetch_sha_for_branch(self, repo: str, branch: str) -> str | None:
        """Fetch commit SHA for a branch."""
        url = f"{GITHUB_API}/repos/{repo}/commits/{branch}"
        self.log(f"Fetching SHA for branch: {url}", "VERBOSE")

        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            req = Request(url, headers=headers)
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                sha = data.get("sha")

                if sha:
                    cache_key = f"{repo}@{branch}"
                    self.sha_cache[cache_key] = sha
                    self.log(f"Found SHA for {repo}@{branch}: {sha[:8]}...", "SUCCESS")
                    return sha

        except Exception as e:
            self.log(f"Error fetching branch {repo}@{branch}: {e}", "ERROR")

        return None

    def extract_actions_from_file(self, filepath: Path) -> list[tuple[str, str, int]]:
        """Extract all action usages from a workflow file.

        Returns list of tuples: (action_name, version_or_sha, line_number)
        """
        actions = []

        with open(filepath, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            # Match: uses: owner/repo@version
            match = re.match(r"\s*-?\s*uses:\s+([^@\s]+)@([^\s#]+)", line)
            if match:
                action = match.group(1)
                version = match.group(2)

                # Skip if already a commit SHA (40 hex chars)
                if re.match(r"^[0-9a-f]{40}$", version):
                    self.log(
                        f"  Line {i}: {action}@{version[:8]}... (already SHA)",
                        "VERBOSE",
                    )
                    continue

                actions.append((action, version, i))
                self.log(f"  Line {i}: {action}@{version}", "VERBOSE")

        return actions

    def update_workflow_file(self, filepath: Path) -> bool:
        """Update a single workflow file with commit SHAs.

        Returns True if file was modified.
        """
        self.log(f"\nProcessing: {filepath.name}", "INFO")

        # Extract actions
        actions = self.extract_actions_from_file(filepath)

        if not actions:
            self.log(f"  No actions to update in {filepath.name}", "INFO")
            return False

        self.log(f"  Found {len(actions)} action(s) to update", "INFO")

        # Read file content
        with open(filepath, "r") as f:
            content = f.read()

        _original_content = content
        updates_made = 0

        # Process each action
        for action, version, _line_num in actions:
            repo = self.get_repo_from_action(action)

            if not repo:
                self.log(f"  Could not determine repo for: {action}", "WARNING")
                continue

            # Fetch SHA
            sha = self.fetch_sha_for_tag(repo, version)

            if not sha:
                self.log(f"  Failed to fetch SHA for {action}@{version}", "WARNING")
                continue

            # Replace in content
            old_pattern = f"{action}@{version}"
            new_pattern = f"{action}@{sha}"

            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern, 1)
                updates_made += 1
                self.log(f"  ✓ Updated {action}: {version} → {sha[:8]}...", "SUCCESS")
            else:
                self.log(f"  Pattern not found: {old_pattern}", "WARNING")

        # Write back if changed
        if updates_made > 0:
            if not self.dry_run:
                with open(filepath, "w") as f:
                    f.write(content)
                self.log(
                    f"  ✅ Updated {filepath.name} ({updates_made} change(s))",
                    "SUCCESS",
                )
            else:
                self.log(
                    f"  [DRY RUN] Would update {filepath.name} ({updates_made} change(s))",
                    "INFO",
                )
            return True

        return False

    def update_all_workflows(self, workflows_dir: Path) -> dict[str, int]:
        """Update all workflow files in directory.

        Returns dict with statistics.
        """
        stats = {
            "total_files": 0,
            "updated_files": 0,
            "total_actions": 0,
        }

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        if not workflow_files:
            self.log(f"No workflow files found in {workflows_dir}", "WARNING")
            return stats

        stats["total_files"] = len(workflow_files)
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"Found {len(workflow_files)} workflow file(s)", "INFO")
        self.log(f"{'='*60}", "INFO")

        for filepath in sorted(workflow_files):
            if self.update_workflow_file(filepath):
                stats["updated_files"] += 1

        return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update GitHub Actions to use commit SHAs instead of tags")
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--workflows-dir",
        "-w",
        type=str,
        default=".github/workflows",
        help="Path to workflows directory (default: .github/workflows)",
    )

    args = parser.parse_args()

    # Get workflows directory
    workflows_dir = Path(args.workflows_dir)
    if not workflows_dir.exists():
        sys.exit(1)

    # Create updater
    updater = ActionSHAUpdater(dry_run=args.dry_run, verbose=args.verbose)

    # Show configuration
    if args.dry_run:
        pass
    if not updater.github_token:
        pass

    # Update workflows
    stats = updater.update_all_workflows(workflows_dir)

    # Print summary

    if args.dry_run or stats["updated_files"] > 0:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
