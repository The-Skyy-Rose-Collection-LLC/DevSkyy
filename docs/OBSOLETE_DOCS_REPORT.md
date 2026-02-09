# Obsolete Documentation Report

**Generated**: 2026-02-08
**Scan Location**: `/Users/coreyfoster/DevSkyy`
**Criteria**: Status reports (30 days), deployment reports (60 days), general docs (90 days)

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| **Obsolete Status Reports** | 10 | Archive to `docs/archive/2026/` |
| **Obsolete Deployment Reports** | 6 | Archive to `docs/archive/2026/` |
| **Obsolete General Docs** | 2 | Archive to `docs/archive/2026/` |
| **Core Docs (Never Obsolete)** | 3 | Keep in root |
| **Total Files Scanned** | 26 | - |
| **Total Files to Archive** | 18 | - |

---

## Obsolescence Criteria

**Status/Report Files** (30-day threshold):
- Files with naming patterns: `*_STATUS.md`, `*_SUMMARY.md`, `*_COMPLETE.md`, `*_FIXED.md`
- These document temporary states and become outdated quickly

**Deployment Reports** (60-day threshold):
- Files with naming patterns: `*_DEPLOYMENT*.md`, `*_FIX*.md`, `*_CHECKLIST.md`
- Deployment-specific documentation that becomes historical after 60 days

**General Documentation** (90-day threshold):
- General documentation files (e.g., `QUICK_START*.md`, `NEXT_STEPS.md`)
- Technical guides that may become outdated with platform changes

**Never Obsolete:**
- `README.md` - Main project documentation
- `CLAUDE.md` - Active project instructions
- `AGENTS.md` - Active agent documentation
- Files in `docs/` directory (managed separately)

---

## Obsolete Files Identified

### Status Reports (10 files) - Obsolete after 30 days

| File | Created/Modified | Age (days) | Status | Action |
|------|-----------------|------------|--------|--------|
| `RALPH_LOOP_STATUS.md` | Jan 30 | 9 | Archived | Move to archive |
| `RALPH_LOOP_ITERATION_1_STATUS.md` | Jan 30 | 9 | Archived | Move to archive |
| `RALPH_LOOP_ITERATION_1_COMPLETE.md` | Jan 30 | 9 | Archived | Move to archive |
| `RALPH_LOOP_ITERATION_1_SUMMARY.md` | Jan 30 | 9 | Archived | Move to archive |
| `RALPH_LOOP_FINAL_STATUS.md` | Jan 30 | 9 | Archived | Move to archive |
| `PLUGINS_FIXED_SUMMARY.md` | Jan 28 | 11 | Archived | Move to archive |
| `PLUGINS_FIXED_CHANGELOG.md` | Jan 28 | 11 | Archived | Move to archive |
| `PLUGINS_ACTUALLY_FIXED.md` | Jan 28 | 11 | Archived | Move to archive |
| `CLEANUP_PROGRESS.md` | Jan 20 | 19 | Archived | Move to archive |
| `NEXT_STEPS.md` | Jan 28 | 11 | Archived | Move to archive |

**Rationale**: These files documented temporary project states (Ralph Loop iterations, plugin fixes, cleanup progress). The information is historical and no longer actionable.

### Deployment Reports (6 files) - Obsolete after 60 days

| File | Created/Modified | Age (days) | Status | Action |
|------|-----------------|------------|--------|--------|
| `WORDPRESS-CSP-FIX-DEPLOYMENT.md` | Feb 5 | 3 | Keep temporarily | Archive in 57 days |
| `WORDPRESS-CSP-CONTEXT7-VERIFICATION.md` | Feb 5 | 3 | Keep temporarily | Archive in 57 days |
| `WORDPRESS-CSP-FIX-SUMMARY.md` | Feb 5 | 3 | Keep temporarily | Archive in 57 days |
| `WORDPRESS-DEPLOYMENT-CHECKLIST.md` | Feb 5 | 3 | Superseded | Archive (replaced by RUNBOOK.md) |
| `WORDPRESS-OPERATIONS-SUMMARY.md` | Feb 5 | 3 | Superseded | Archive (replaced by RUNBOOK.md) |
| `WORDPRESS-HEALTH-CHECK-REPORT.md` | Feb 5 | 3 | Superseded | Archive (replaced by RUNBOOK.md) |

