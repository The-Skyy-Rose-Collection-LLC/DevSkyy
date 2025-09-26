# GitHub Actions SHA Updater - Security Compliance Tool

## Overview

The GitHub Actions SHA Updater is an enhanced security compliance tool that automatically updates GitHub Action version tags to their corresponding commit SHAs. This follows security best practices by pinning actions to specific commits rather than mutable tags.

## Why Use SHA Pinning?

### Security Benefits
- **Immutable References**: SHAs cannot be changed, preventing supply chain attacks
- **Exact Version Control**: Ensures workflows use the exact code you've tested
- **Attack Prevention**: Prevents malicious updates to action tags
- **Compliance**: Meets enterprise security requirements for CI/CD pipelines

### Risk Mitigation
- **Tag Hijacking**: Prevents attackers from pushing malicious code to existing tags
- **Dependency Confusion**: Eliminates ambiguity about which version is being used
- **Supply Chain Security**: Provides tamper-proof action references

## Features

### Core Capabilities
- ✅ **Automatic SHA Detection**: Discovers all GitHub Actions in workflow files
- ✅ **Comprehensive Coverage**: Updates all supported actions with latest SHAs
- ✅ **Backup & Rollback**: Creates backups before changes with restore capability
- ✅ **Configuration Driven**: Flexible JSON configuration for custom setups
- ✅ **Dry Run Mode**: Preview changes without modifying files
- ✅ **Rate Limiting**: Respects GitHub API limits with authentication support
- ✅ **Error Handling**: Robust error handling with retry logic
- ✅ **Detailed Logging**: Comprehensive logging with multiple output levels
- ✅ **Priority Management**: Update actions based on security priority levels

### Enhanced Security
- 🔒 **SHA Validation**: Verifies SHA integrity and format
- 🔒 **Source Validation**: Ensures actions come from trusted sources
- 🔒 **Audit Trail**: Maintains detailed logs of all changes
- 🔒 **Rollback Safety**: Automatic rollback on update failures

## Installation & Setup

### Prerequisites
- Python 3.8+
- GitHub repository with workflow files
- Optional: GitHub Personal Access Token for higher API rate limits

### Dependencies
```bash
pip install requests pyyaml
```

### GitHub Token Setup (Recommended)
```bash
export GITHUB_TOKEN="your_personal_access_token"
```

## Usage

### Basic Usage
```bash
# Update all actions with default configuration
python3 update_action_shas.py

# Dry run to preview changes
python3 update_action_shas.py --dry-run

# Use custom configuration
python3 update_action_shas.py --config action_sha_config.json

# Enable verbose logging
python3 update_action_shas.py --verbose

# Generate detailed report
python3 update_action_shas.py --report update_report.json
```

### Advanced Usage
```bash
# Combine options for comprehensive update
python3 update_action_shas.py \
  --config action_sha_config.json \
  --verbose \
  --report update_report.json

# Dry run with custom config and reporting
python3 update_action_shas.py \
  --dry-run \
  --config action_sha_config.json \
  --report dry_run_report.json \
  --verbose
```

## Configuration

### Configuration File Structure

The script uses a JSON configuration file to define which actions to update and how:

```json
{
  "actions_to_update": {
    "actions/checkout": {
      "versions": ["v4"],
      "priority": "high",
      "description": "Repository checkout action"
    }
  },
  "backup_enabled": true,
  "dry_run": false,
  "rate_limit_delay": 1.0,
  "max_retries": 3
}
```

### Priority Levels
- **High**: Critical actions (checkout, setup-python, security scanners)
- **Medium**: Important but non-critical actions (artifact uploads, deployments)
- **Low**: Nice-to-have actions (stale issue management)

### Supported Actions

The script automatically detects and can update these GitHub Actions:

#### Core GitHub Actions
- `actions/checkout@v4` - Repository checkout
- `actions/setup-python@v4,v5` - Python environment setup
- `actions/setup-node@v5` - Node.js environment setup
- `actions/github-script@v6` - GitHub API interactions
- `actions/upload-artifact@v4` - Artifact uploads
- `actions/stale@v5` - Stale issue management

#### GitHub Pages Actions
- `actions/configure-pages@v5` - Pages configuration
- `actions/deploy-pages@v4` - Pages deployment
- `actions/jekyll-build-pages@v1` - Jekyll builds
- `actions/upload-pages-artifact@v3` - Pages artifacts

#### Security Actions
- `github/codeql-action/init@v3` - CodeQL initialization
- `github/codeql-action/analyze@v3` - CodeQL analysis

