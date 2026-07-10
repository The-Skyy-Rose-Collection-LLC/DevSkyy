---
name: release-notes
description: "Writes user-friendly release notes with categorized changes, migration guides, and known issues. Use when communicating software updates to users and stakeholders."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Release Notes

## When to Use This Skill

Use this skill when you need to:
- Write release notes for a software update or new version
- Communicate breaking changes with migration guides
- Document known issues and workarounds for a release
- Create release notes that serve both technical and non-technical audiences

**DO NOT** use this skill for product changelogs (ongoing, shorter entries), feature announcements (marketing-focused), or internal engineering post-mortems. This is for formal release notes tied to a specific version or update.

---

## Core Principle

RELEASE NOTES SERVE TWO AUDIENCES SIMULTANEOUSLY — USERS WHO WANT TO KNOW WHAT CHANGED AND DEVELOPERS WHO NEED TO KNOW WHAT BROKE. WRITE FOR BOTH.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Version number** | "What is the version or release identifier?" | No default — must be provided |
| **Release date** | "When is this release going live?" | Today |
| **Changes list** | "List all changes — features, improvements, fixes, breaking changes." | No default — must be provided |
| **Breaking changes** | "Are there any breaking changes that require user action?" | None |
| **Known issues** | "Are there any known issues shipping with this release?" | None |
| **Audience** | "Are readers technical developers, end users, or both?" | Both |

**GATE: Confirm the brief before writing.**

---

## Phase 2: Categorize Changes

Sort every change into one of these categories:

- **Highlights** — Major features or changes worth calling out at the top
- **New Features** — Capabilities that did not exist before
- **Improvements** — Enhancements to existing functionality
- **Bug Fixes** — Issues resolved in this release
- **Breaking Changes** — Changes that require user action or code updates
- **Deprecations** — Features being phased out (with timeline)
- **Known Issues** — Problems shipping with this release (with workarounds)

Present the categorized list for confirmation.

**GATE: Confirm categorization before writing the full notes.**

---

## Phase 3: Write

### Release Notes Format

```
# Release Notes — v[X.Y.Z]
**Release Date:** [Date]

## Highlights

[1-2 paragraph summary of the most important changes in this release. Write for someone skimming — they should understand the impact in 30 seconds.]

## New Features

- **[Feature name]** — [What it does and how to access it. 1-2 sentences.]

## Improvements

- **[Area improved]** — [What changed and the user benefit. 1 sentence.]

## Bug Fixes

- **[Issue description]** — [What was broken and confirmation it is resolved. 1 sentence.]

## Breaking Changes

### [Change title]
**Impact:** [Who is affected and how]
**Action required:** [Exactly what users must do]
**Migration guide:** [Step-by-step instructions]
**Deadline:** [When the old behavior stops working]

## Deprecations

- **[Feature name]** — Deprecated as of this release. Will be removed in v[X.Y.Z]. Use [alternative] instead.

## Known Issues

- **[Issue description]** — [Workaround if available. Expected fix in v[X.Y.Z].]
```

### Writing Rules

- **Highlights section is mandatory** — even for small releases, summarize the key changes in 2-3 sentences
- **User-facing language** — translate technical changes to user impact
- **Specific bug fix descriptions** — "Fixed login failure on Safari 17" not "Fixed authentication bug"
- **Breaking changes get full treatment** — impact statement, action required, migration steps, and deadline
- **Known issues include workarounds** — never list a known issue without a workaround or expected fix date

---

## Phase 4: Polish

### 1. Migration Guide (if breaking changes exist)

Write a step-by-step migration guide:
- Before/after code examples
- Configuration changes required
- Timeline for backward compatibility
- Support contact for migration issues

### 2. Distribution Plan

| Channel | Format | Audience |
|---------|--------|----------|
| In-app notification | Highlight summary + link | All users |
| Email | Full release notes | Opted-in users |
| Documentation site | Complete notes with migration guides | Developers |
| Blog | Highlights only with feature focus | Prospects and public |
| Social media | One-liner about the biggest change | General audience |

### 3. Quality Checklist

```
## Release Notes Checklist

- [ ] Version number and date are clearly stated
- [ ] Highlights section summarizes key changes in 2-3 sentences
- [ ] All changes are categorized (New, Improved, Fixed, Breaking, Deprecated)
- [ ] Breaking changes include impact, action required, and migration steps
- [ ] Bug fixes describe what was broken specifically
- [ ] Known issues include workarounds or fix timelines
- [ ] Language is understandable by non-technical users
- [ ] No internal jargon, ticket numbers, or code references in user-facing notes
- [ ] Distribution plan covers all relevant channels
- [ ] Deprecation timeline is specific (version number and date)
```

---

## Example

**Version:** v2.4.0
**Release date:** February 27, 2026

**Highlights excerpt:**
"Version 2.4.0 introduces recurring invoices and a redesigned dashboard. Recurring invoices let you schedule automatic billing on any cadence — set it once, and invoices send themselves. The new dashboard loads 60% faster and surfaces your most important metrics at a glance."

**Breaking change excerpt:**
```
### API v1 Endpoints Deprecated

**Impact:** All users making API calls to api.example.com/v1/ endpoints.
**Action required:** Update your API calls to use /v2/ endpoints by April 30, 2026.
**Migration guide:**
1. Replace /v1/ with /v2/ in all endpoint URLs
2. Update the Authorization header format (see docs)
3. Test with the sandbox environment
4. Switch production calls before April 30

**Deadline:** April 30, 2026. After this date, /v1/ endpoints will return 410 Gone.
```

---

## Anti-Patterns

- **Dumping git commit messages** — "Fixed #4521" and "Refactored user service" are not release notes. Translate to user impact.
- **Hiding breaking changes** — burying them at the bottom guarantees angry users. Lead with breaking changes or highlight them prominently.
- **No migration guide** — telling users something broke without telling them how to fix it is worse than not telling them at all.
- **Skipping known issues** — users will find them anyway. Documenting them proactively builds trust.
- **Marketing fluff** — release notes are not blog posts. Be factual, specific, and concise.

---

## Recovery

- **Tiny release with few changes:** Write a brief note. Even "Bug fixes and performance improvements" is better than silence, but add specifics.
- **Major breaking change with complex migration:** Create a dedicated migration guide document. Link from the release notes.
- **Known issue with no workaround:** State the issue, acknowledge the impact, and provide a timeline for the fix. Offer direct support contact.
- **Release was rolled back:** Publish a note explaining the rollback, what was affected, and when the re-release is expected.
