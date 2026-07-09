---
name: content-gap-finder
description: "Identifies content gaps by analyzing competitor content, search intent mismatches, and audience questions. Use when planning what content to create next based on strategic opportunities."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Content Gap Finder

## When to Use This Skill

Use this skill when you need to:
- Identify topics your competitors cover that you do not
- Find audience questions that have no good content answering them
- Discover search intent mismatches where existing content falls short
- Prioritize your next batch of content based on strategic gaps

**DO NOT** use this skill for keyword research, content auditing (use content-audit skill), or writing content. This is for identifying and prioritizing content opportunities.

---

## Core Principle

A CONTENT GAP IS NOT JUST A MISSING TOPIC — IT IS A MISSED OPPORTUNITY WHERE YOUR AUDIENCE IS LOOKING FOR ANSWERS AND FINDING NOTHING (OR NOTHING GOOD).

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Your website / content** | "Share your website URL or a list of your published content." | No default — must be provided |
| **Competitors** | "List 3-5 competitors or similar brands in your space." | No default — must be provided |
| **Target audience** | "Who are you creating content for?" | Solopreneurs and business owners |
| **Business goals** | "What should your content drive? Traffic, leads, sales, authority?" | Organic traffic and leads |
| **Content channels** | "Where do you publish? Blog, YouTube, podcast, social?" | Blog |

**GATE: Confirm brief before analysis.**

---

## Phase 2: Analysis Framework

### Gap Categories

Analyze across five gap types:

```
1. **Topic gaps** — topics competitors cover that you do not
2. **Depth gaps** — topics you cover but not deeply enough
3. **Format gaps** — topics covered in text but not video (or vice versa)
4. **Audience gaps** — content that serves one segment but ignores another
5. **Intent gaps** — content that targets informational queries but misses commercial/transactional intent
```

**GATE: Confirm analysis scope before full report.**

---

## Phase 3: Write

### Gap Analysis Report

#### 1. Topic Gaps

```
## Topics Your Competitors Cover That You Don't

| # | Topic | Competitor Covering It | Search Intent | Priority |
|---|-------|----------------------|---------------|----------|
| 1 | [Topic] | [Competitor A, B] | [Informational/Commercial] | High |
| 2 | [Topic] | [Competitor A] | [Informational] | Medium |
...
```

For each high-priority gap:
```
### Gap: [Topic]

**Why it matters:** [1-2 sentences on audience demand and business relevance]
**Competitor coverage:** [What competitors have published and what quality level]
**Your opportunity:** [How to cover this better — angle, format, depth]
**Suggested content:** "[Working title]" — [format] — [estimated word count/length]
**Target keyword:** [Primary keyword suggestion]
```

#### 2. Depth Gaps

```
## Topics You Cover but Not Deeply Enough

| Your Content | What's Missing | Competitor's Better Version | Action |
|-------------|----------------|---------------------------|--------|
| [Your post title] | [Missing element] | [Competitor post] | Update / Expand |
```

#### 3. Format Gaps

```
## Format Opportunities

| Topic | You Have | You're Missing | Opportunity |
|-------|---------|---------------|-------------|
| [Topic] | Blog post | Video explainer | Create a companion video |
| [Topic] | Nothing | Competitor has a podcast episode | Create a blog post + video |
```

#### 4. Audience Gaps

```
## Underserved Audience Segments

| Segment | What They Need | What You Have | Gap |
|---------|---------------|---------------|-----|
| [Segment, e.g., beginners] | [Content need] | [Nothing / too advanced] | [Specific content to create] |
```

#### 5. Content Priority Matrix

```
## Priority Matrix

| Priority | Topic | Type | Effort | Potential Impact |
|----------|-------|------|--------|-----------------|
| 1 | [Topic] | New content | Medium | High (competitor gap + search volume) |
| 2 | [Topic] | Update existing | Low | High (depth gap on top-performing page) |
| 3 | [Topic] | New format | Medium | Medium (video for popular blog post) |
...
```

---

## Phase 4: Polish

### 1. Gap Analysis Checklist

```
## Checklist

- [ ] At least 3 competitors analyzed
- [ ] Topic gaps identified with priority ratings
- [ ] Depth gaps flagged with specific missing elements
- [ ] Format gaps noted where applicable
- [ ] Each high-priority gap has a suggested content piece
- [ ] Priority matrix ranks all opportunities by effort vs impact
- [ ] Recommendations are specific (title, format, target keyword)
- [ ] Analysis connects gaps to business goals (traffic, leads, sales)
```

### 2. 90-Day Content Roadmap

Based on the gaps, suggest a 90-day plan:
- Month 1: Address the top 3 highest-impact gaps
- Month 2: Update depth gaps on existing content
- Month 3: Experiment with new formats and audience segments

---

## Example: Gap Analysis for a Freelance Business Blog

```
Competitor blogs analyzed: Freelancers Union, Millo, Careful Cents

Topic gaps found:
1. "Freelance contract templates" — 3 competitors cover it, you don't → High priority
2. "How to fire a client" — 2 competitors, high engagement → Medium priority
3. "Freelance tax deductions guide" — seasonal topic, no competitor does it well → High priority

Depth gaps:
- Your "Freelance Pricing Guide" is 800 words. Top competitor's is 3,200 with examples and a calculator. Update to 2,500+ words with tools and templates.

Priority #1: Create "Freelance Contract Templates (Free Downloads)" — high search volume, no existing content, strong lead magnet potential.
```

---

## Anti-Patterns

- **Copying competitors** — the goal is to identify gaps, not replicate competitor content. Cover the topic better, not the same.
- **Chasing every gap** — not every gap is worth filling. Prioritize by business impact, not completeness.
- **Ignoring depth gaps** — sometimes the biggest opportunity is improving existing content, not creating new pieces.
- **No prioritization** — a list of 50 gaps without a priority framework is overwhelming and useless.
- **Assuming gaps mean demand** — a competitor covering a topic does not prove your audience cares. Validate demand before creating.

---

## Recovery

- **No competitor data available:** Analyze audience questions from forums, social media, and "People Also Ask" results instead.
- **Too many gaps identified:** Narrow to the top 10 by applying the effort-vs-impact filter. Focus on high-impact, low-effort gaps first.
- **All gaps are high-effort:** Look for "quick win" depth gaps — updating existing content is almost always lower effort than creating new pieces.
- **User's niche has few competitors:** Expand the competitor list to include adjacent niches or larger industry publications.
- **No existing content to compare:** Start with the top 20 questions your audience asks and check whether any competitor answers them well.
