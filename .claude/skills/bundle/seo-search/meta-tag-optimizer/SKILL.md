---
name: meta-tag-optimizer
description: "Optimizes title tags and meta descriptions for a batch of pages with character counts and CTR optimization. Use when improving your site's search appearance."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Meta Tag Optimizer

## When to Use This Skill

Use this skill when you need to:
- Optimize title tags and meta descriptions across multiple pages
- Improve click-through rates from search engine results pages
- Audit existing meta tags for length, keyword inclusion, and effectiveness
- Batch-write meta tags for new or under-optimized pages

**DO NOT** use this skill for on-page content optimization, technical SEO audits, or schema markup. This is specifically for title tags and meta descriptions.

---

## Core Principle

TITLE TAGS AND META DESCRIPTIONS ARE YOUR AD COPY IN SEARCH RESULTS — THEY MUST INCLUDE THE TARGET KEYWORD, FIT THE CHARACTER LIMITS, AND MAKE SEARCHERS CHOOSE YOUR RESULT OVER THE OTHERS.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Pages to optimize** | "List the pages (URLs or titles) that need meta tag optimization." | No default — must be provided |
| **Target keywords** | "What keyword should each page target?" | No default — must be provided |
| **Brand name** | "What is your brand name for title tag formatting?" | Business name |
| **Title format preference** | "Do you append your brand name to title tags?" | Yes — "Page Title | Brand Name" |
| **Current meta tags** | "Can you share the existing title tags and meta descriptions?" | Will audit if URLs provided |

**GATE: Confirm the page list and keywords before optimizing.**

---

## Phase 2: Meta Tag Audit

### Current State Assessment

For each page, evaluate:

```
## Meta Tag Audit

| Page | Current Title | Chars | Current Description | Chars | Issues |
|------|--------------|-------|--------------------|----|--------|
| [Page 1] | [Title] | [X] | [Description] | [X] | [Issues] |
| [Page 2] | [Title] | [X] | [Description] | [X] | [Issues] |
```

### Common Issues to Flag

- Title over 60 characters (gets truncated)
- Title under 30 characters (misses ranking potential)
- Meta description over 160 characters (gets truncated)
- Meta description under 120 characters (wastes SERP space)
- Missing target keyword in title
- Missing target keyword in description
- Duplicate titles across pages
- Generic descriptions ("Welcome to our website")
- No CTA or benefit in description

**GATE: Present the audit before writing optimized versions.**

---

## Phase 3: Write Optimized Meta Tags

### Title Tag Rules

- **Length:** 50-60 characters (hard limit: 60 to avoid truncation)
- **Keyword placement:** Target keyword as close to the beginning as possible
- **Brand name:** Append at the end with a pipe separator (| Brand Name)
- **Format:** [Primary Keyword Phrase] — [Benefit or Modifier] | Brand
- **Uniqueness:** Every page gets a unique title tag

### Meta Description Rules

- **Length:** 150-160 characters (hard limit: 160)
- **Keyword inclusion:** Target keyword appears naturally (Google bolds it)
- **Structure:** [Hook/benefit] + [What the page covers] + [CTA or value prop]
- **Action words:** Use "Learn," "Discover," "Get," "Find out" — not passive language
- **No quotes or special characters** that might cause truncation

### Output Format

```
## Optimized Meta Tags

### Page: [Page Name/URL]
**Target keyword:** [keyword]

**Title tag (XX chars):**
[Optimized title tag here]

**Meta description (XXX chars):**
[Optimized meta description here]

**Notes:** [Any specific recommendations]

---

### Page: [Next Page]
...
```

### Before/After Examples

Show the improvement for at least 2-3 pages:

```
**Before:** Home | My Company Website (27 chars — too short, no keyword)
**After:** Email Marketing Tools for Small Business | [Brand] (52 chars)

**Before:** We offer many great services for your business needs (too generic, 52 chars)
**After:** Save 10+ hours/week with email automation tools built for solopreneurs. Free trial available. (93 chars — add more)
```

---

## Phase 4: Polish

### 1. Implementation Checklist

- [ ] All title tags under 60 characters
- [ ] All meta descriptions between 150-160 characters
- [ ] Every page has a unique title and description
- [ ] Target keyword present in every title
- [ ] Target keyword present in every description
- [ ] No duplicate meta tags across the site
- [ ] Brand name consistently formatted

### 2. CTR Optimization Tips

- Use numbers when possible ("7 Ways to..." or "Save $500")
- Use current year for time-sensitive content ("2026 Guide")
- Test parenthetical additions: (Free Template) (Step-by-Step) (With Examples)
- Analyze Search Console CTR data monthly — low CTR + high impressions = rewrite the meta tags

### 3. Ongoing Process

- Review meta tags for top 20 pages monthly
- Update title tags when targeting changes
- Refresh descriptions seasonally or when offers change
- Check Google Search Console for pages with high impressions but low CTR

---

## Anti-Patterns

- **Keyword stuffing in titles** — "Email Marketing Email Tools Email Software" is unreadable and hurts rankings.
- **Same meta description on every page** — duplicate descriptions are treated as missing descriptions by Google.
- **Writing for search engines, not humans** — the meta description must make a human want to click, not just contain keywords.
- **Ignoring mobile truncation** — mobile SERPs show fewer characters. Front-load the most important words.
- **Set and forget** — meta tags should be reviewed and updated as keyword strategies evolve.

---

## Recovery

- **Hundreds of pages to optimize:** Prioritize by traffic and impressions. Start with the top 20 pages in Google Search Console.
- **No target keywords defined:** Run keyword research first. Each page needs a primary keyword before meta tags can be optimized.
- **Google rewrites your meta tags:** Google sometimes generates its own snippets. Ensure your tags accurately reflect page content — this reduces rewrites.
- **CMS doesn't support custom meta tags:** Recommend Yoast SEO (WordPress) or similar plugins that add meta tag fields to every page.
