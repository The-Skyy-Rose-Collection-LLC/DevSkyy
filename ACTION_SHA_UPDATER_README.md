# GitHub Actions SHA Updater

## Overview

The Action SHA Updater is a security compliance tool that automatically converts GitHub Actions references from version tags (e.g., `@v4`) to immutable commit SHAs (e.g., `@692973e3d937129bcbf40652eb9f2f61becf3332`).

## Why Use Commit SHAs?

Using commit SHAs for GitHub Actions provides several security benefits:

- **Immutable References**: SHAs point to specific commits that cannot be changed, preventing supply chain attacks
- **Reproducible Builds**: Ensures that workflows always use the exact same code
- **Security Compliance**: Meets enterprise security requirements and best practices
- **Prevents Tag Hijacking**: Tags can be moved to different commits; SHAs cannot

## Usage

### Quick Start

Run the update script from the repository root:

```bash
# Update all workflow files
bash scripts/update_actions.sh

# Preview changes without modifying files
bash scripts/update_actions.sh --dry-run

# Generate detailed report
bash scripts/update_actions.sh --verbose --report update_report.json
```

### Direct Python Script Usage

You can also run the Python script directly:

```bash
# Basic usage
python3 update_action_shas.py

# Dry run mode
python3 update_action_shas.py --dry-run

# Verbose output
python3 update_action_shas.py --verbose

# Generate JSON report
python3 update_action_shas.py --report update_report.json
```

## Command Line Options

### Bash Script (`scripts/update_actions.sh`)

| Option | Description |
|--------|-------------|
| `-d, --dry-run` | Preview changes without modifying files |
| `-v, --verbose` | Enable verbose logging |
| `-c, --config FILE` | Use custom configuration file (reserved for future use) |
| `-r, --report FILE` | Generate JSON report to specified file |
| `-h, --help` | Show help message |

### Python Script (`update_action_shas.py`)

| Option | Description |
|--------|-------------|
| `-d, --dry-run` | Preview changes without modifying files |
| `-v, --verbose` | Enable verbose logging |
| `-c, --config FILE` | Configuration file (reserved for future use) |
| `-r, --report FILE` | Generate JSON report to specified file |

## Examples

### Preview Changes

```bash
bash scripts/update_actions.sh --dry-run
```

Output:
```
🔒 GitHub Actions SHA Updater
==================================================

🔍 DRY RUN MODE - No files will be modified

📋 Found 10 workflow file(s)

📄 Processing: .github/workflows/ci.yml
  ✓ actions/checkout@v4 -> 692973e3...
  ✓ actions/setup-python@v5 -> 0b93645e...
  ✅ Would update ci.yml (dry-run)
```

### Update All Workflows

```bash
bash scripts/update_actions.sh
```

Output includes:
- List of updated files
- Old and new references
- Summary of changes
- Next steps for committing

### Generate Report

```bash
bash scripts/update_actions.sh --verbose --report sha_update_report.json
```

Report format (JSON):
```json
{
  "dry_run": false,
  "total_updates": 35,
  "updates": [
    {
      "file": ".github/workflows/ci.yml",
      "action": "actions/checkout",
      "old_ref": "v4",
      "new_sha": "692973e3d937129bcbf40652eb9f2f61becf3332"
    }
  ]
}
```

## How It Works

1. **Scans Workflow Files**: Finds all `.yml` and `.yaml` files in `.github/workflows/`
2. **Identifies Actions**: Uses regex to find all `uses:` statements with action references
3. **Resolves SHAs**: 
   - First checks static mapping for common actions
   - Falls back to GitHub API for unknown actions
   - Caches results to minimize API calls
4. **Updates Files**: Replaces version tags with commit SHAs
5. **Reports Results**: Shows summary of changes made

## Static Mapping

The script includes a static mapping of common GitHub Actions to their latest stable commit SHAs:

