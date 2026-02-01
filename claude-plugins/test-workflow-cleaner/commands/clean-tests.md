---
name: clean-tests
description: Remove outdated and irrelevant tests from the codebase. Creates backups before deletion and provides undo capability.
---

# Clean Tests Command

You have been asked to clean the test suite. Follow this workflow:

## Step 1: Review or Generate Analysis

First, check if a recent test analysis exists. If not, run analysis:

- Look for existing analysis report
- If no report, trigger test-analyzer agent first
- Review which tests are flagged for removal

## Step 2: Create Backup

**CRITICAL: ALWAYS backup before any deletion**

```bash
# Create timestamped backup directory
BACKUP_DIR=".test-backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copy all files that will be deleted
cp <file_to_delete> "$BACKUP_DIR/"
```

## Step 3: Categorize and Confirm Deletions

| Category | Auto-Delete | Action |
|----------|-------------|--------|
| Orphaned (source deleted) | Yes | Delete |
| Import errors (unresolvable) | Yes | Delete |
| Skipped 60+ days | Yes | Delete |
| Skipped 30-60 days | No | Flag for review |
| Empty/no assertions | Yes | Delete |
| Modified in last 7 days | No | Never delete |

## Step 4: Execute Deletions

For files to be deleted entirely:
```bash
# Move to backup (safer than rm)
mv <test_file> "$BACKUP_DIR/"
```

For partial cleanup (specific tests within a file):
- Use Edit tool to remove specific test functions
- Preserve file structure and remaining valid tests

## Step 5: Verify Cleanup

After deletion, verify the test suite still works:

```bash
# Run remaining tests
pytest -v --tb=short  # Python
npm test              # JavaScript
go test -v ./...      # Go
cargo test            # Rust
```

## Step 6: Generate Cleanup Report

```markdown
# Test Cleanup Report

## Deleted Files
| File | Reason | Backup Location |
|------|--------|-----------------|
| ... | ... | ... |

## Deleted Tests (from files)
| File | Test | Reason |
|------|------|--------|
| ... | ... | ... |

## Undo Instructions
To restore all deleted files:
\`\`\`bash
cp -r .test-backups/<timestamp>/* tests/
\`\`\`

## Summary
- Files deleted: X
- Tests removed: Y
- Tests remaining: Z
```

## Safety Rules

1. **NEVER delete without backup**
2. **NEVER delete tests that pass** (unless clearly orphaned)
3. **NEVER delete tests modified in last 7 days**
4. **ALWAYS verify after cleanup**
5. **ALWAYS provide undo instructions**

## Undo Mechanism

```bash
# List available backups
ls -la .test-backups/

# Restore specific backup
cp -r .test-backups/<timestamp>/* tests/

# Restore single file
cp .test-backups/<timestamp>/<filename> tests/
```
