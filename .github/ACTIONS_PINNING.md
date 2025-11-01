# GitHub Actions Pinning Documentation

All GitHub Actions in this repository are pinned to full-length commit SHAs for enhanced security.

## Why Pin Actions?

Pinning actions to commit SHAs prevents:
- **Supply chain attacks** - Malicious updates to action repositories
- **Breaking changes** - Unexpected behavior from version updates
- **Reproducibility issues** - Ensures consistent builds across time

## Current Action Versions

### Core Actions

| Action | Version Tag | Commit SHA | File |
|--------|-------------|------------|------|
| `actions/checkout` | v4.2.2 | `11bd71901bbe5b1630ceea73d27597364c9af683` | ci-cd.yml (4x), claude.yml, claude-code-review.yml |
| `actions/setup-python` | v5.5.0 | `8d9ed9ac5c53483de85588cdf95a591a75ab9f55` | ci-cd.yml (3x) |
| `actions/upload-artifact` | v4.6.2 | `ea165f8d65b6e75b540449e92b4886f43607fa02` | ci-cd.yml |

### External Service Actions

| Action | Version Tag | Commit SHA | File |
|--------|-------------|------------|------|
| `codecov/codecov-action` | v5.5.1 | `5a1091511ad55cbe89839c7260b706298ca349f7` | ci-cd.yml |

### Docker Actions

| Action | Version Tag | Commit SHA | File |
|--------|-------------|------------|------|
| `docker/setup-buildx-action` | v3.11.1 | `e468171a9de216ec08956ac3ada2f0791b6bd435` | ci-cd.yml |
| `docker/build-push-action` | v6.18.0 | `263435318d21b8e681c14492fe198d362a7d2c83` | ci-cd.yml |

### Claude Code Actions

| Action | Version Tag | Commit SHA | File |
|--------|-------------|------------|------|
| `anthropics/claude-code-action` | Latest | `52e5d0a84c4b2c19d9a650ab2c5d8c03c5e39c91` | claude.yml, claude-code-review.yml |

## Workflow Files Status

### ✅ `.github/workflows/ci-cd.yml`
- **Status**: Fully pinned
- **Actions**: 6 different actions, 11 total uses
- **Last Updated**: 2025-10-12

### ✅ `.github/workflows/claude.yml`
- **Status**: Already pinned
- **Actions**: 2 actions
- **Last Updated**: Previously pinned

### ✅ `.github/workflows/claude-code-review.yml`
- **Status**: Already pinned
- **Actions**: 2 actions
- **Last Updated**: Previously pinned

## How to Update Pinned Actions

When you need to update an action to a newer version:

1. **Find the new version tag**
   ```bash
   # Visit the action's GitHub releases page
   https://github.com/{org}/{action}/releases
   ```

2. **Get the commit SHA for that version**
   ```bash
   # Click on the version tag
   # Copy the full 40-character commit SHA
   ```

3. **Update the workflow file**
   ```yaml
   # Change from:
   - uses: actions/checkout@v4

   # To:
   - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
   ```

4. **Always include the version comment**
   - Makes it easy to see what version the SHA represents
   - Format: `# v{major}.{minor}.{patch}`

## Verification

You can verify all actions are pinned with:

```bash
# Search for any non-pinned actions (should return empty)
grep -r "uses:.*@v[0-9]" .github/workflows/

# List all pinned actions
grep -r "uses:.*@[a-f0-9]\{40\}" .github/workflows/
```

## Security Policy

- ✅ All actions MUST be pinned to full commit SHAs
- ✅ Version tags MUST be included as comments for clarity
- ✅ SHAs should be updated quarterly or when security issues are found
- ✅ All SHA updates must be reviewed for legitimacy before merging

## Automated Monitoring

Consider using these tools to monitor for action updates:

- **Dependabot**: Enable for GitHub Actions
- **Renovate Bot**: Automated dependency updates
- **GitHub Security Advisories**: Subscribe to action repositories

## Version Update Schedule

| Action | Current Version | Last Updated | Next Check |
|--------|----------------|--------------|------------|
| actions/checkout | v4.2.2 | 2025-10-12 | 2026-01-12 |
| actions/setup-python | v5.5.0 | 2025-10-12 | 2026-01-12 |
| actions/upload-artifact | v4.6.2 | 2025-10-12 | 2026-01-12 |
| codecov/codecov-action | v5.5.1 | 2025-10-12 | 2026-01-12 |
| docker/setup-buildx-action | v3.11.1 | 2025-10-12 | 2026-01-12 |
| docker/build-push-action | v6.18.0 | 2025-10-12 | 2026-01-12 |
| anthropics/claude-code-action | Latest | Previously set | As needed |

## Additional Resources

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Why You Should Pin Actions by Commit Hash](https://blog.rafaelgss.dev/why-you-should-pin-actions-by-commit-hash)
- [StepSecurity Guide](https://www.stepsecurity.io/blog/pinning-github-actions-for-enhanced-security-a-complete-guide)

---

**Last Updated**: 2025-10-12
**Maintained By**: DevSkyy Team
**Security Contact**: See SECURITY.md
