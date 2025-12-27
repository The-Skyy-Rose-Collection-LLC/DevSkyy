# Branch Protection Rules

Recommended branch protection settings for the DevSkyy repository.

## Main Branch (`main`)

### Required Status Checks

Enable **"Require status checks to pass before merging"** with these checks:

| Check Name | Description | Required |
|------------|-------------|----------|
| `Python Tests` | pytest suite | ✅ Yes |
| `TypeScript Tests` | Jest collection tests | ✅ Yes |
| `TypeScript Build` | tsc compilation | ✅ Yes |
| `Python Lint & Format` | ruff, black, isort | ✅ Yes |
| `TypeScript Lint & Type Check` | tsc --noEmit | ✅ Yes |
| `CI Success` | Final aggregated check | ✅ Yes |

### Pull Request Settings

- [x] **Require a pull request before merging**
- [x] **Require approvals**: 1 (minimum)
- [x] **Dismiss stale pull request approvals when new commits are pushed**
- [x] **Require review from Code Owners**
- [x] **Require status checks to be up-to-date before merging**

### Additional Protection

- [x] **Require conversation resolution before merging**
- [x] **Require signed commits** (optional, but recommended)
- [x] **Include administrators** in restrictions
- [ ] **Allow force pushes**: Disabled
- [ ] **Allow deletions**: Disabled

## Develop Branch (`develop`)

Less restrictive for active development:

- [x] **Require status checks to pass**: `Python Tests`, `TypeScript Tests`
- [x] **Require a pull request**: 1 approval
- [ ] **Require signed commits**: Optional
- [x] **Allow force pushes**: Only for admins

## How to Configure

1. Go to **Settings** → **Branches**
2. Click **Add branch protection rule**
3. Enter branch name pattern: `main`
4. Configure settings as above
5. Click **Create** / **Save changes**

## GitHub CLI Commands

```bash
# View current protection rules
gh api repos/{owner}/{repo}/branches/main/protection

# Enable branch protection (requires admin)
gh api -X PUT repos/{owner}/{repo}/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["Python Tests","TypeScript Tests","CI Success"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f restrictions=null
```

## Rulesets (GitHub Enterprise / Advanced)

For organizations using GitHub Enterprise, consider creating repository rulesets
for more granular control over branch protections, tag protections, and push rules.
