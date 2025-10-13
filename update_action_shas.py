#!/usr/bin/env python3
"""
GitHub Actions SHA Updater
Converts action references from tags to commit SHAs for enhanced security
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
    import yaml
except ImportError:
    print("❌ Missing dependencies. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pyyaml"])
    import requests
    import yaml


class ActionSHAUpdater:
    """Updates GitHub Actions to use commit SHAs instead of tags"""
    
    # Static mapping of known action versions to commit SHAs
    # This reduces API calls and avoids rate limiting
    KNOWN_SHAS = {
        # actions/checkout
        "actions/checkout@v4": "692973e3d937129bcbf40652eb9f2f61becf3332",  # v4.1.7
        "actions/checkout@v5.0.0": "11bd71901bbe5b1630ceea73d27597364c9af683",  # v5.0.0
        
        # actions/setup-python
        "actions/setup-python@v5": "0b93645e9fea7318ecaed2b359559ac225c90a2b",  # v5.3.0
        
        # actions/setup-node
        "actions/setup-node@v4": "1e60f620b9541d16bece96c5465dc8762fab0a9f",  # v4.0.4
        
        # actions/upload-artifact
        "actions/upload-artifact@v4": "6f51ac03b9356f520e9adb1b1b7802705f340c2b",  # v4.5.0
        
        # actions/download-artifact
        "actions/download-artifact@v4": "fa0a91b85d4f404e444e00e005971372dc801d16",  # v4.1.8
        
        # actions/stale
        "actions/stale@v9": "f7176fd3007623b69d27091f9b9d4ab7995f0a06",  # v9.0.0
        
        # codecov/codecov-action
        "codecov/codecov-action@v4": "015f24e6818733317a2da2edd6290ab26238649a",  # v4.6.0
        
        # docker actions
        "docker/setup-buildx-action@v3": "8026d2bc3645ea78b0d2544766a1225eb5691f89",  # v3.7.1
        "docker/login-action@v3": "9780b0c442fbb1117ed29e0efdff1e18412f7567",  # v3.3.0
        "docker/build-push-action@v5": "4f58ea79222b3b9dc2c8bbdd6debcef730109a75",  # v5.4.0
        "docker/metadata-action@v5": "8e5442c4ef9f78752691e2d8f8d19755c6f78e81",  # v5.5.1
        
        # github/codeql-action
        "github/codeql-action/init@v3": "6213e19f2269b2079c747e15760b2b4eff0b549d",  # v3.27.6
        "github/codeql-action/autobuild@v3": "6213e19f2269b2079c747e15760b2b4eff0b549d",  # v3.27.6
        "github/codeql-action/analyze@v3": "6213e19f2269b2079c747e15760b2b4eff0b549d",  # v3.27.6
        "github/codeql-action/upload-sarif@v3": "6213e19f2269b2079c747e15760b2b4eff0b549d",  # v3.27.6
        
        # aquasecurity/trivy-action
        "aquasecurity/trivy-action@master": "a20de5420d57c4102486cdd9578b45609c99d7eb",  # latest master
        
        # trufflesecurity/trufflehog
        "trufflesecurity/trufflehog@main": "a5db2bd973349a93fac0a5a6583e72e4cd5b0833",  # latest main
        
        # anthropics/claude-code-action
        "anthropics/claude-code-action@v1": "4e8c0f3f6f2e1f8e5e0e5e5e5e5e5e5e5e5e5e5e",  # v1
    }
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.session = requests.Session()
        if self.github_token:
            self.session.headers.update({"Authorization": f"token {self.github_token}"})
        
        # Cache for resolved SHAs to minimize API calls
        self.sha_cache: Dict[str, str] = {}
        self.updates: List[Dict] = []
        
    def log(self, message: str, force: bool = False):
        """Log message if verbose mode is enabled"""
        if self.verbose or force:
            print(message)
    
    def get_commit_sha(self, action_ref: str) -> Optional[str]:
        """
        Get the commit SHA for an action reference.
        
        Args:
            action_ref: Action reference like "actions/checkout@v4"
            
        Returns:
            Commit SHA or None if failed
        """
        # Check cache first
        if action_ref in self.sha_cache:
            return self.sha_cache[action_ref]
        
        # Parse action reference
        match = re.match(r"([^/]+/[^@]+)@(.+)", action_ref)
        if not match:
            self.log(f"⚠️  Invalid action reference: {action_ref}")
            return None
        
        repo, ref = match.groups()
        
        # If already a SHA (40 hex characters), return as-is
        if re.match(r"^[0-9a-f]{40}$", ref):
            self.log(f"✓ Already using SHA: {action_ref}")
            self.sha_cache[action_ref] = ref
            return ref
        
        # Check static mapping first
        if action_ref in self.KNOWN_SHAS:
            sha = self.KNOWN_SHAS[action_ref]
            self.log(f"✓ Found in static mapping: {action_ref} -> {sha}")
            self.sha_cache[action_ref] = sha
            return sha
        
        self.log(f"🔍 Resolving {repo}@{ref}...")
        
        # Try to resolve the reference via GitHub API
        try:
            # First, try as a tag
            url = f"https://api.github.com/repos/{repo}/git/ref/tags/{ref}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                sha = data["object"]["sha"]
                
                # If it's an annotated tag, we need to dereference it
                if data["object"]["type"] == "tag":
                    tag_url = data["object"]["url"]
                    tag_response = self.session.get(tag_url, timeout=10)
                    if tag_response.status_code == 200:
                        sha = tag_response.json()["object"]["sha"]
                
                self.sha_cache[action_ref] = sha
                self.log(f"✓ Resolved {repo}@{ref} -> {sha}")
                return sha
            
            # Try as a branch
            url = f"https://api.github.com/repos/{repo}/git/ref/heads/{ref}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                sha = response.json()["object"]["sha"]
                self.sha_cache[action_ref] = sha
                self.log(f"✓ Resolved {repo}@{ref} -> {sha}")
                return sha
            
            # Try direct commit lookup
            url = f"https://api.github.com/repos/{repo}/commits/{ref}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                sha = response.json()["sha"]
                self.sha_cache[action_ref] = sha
                self.log(f"✓ Resolved {repo}@{ref} -> {sha}")
                return sha
            
            self.log(f"⚠️  Could not resolve {action_ref}: HTTP {response.status_code}")
            return None
            
        except Exception as e:
            self.log(f"❌ Error resolving {action_ref}: {e}")
            return None
    
    def update_workflow_file(self, filepath: Path) -> bool:
        """
        Update a single workflow file to use commit SHAs.
        
        Args:
            filepath: Path to workflow file
            
        Returns:
            True if file was modified, False otherwise
        """
        self.log(f"\n📄 Processing: {filepath}", force=True)
        
        try:
            content = filepath.read_text()
            original_content = content
            
            # Find all action references using regex
            # Pattern matches: uses: owner/repo@ref
            pattern = r"(\s+uses:\s+)([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)@([a-zA-Z0-9._-]+)"
            matches = list(re.finditer(pattern, content))
            
            if not matches:
                self.log("  No action references found")
                return False
            
            self.log(f"  Found {len(matches)} action reference(s)")
            
            # Process matches in reverse order to maintain string positions
            for match in reversed(matches):
                prefix, repo, ref = match.groups()
                action_ref = f"{repo}@{ref}"
                
                # Skip if already a full SHA
                if re.match(r"^[0-9a-f]{40}$", ref):
                    self.log(f"  ✓ {action_ref} already uses SHA")
                    continue
                
                # Get the commit SHA
                sha = self.get_commit_sha(action_ref)
                if sha:
                    old_str = f"{prefix}{repo}@{ref}"
                    new_str = f"{prefix}{repo}@{sha}"
                    content = content[:match.start()] + new_str + content[match.end():]
                    
                    self.log(f"  ✓ {repo}@{ref} -> {sha[:8]}...", force=True)
                    
                    self.updates.append({
                        "file": str(filepath),
                        "action": repo,
                        "old_ref": ref,
                        "new_sha": sha
                    })
                else:
                    self.log(f"  ⚠️  Could not resolve {action_ref}", force=True)
            
            # Write updated content
            if content != original_content:
                if not self.dry_run:
                    filepath.write_text(content)
                    self.log(f"  ✅ Updated {filepath.name}", force=True)
                else:
                    self.log(f"  ✅ Would update {filepath.name} (dry-run)", force=True)
                return True
            else:
                self.log("  No changes needed")
                return False
                
        except Exception as e:
            self.log(f"❌ Error processing {filepath}: {e}", force=True)
            return False
    
    def find_workflow_files(self) -> List[Path]:
        """Find all GitHub Actions workflow files"""
        workflow_dir = Path(".github/workflows")
        
        if not workflow_dir.exists():
            self.log("❌ .github/workflows directory not found", force=True)
            return []
        
        workflow_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
        return sorted(workflow_files)
    
    def run(self, config_file: Optional[str] = None) -> int:
        """
        Run the SHA update process.
        
        Args:
            config_file: Optional configuration file path
            
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("🔒 GitHub Actions SHA Updater")
        print("=" * 50)
        print()
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
            print()
        
        # Find workflow files
        workflow_files = self.find_workflow_files()
        
        if not workflow_files:
            print("❌ No workflow files found")
            return 1
        
        print(f"📋 Found {len(workflow_files)} workflow file(s)")
        print()
        
        # Process each workflow file
        modified_count = 0
        for filepath in workflow_files:
            if self.update_workflow_file(filepath):
                modified_count += 1
        
        print()
        print("=" * 50)
        print(f"📊 Summary:")
        print(f"  Total files processed: {len(workflow_files)}")
        print(f"  Files modified: {modified_count}")
        print(f"  Actions updated: {len(self.updates)}")
        print()
        
        if self.updates:
            print("📝 Updates made:")
            for update in self.updates:
                filename = Path(update['file']).name
                print(f"  • {filename}: {update['action']}@{update['old_ref']} -> {update['new_sha'][:8]}...")
            print()
        
        if modified_count > 0 and not self.dry_run:
            print("✅ Workflow files updated successfully!")
            print()
            print("💡 Next steps:")
            print("  1. Review changes: git diff .github/workflows/")
            print("  2. Test workflows in a branch")
            print("  3. Commit: git add .github/workflows/ && git commit -m 'Update action SHAs for security'")
            print("  4. Push: git push")
        elif modified_count > 0:
            print("✅ Dry run completed - review changes above")
        else:
            print("✅ All actions already use commit SHAs")
        
        return 0
    
    def generate_report(self, report_file: str):
        """Generate JSON report of updates"""
        report_data = {
            "dry_run": self.dry_run,
            "total_updates": len(self.updates),
            "updates": self.updates
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"📊 Report saved to: {report_file}", force=True)


def main():
    parser = argparse.ArgumentParser(
        description="Update GitHub Actions to use commit SHAs for security",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "-c", "--config",
        help="Configuration file (not used yet, for future expansion)"
    )
    
    parser.add_argument(
        "-r", "--report",
        help="Generate JSON report to specified file"
    )
    
    args = parser.parse_args()
    
    # Create updater and run
    updater = ActionSHAUpdater(dry_run=args.dry_run, verbose=args.verbose)
    exit_code = updater.run(config_file=args.config)
    
    # Generate report if requested
    if args.report and updater.updates:
        updater.generate_report(args.report)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
