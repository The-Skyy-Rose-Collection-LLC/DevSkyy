---
name: article-rewriter
description: "Rewrites existing articles with fresh angles, updated data, and improved SEO while preserving core message. Use when refreshing outdated content or adapting articles for new audiences."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Article Rewriter

## When to Use This Skill

Use this skill when you need to:
- Refresh an outdated blog post with current data and improved structure
- Rewrite an article with a new angle for a different audience
- Improve SEO performance of existing content that has lost rankings
- Update a competitor-style article into original, higher-quality content

**DO NOT** use this skill for spinning or plagiarizing content. This skill produces genuinely rewritten content that adds new value.

---

## Core Principle

A REWRITE MUST MAKE THE CONTENT MEANINGFULLY BETTER — NOT JUST DIFFERENT. IF THE REWRITE ADDS NO NEW VALUE, IT IS A WASTE OF TIME.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Original article** | "Paste the article or provide the URL." | No default — must be provided |
| **Rewrite goal** | "Why are you rewriting? SEO refresh, new audience, updated info, better quality?" | SEO refresh |
| **Target keyword** | "What keyword should the rewritten version target?" | Same as original |
| **Audience** | "Same audience or different?" | Same audience |
| **What to keep** | "Any sections, examples, or data that must stay?" | Preserve core message and structure |
| **What to change** | "What specifically needs improvement?" | User's discretion — will audit |
| **Word count** | "Target length for the rewrite?" | Match original +/- 20% |

**GATE: Confirm brief and review original article before proceeding.**

---

## Phase 2: Audit and Plan

### Content Audit

Before rewriting, analyze the original article on these dimensions:

```
## Content Audit

**Strengths (keep these):**
- [What works well — strong sections, good examples, solid structure]

**Weaknesses (fix these):**
- [Outdated data, weak intro, poor formatting, missing sections]

**SEO Issues:**
- [Keyword placement, meta description, heading structure, density]

**Structural Issues:**
- [Flow problems, missing transitions, wall-of-text sections]

**Missing Elements:**
- [Examples, data, internal links, CTA, visuals]
```

### Rewrite Plan

```
## Rewrite Plan

**New angle/hook:** [How the rewrite will open differently]
**Sections to keep (with updates):** [List]
**Sections to rewrite completely:** [List]
**Sections to add:** [List]
**Sections to cut:** [List]
**New data or examples to include:** [List]
```

**GATE: Present audit and plan for approval before rewriting.**

---

## Phase 3: Write

### Rewriting Rules

| Rule | Detail |
|------|--------|
| **Never copy-paste paragraphs** | Every paragraph must be rewritten, not rearranged |
| **New intro required** | The opening paragraph must be completely original |
| **Add new value** | Include at least 2 new examples, data points, or insights not in the original |
| **Improve structure** | Fix heading hierarchy, add lists where text is dense |
| **Update data** | Replace outdated statistics with current ones (note sources) |
| **Better formatting** | Short paragraphs, bold key phrases, bullet points for lists of 3+ |
| **SEO optimization** | Apply keyword placement rules (H1, first 100 words, H2s, meta description) |

### Rewrite Checklist (per section)

For each section of the rewrite:
- Is this meaningfully different from the original (not just synonym swaps)?
- Does it add new value (examples, data, perspective)?
- Is it better structured and more readable?
- Does it serve the target keyword better?

### Deliverables

1. **Full rewritten article** with proper heading structure
2. **Meta description** (150-160 characters)
3. **Change summary** — what was kept, changed, added, and removed

```
## Change Summary

| Section | Action | Detail |
|---------|--------|--------|
| Intro | Completely rewritten | New hook using [approach] |
| Section 2 | Updated | New data from [source], added example |
| Section 4 | Added | New section on [topic] not in original |
| Section 6 | Removed | Redundant with Section 3 |
```

---

## Phase 4: Polish

### 1. Before/After Comparison

Highlight 2-3 key improvements:

```
## Key Improvements

**1. Intro**
Before: "In today's digital world, content marketing is important..."
After: "We published 47 blog posts last year. Three of them drove 80% of our traffic. Here's what made them different."

**2. [Section name]**
Before: [Brief excerpt]
After: [Brief excerpt]
```

### 2. SEO Improvement Checklist

```
## SEO Checklist

- [ ] Target keyword appears in the H1
- [ ] Keyword in first 100 words
- [ ] Keyword in at least one H2
- [ ] Keyword density between 0.5-1.5%
- [ ] New meta description written (150-160 chars)
- [ ] Heading hierarchy is correct (H1 > H2 > H3)
- [ ] Internal links added or updated
- [ ] Alt text suggestions for any images
- [ ] Word count meets target
```

### 3. Readability Assessment

Compare readability metrics before and after: reading level, average sentence length, passive voice percentage.

---

## Example: Rewriting "10 Email Marketing Tips" from 2022

```
Audit findings:
- Outdated stats (2021 data)
- Generic tips with no examples
- No keyword optimization
- 800 words (too thin for ranking)

Rewrite plan:
- New angle: "10 Email Marketing Tactics That Work in 2025"
- Add specific examples for each tip
- Include 2024-2025 email marketing data
- Expand to 1,800 words with deeper coverage
- Target keyword: "email marketing tactics 2025"
```

---

## Anti-Patterns

- **Synonym swapping** — replacing words with synonyms is not rewriting. It is spinning, and readers and search engines can tell.
- **Keeping the same intro** — the intro is the most important paragraph. If it does not change, the rewrite feels stale.
- **No new value added** — if the rewrite has the same examples, same data, and same structure, it is not worth publishing.
- **Ignoring outdated data** — rewriting around old statistics undermines credibility. Update or remove.
- **Making it longer without making it better** — adding 500 words of fluff to hit a word count hurts quality.

---

## Recovery

- **Original is good but outdated:** Focus the rewrite on data updates, new examples, and SEO fixes. Preserve the structure.
- **Original is poorly written:** Rewrite from scratch using the original as a topic brief, not a template.
- **No new data available:** Substitute with qualitative improvements — better examples, clearer explanations, stronger structure.
- **User wants minimal changes:** Create a "light refresh" — new intro, updated data, improved meta description, better formatting. Flag that light refreshes have limited SEO impact.
- **Rewrite is too similar to original:** Compare paragraphs side-by-side. Any paragraph that is more than 50% similar needs another pass.