**Rationale**: WordPress CSP fix files are recent (3 days old) but will become historical in 60 days. Checklist/operations/health check files are superseded by the new comprehensive RUNBOOK.md.

### Obsolete WordPress Documentation (4 files) - Superseded

| File | Created/Modified | Status | Action |
|------|-----------------|--------|--------|
| `WORDPRESS_THEME_INTEGRATION.md` | Jan 30 | Superseded | Archive (info in CONTRIB.md) |
| `WORDPRESS_MCP_FIX.md` | Jan 30 | Superseded | Archive (historical fix) |
| `WORDPRESS_MCP_QUICKSTART.md` | Jan 30 | Superseded | Archive (info in CONTRIB.md) |
| `WORDPRESS-INVESTIGATION-REPORT.md` | Feb 5 | Superseded | Archive (historical) |

**Rationale**: WordPress documentation has been consolidated into CONTRIB.md and RUNBOOK.md. These files are no longer the source of truth.

### General Documentation (2 files) - Obsolete after 90 days

| File | Created/Modified | Age (days) | Status | Action |
|------|-----------------|------------|--------|--------|
| `QUICK_START_3D_GENERATION.md` | Jan 18 | 21 | Keep temporarily | Archive in 69 days |
| `SECURITY-FIXES.md` | Feb 4 | 4 | Keep temporarily | Archive in 86 days |

**Rationale**: 3D generation quickstart is <90 days old. Security fixes document is recent. Both will be archived when they reach the 90-day threshold unless updated.

### Superseded Documentation (2 files) - Replaced

| File | Created/Modified | Replaced By | Action |
|------|-----------------|-------------|--------|
| `PRODUCTION_RUNBOOK.md` | Jan 20 | `docs/RUNBOOK.md` | Archive (superseded) |
| `everything-claude-code.md` | Jan 22 | `.claude/rules/` directory | Archive (superseded) |

**Rationale**: PRODUCTION_RUNBOOK.md has been replaced by the enhanced docs/RUNBOOK.md. everything-claude-code.md has been split into .claude/rules/ files.

---

## Files to Keep (Never Obsolete)

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Main project documentation | Active |
| `CLAUDE.md` | Project-specific instructions | Active |
| `AGENTS.md` | Agent documentation | Active |

---

## Archival Actions

### Immediate Archival (18 files)

**Status Reports (10 files):**
```bash
mv RALPH_LOOP_STATUS.md docs/archive/2026/
mv RALPH_LOOP_ITERATION_1_STATUS.md docs/archive/2026/
mv RALPH_LOOP_ITERATION_1_COMPLETE.md docs/archive/2026/
mv RALPH_LOOP_ITERATION_1_SUMMARY.md docs/archive/2026/
mv RALPH_LOOP_FINAL_STATUS.md docs/archive/2026/
mv PLUGINS_FIXED_SUMMARY.md docs/archive/2026/
mv PLUGINS_FIXED_CHANGELOG.md docs/archive/2026/
mv PLUGINS_ACTUALLY_FIXED.md docs/archive/2026/
mv CLEANUP_PROGRESS.md docs/archive/2026/
mv NEXT_STEPS.md docs/archive/2026/
```

**Superseded WordPress Docs (4 files):**
```bash
mv WORDPRESS_THEME_INTEGRATION.md docs/archive/2026/
mv WORDPRESS_MCP_FIX.md docs/archive/2026/
mv WORDPRESS_MCP_QUICKSTART.md docs/archive/2026/
mv WORDPRESS-INVESTIGATION-REPORT.md docs/archive/2026/
```

**Superseded Deployment Docs (3 files):**
```bash
mv WORDPRESS-DEPLOYMENT-CHECKLIST.md docs/archive/2026/
mv WORDPRESS-OPERATIONS-SUMMARY.md docs/archive/2026/
mv WORDPRESS-HEALTH-CHECK-REPORT.md docs/archive/2026/
```

**Superseded General Docs (2 files):**
```bash
mv PRODUCTION_RUNBOOK.md docs/archive/2026/
mv everything-claude-code.md docs/archive/2026/
```

### Future Archival (Scheduled)

**In 57 days (2026-04-06):**
```bash
# WordPress CSP fix documentation (60-day threshold)
mv WORDPRESS-CSP-FIX-DEPLOYMENT.md docs/archive/2026/
mv WORDPRESS-CSP-CONTEXT7-VERIFICATION.md docs/archive/2026/
mv WORDPRESS-CSP-FIX-SUMMARY.md docs/archive/2026/
```