- `actions/checkout@v4` → `692973e3d937...`
- `actions/setup-python@v5` → `0b93645e9fea...`
- `actions/setup-node@v4` → `1e60f620b954...`
- `actions/upload-artifact@v4` → `6f51ac03b935...`
- `docker/setup-buildx-action@v3` → `8026d2bc3645...`
- And many more...

This eliminates the need for API calls for common actions and avoids rate limiting.

## GitHub API Rate Limiting

The script can make API calls to resolve unknown action references. To avoid rate limiting:

1. **Set GITHUB_TOKEN environment variable**:
   ```bash
   export GITHUB_TOKEN='your_github_token'
   bash scripts/update_actions.sh
   ```

2. **Use Static Mapping**: Most common actions are already in the static mapping

3. **Authenticated Rate Limit**: 5,000 requests/hour
4. **Unauthenticated Rate Limit**: 60 requests/hour

## Dependencies

The script automatically installs required dependencies:

- `requests` - For GitHub API calls
- `pyyaml` - For YAML parsing (installed but not currently used)

## After Updating

After running the script successfully:

1. **Review Changes**:
   ```bash
   git diff .github/workflows/
   ```

2. **Test Workflows**: Push to a test branch and verify workflows run correctly

3. **Commit Changes**:
   ```bash
   git add .github/workflows/
   git commit -m "Update action SHAs for security compliance"
   ```

4. **Push Changes**:
   ```bash
   git push
   ```

## Workflow Files Updated

The script automatically updates all workflow files in `.github/workflows/`:

- `ci.yml` - CI/CD pipeline
- `deploy.yml` - Deployment workflows
- `docker.yml` - Docker build and push
- `security-scan.yml` - Security scanning
- `codeql.yml` - CodeQL analysis
- `claude.yml` - Claude AI integration
- `claude-code-review.yml` - Code review automation
- `stale.yml` - Stale issue management
- `github-actions.yml` - Meta workflows
- `release.yml` - Release automation

## Security Benefits

### Before (Using Tags)
```yaml
- uses: actions/checkout@v4
```
- Tag `v4` can be moved to different commits
- Vulnerable to tag hijacking attacks
- Harder to audit what code actually ran

### After (Using SHAs)
```yaml
- uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332
```
- SHA is immutable and cannot be changed
- Exact commit is always used
- Easy to audit and verify
- Compliant with security best practices

## Troubleshooting

### "update_action_shas.py not found"

Run the script from the repository root:
```bash
cd /path/to/DevSkyy
bash scripts/update_actions.sh
```

### "Could not resolve action reference"

1. Check internet connectivity
2. Set `GITHUB_TOKEN` environment variable to avoid rate limiting
3. Verify the action exists on GitHub

### "HTTP 403" Errors

GitHub API rate limit reached. Solutions:
- Set `GITHUB_TOKEN` environment variable
- Wait for rate limit to reset (60 minutes for unauthenticated)
- Most common actions are in static mapping and don't need API calls

## Maintenance

### Updating Static Mapping

To add new actions or update existing ones in the static mapping:

1. Edit `update_action_shas.py`
2. Find the `KNOWN_SHAS` dictionary in the `ActionSHAUpdater` class
3. Add or update entries:
   ```python
   KNOWN_SHAS = {
       "actions/new-action@v1": "commit_sha_here",
       # ... other entries
   }
   ```

### Finding Commit SHAs

To find the commit SHA for an action version:

1. Visit the action's GitHub repository
2. Click on "Releases" or "Tags"
3. Find the desired version
4. Click on the commit associated with that version
5. Copy the full 40-character commit SHA

## Contributing

When contributing updates to the script:

1. Test with `--dry-run` first
2. Verify static mapping SHAs are correct
3. Update documentation if adding new features
4. Test with both authenticated and unauthenticated API access

## License

This tool is part of the DevSkyy platform and follows the same license terms.

## Support

For issues or questions:
1. Check this README first
2. Review the troubleshooting section
3. Run with `--verbose` flag to see detailed output
4. Open an issue on the DevSkyy repository
