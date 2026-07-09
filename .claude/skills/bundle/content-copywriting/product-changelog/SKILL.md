---
name: product-changelog
description: "Creates product changelog formats with version notes, categorization (new, improved, fixed), and user-friendly language. Use when documenting product updates for users."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Product Changelog

## When to Use This Skill

Use this skill when you need to:
- Create a changelog format and template for ongoing product updates
- Write user-friendly version notes for a product release
- Categorize changes into new features, improvements, and bug fixes
- Establish a consistent changelog cadence and style

**DO NOT** use this skill for internal release notes (engineering-facing), feature announcements (marketing-facing), or technical API documentation. This is for user-facing product changelogs.

---

## Core Principle

A CHANGELOG BUILDS USER TRUST BY SHOWING CONTINUOUS IMPROVEMENT — WRITE EVERY ENTRY SO A NON-TECHNICAL USER UNDERSTANDS WHAT CHANGED AND WHY IT MATTERS TO THEM.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product name** | "What product is this changelog for?" | No default — must be provided |
| **Update frequency** | "How often do you ship updates? Weekly, biweekly, monthly?" | Biweekly |
| **Audience** | "Are changelog readers technical or non-technical?" | Non-technical business users |
| **Current changes** | "List the changes in this update — features, improvements, and fixes." | No default — must be provided |
| **Version numbering** | "Do you use version numbers, dates, or both?" | Date-based (e.g., January 15, 2026) |
| **Distribution** | "Where does the changelog live? In-app, blog, email, dedicated page?" | Dedicated changelog page |

**GATE: Confirm the brief before writing.**

---

## Phase 2: Structure

### Category System

Every change falls into one of these categories:

- **New** — Features or capabilities that did not exist before
- **Improved** — Enhancements to existing features (performance, UX, expanded functionality)
- **Fixed** — Bug fixes and issue resolutions
- **Removed** (use sparingly) — Deprecated features with migration guidance

### Entry Format

Each changelog entry follows this structure:

```
### [Date or Version]

**New**
- **[Feature name]** — [What it does and why it matters in one sentence]

**Improved**
- **[Feature name]** — [What changed and the user benefit]

**Fixed**
- **[Issue description]** — [What was broken and confirmation it is resolved]
```

**GATE: Confirm the category system and format before writing entries.**

---

## Phase 3: Write

### Writing Rules

- **Lead with the benefit, not the technical change.** "Invoices now send 3x faster" beats "Optimized invoice queue processing."
- **One sentence per entry.** If it needs more, it deserves a feature announcement.
- **Use active voice.** "You can now export to PDF" not "PDF export has been added."
- **Be specific about fixes.** "Fixed: Emails with attachments over 5MB failed to send" not "Fixed email bug."
- **Group related changes.** If 3 fixes relate to the same feature, list them under one sub-heading.

### Tone Guide

- Conversational but professional
- Celebratory for big features ("We have been working on this one for months...")
- Matter-of-fact for fixes (acknowledge, confirm fixed, move on)
- No apologies for bugs — just fix and state clearly

### Entry Length Guide

| Category | Length | Detail Level |
|----------|--------|-------------|
| Major new feature | 2-3 sentences | Benefit + how to access it |
| Minor improvement | 1 sentence | What changed + benefit |
| Bug fix | 1 sentence | What was broken + resolved |
| Deprecation | 2-3 sentences | What, when, migration path |

---

## Phase 4: Polish

### 1. Changelog Page Template

Provide a recommended page layout:
- Product name and "Changelog" or "What's New" header
- Filter/search by category (New, Improved, Fixed)
- Subscribe option (email or RSS)
- Archive with expandable months or pagination
- Link to roadmap or feature request board

### 2. Distribution Plan

- **In-app:** Badge notification on changelog link when new entries exist
- **Email:** Monthly digest of changes for subscribers
- **Social:** Highlight major features in a dedicated post
- **Blog:** Full write-up for major releases only

### 3. Quality Checklist

```
## Changelog Quality Checklist

- [ ] Every entry starts with a benefit, not a technical description
- [ ] Changes are categorized as New, Improved, or Fixed
- [ ] Each entry is one sentence (major features may use 2-3)
- [ ] Active voice used throughout
- [ ] Bug fixes describe what was broken specifically
- [ ] No jargon — readable by non-technical users
- [ ] Date or version number is included
- [ ] Deprecated features include migration guidance
- [ ] Subscribe/notification option exists for the changelog page
```

---

## Example

```
### February 15, 2026

**New**
- **Recurring invoices** — Set any invoice to automatically send on a schedule (weekly, monthly, or custom). Find it under Invoice Settings.
- **Client portal** — Your clients can now view all their invoices and payment history in one place. Share the link from any client profile.

**Improved**
- **Dashboard loading speed** — Dashboard now loads 60% faster, especially for accounts with 500+ invoices.
- **CSV exports** — Exports now include payment status and date columns by default.

**Fixed**
- **Tax calculation on discounted items** — Tax was calculated before the discount was applied, resulting in overcharges. Now calculates correctly on the discounted amount.
- **Email notifications** — Some users were not receiving payment confirmation emails. Resolved for all accounts.
```

---

## Anti-Patterns

- **Technical jargon** — "Refactored the webhook handler" means nothing to users. Translate to impact.
- **Vague fix descriptions** — "Fixed a bug" tells users nothing. Be specific about what was broken.
- **Skipping updates** — inconsistent changelogs erode trust. Ship on your stated cadence, even if it is a small update.
- **Marketing fluff in changelogs** — save the hype for feature announcements. Changelogs should be factual and scannable.
- **No categorization** — a flat list of changes is hard to scan. Always categorize.

---

## Recovery

- **Very few changes this cycle:** Combine with the next cycle, or ship a brief update noting improvements and behind-the-scenes work.
- **Breaking change included:** Lead with the breaking change, explain what users need to do, and provide a migration guide link.
- **User-reported bug is fixed:** Consider naming the fix in a way that acknowledges the report: "Fixed (thanks for reporting!): [description]."
- **No changelog exists yet:** Create a retroactive launch entry summarizing the product's current capabilities, then begin regular updates.