#### Third-Party Actions
- `codecov/codecov-action@v3` - Code coverage
- `docker/build-push-action@v5` - Docker builds
- `docker/login-action@v3` - Docker authentication
- `docker/setup-buildx-action@v3` - Docker Buildx

## Workflow Integration

### Manual Execution
Run the script manually when you want to update action SHAs:

```bash
python3 update_action_shas.py --config action_sha_config.json --report update_report.json
```

### Automated Integration
Create a GitHub workflow to run the updater periodically:

```yaml
name: Update Action SHAs
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Mondays at 2 AM
  workflow_dispatch:

jobs:
  update-shas:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install requests pyyaml
      
      - name: Update Action SHAs
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 update_action_shas.py \
            --config action_sha_config.json \
            --report sha_update_report.json \
            --verbose
      
      - name: Create Pull Request
        if: success()
        uses: actions/github-script@v6
        with:
          script: |
            // Create PR with updated SHAs
            // Implementation depends on your workflow
```

## Output & Reporting

### Console Output
```
2024-01-15 10:30:00 - INFO - Starting GitHub Actions SHA update process
2024-01-15 10:30:01 - INFO - Created backup at .github/workflows_backup
2024-01-15 10:30:02 - INFO - Found 5 actions in ci-cd-pipeline.yml
2024-01-15 10:30:03 - INFO - ✅ actions/checkout@v4 -> a1b2c3d4...
2024-01-15 10:30:04 - INFO - ✅ actions/setup-python@v5 -> e5f6g7h8...
2024-01-15 10:30:05 - INFO - Updated ci-cd-pipeline.yml
2024-01-15 10:30:06 - INFO - ========================================
2024-01-15 10:30:06 - INFO - SHA UPDATE SUMMARY
2024-01-15 10:30:06 - INFO - ========================================
2024-01-15 10:30:06 - INFO - Files processed: 8
2024-01-15 10:30:06 - INFO - Files updated: 3  
2024-01-15 10:30:06 - INFO - Actions updated: 12
2024-01-15 10:30:06 - INFO - Failed updates: 0
```

### JSON Report
```json
{
  "timestamp": "2024-01-15T10:30:06.123456",
  "config": {...},
  "updated_actions": {
    "actions/checkout@v4": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
    "actions/setup-python@v5": "e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0a1b2c3d4"
  },
  "failed_updates": [],
  "summary": {
    "total_updated": 12,
    "total_failed": 0,
    "success_rate": 100.0
  }
}
```

## Safety Features

### Backup System
- Automatic backup creation before any changes
- Restore capability in case of errors
- Configurable backup retention

### Validation
- SHA format validation (40-character hex)
- Action source validation against allowlist
- Workflow syntax preservation

### Error Handling
- Comprehensive exception handling
- Automatic rollback on critical errors
- Detailed error logging and reporting

## Troubleshooting

### Common Issues

#### API Rate Limiting
```bash
# Solution: Set GitHub token
export GITHUB_TOKEN="your_token_here"
```

#### Network Errors
- Check internet connectivity
- Verify GitHub API accessibility
- Review proxy settings if applicable

#### Permission Errors
- Ensure write permissions to workflow directory
- Check Git repository permissions
- Verify backup directory creation rights

### Debug Mode
```bash
python3 update_action_shas.py --verbose --dry-run
```

## Security Considerations

### Best Practices
1. **Regular Updates**: Run weekly or bi-weekly to stay current
2. **Token Security**: Use secure token storage (GitHub Secrets)
3. **Backup Verification**: Regularly test backup restore process
4. **Audit Logs**: Review update logs for unusual changes
5. **Testing**: Test updated workflows in staging before production

### Compliance
- Follows NIST Cybersecurity Framework guidelines
- Meets SOC 2 Type II requirements for supply chain security
- Supports enterprise security policies
- Provides audit trail for compliance reporting

## Contributing

### Development Setup
```bash
git clone https://github.com/SkyyRoseLLC/DevSkyy.git
cd DevSkyy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Adding New Actions
1. Update `action_sha_config.json` with new action details
2. Test with `--dry-run` flag
3. Verify SHA retrieval and validation
4. Update documentation

### Testing
```bash
# Run in dry-run mode
python3 update_action_shas.py --dry-run --verbose

# Test with custom config
python3 update_action_shas.py --config test_config.json --dry-run
```

## License

MIT License - See LICENSE file for details.

## Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue](https://github.com/SkyyRoseLLC/DevSkyy/issues)
- Documentation: This file and inline code comments
- Security Issues: Please report privately to the maintainers

---

**Note**: This tool is part of the DevSkyy Enhanced Platform's security compliance toolkit. Regular updates ensure your GitHub Actions workflows maintain the highest security standards.