**In 69 days (2026-04-18):**
```bash
# 3D generation quickstart (90-day threshold)
mv QUICK_START_3D_GENERATION.md docs/archive/2026/
```

**In 86 days (2026-05-05):**
```bash
# Security fixes documentation (90-day threshold)
mv SECURITY-FIXES.md docs/archive/2026/
```

---

## Post-Archival Root Directory

After archival, root directory will contain:

**Active Core Documentation (3 files):**
- `README.md` - Main project README
- `CLAUDE.md` - Project instructions for Claude Code
- `AGENTS.md` - Agent documentation

**Recent Documentation (To be archived later - 4 files):**
- `WORDPRESS-CSP-FIX-DEPLOYMENT.md` (archive in 57 days)
- `WORDPRESS-CSP-CONTEXT7-VERIFICATION.md` (archive in 57 days)
- `WORDPRESS-CSP-FIX-SUMMARY.md` (archive in 57 days)
- `QUICK_START_3D_GENERATION.md` (archive in 69 days)
- `SECURITY-FIXES.md` (archive in 86 days)

**Total Root .md Files After Immediate Archival**: 8 (down from 26)

---

## Archive Directory Structure

```
docs/archive/2026/
├── RALPH_LOOP_STATUS.md
├── RALPH_LOOP_ITERATION_1_STATUS.md
├── RALPH_LOOP_ITERATION_1_COMPLETE.md
├── RALPH_LOOP_ITERATION_1_SUMMARY.md
├── RALPH_LOOP_FINAL_STATUS.md
├── PLUGINS_FIXED_SUMMARY.md
├── PLUGINS_FIXED_CHANGELOG.md
├── PLUGINS_ACTUALLY_FIXED.md
├── CLEANUP_PROGRESS.md
├── NEXT_STEPS.md
├── WORDPRESS_THEME_INTEGRATION.md
├── WORDPRESS_MCP_FIX.md
├── WORDPRESS_MCP_QUICKSTART.md
├── WORDPRESS-INVESTIGATION-REPORT.md
├── WORDPRESS-DEPLOYMENT-CHECKLIST.md
├── WORDPRESS-OPERATIONS-SUMMARY.md
├── WORDPRESS-HEALTH-CHECK-REPORT.md
├── PRODUCTION_RUNBOOK.md
└── everything-claude-code.md
```

**Total Archived**: 19 files (18 immediate + 1 superseded)

---

## Justification for Archival

### Why Archive Instead of Delete?

1. **Historical Record**: Documents project evolution and decisions
2. **Reference**: May need to reference old deployment procedures or fixes
3. **Learning**: Future team members can learn from past approaches
4. **Audit Trail**: Maintains record of changes for compliance/security

### Why These Files Are Obsolete

**Status Reports**: Document point-in-time project states that are no longer current. Information is historical and not actionable.

**Deployment Reports**: Specific to past deployments. Current deployment procedures are in RUNBOOK.md.

**Superseded Docs**: Information has been consolidated into comprehensive guides (CONTRIB.md, RUNBOOK.md, ENV_VARS_REFERENCE.md).

**WordPress Docs**: Scattered WordPress documentation has been consolidated into CONTRIB.md (development) and RUNBOOK.md (deployment/operations).

---

## Recommendations

1. **Maintain Archive**: Keep `docs/archive/YYYY/` structure for historical files
2. **Review Quarterly**: Every 90 days, scan for new obsolete documentation
3. **Update Core Docs**: Keep README.md, CLAUDE.md, and AGENTS.md current
4. **Use docs/ Directory**: New documentation should go in `docs/` directory, not root
5. **Naming Convention**: Use `docs/` subdirectories for organization:
   - `docs/deployment/` - Deployment guides
   - `docs/development/` - Development guides
   - `docs/operations/` - Operational procedures
   - `docs/archive/YYYY/` - Historical files

---

## Verification

After archival, verify:

```bash
# Count root .md files (should be 8)
ls -1 *.md | wc -l

# List remaining root .md files
ls -1 *.md

# Count archived files (should be 19)
ls -1 docs/archive/2026/*.md | wc -l

# Verify core docs exist
ls -la README.md CLAUDE.md AGENTS.md
```

---

**Generated By**: Documentation Update Task
**Archive Location**: `docs/archive/2026/`
**Next Review**: 2026-05-01 (90 days)
