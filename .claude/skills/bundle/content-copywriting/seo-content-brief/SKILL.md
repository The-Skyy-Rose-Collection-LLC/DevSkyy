---
name: seo-content-brief
description: "Writes SEO content briefs with target keywords, competitor analysis, SERP feature opportunities, and outline structure. Use when assigning content to writers."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# SEO Content Brief

## When to Use This Skill

Use this skill when you need to:
- Create a detailed content brief for a writer or yourself before drafting
- Analyze the current SERP to identify content gaps and opportunities
- Define target keywords, word count, structure, and optimization targets
- Provide a clear blueprint that produces SEO-optimized content without guesswork

**DO NOT** use this skill for writing the actual content (use blog-post skill), keyword research (use keyword-research skill), or technical SEO audits. This is for the brief that precedes content creation.

---

## Core Principle

A GREAT BRIEF ELIMINATES GUESSWORK — THE WRITER SHOULD KNOW EXACTLY WHAT TO WRITE, WHO TO WRITE FOR, AND WHAT SUCCESS LOOKS LIKE BEFORE TYPING A SINGLE WORD.

---

## Phase 1: Brief Inputs

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Target keyword** | "What keyword should this content rank for?" | No default — must be provided |
| **Secondary keywords** | "Any related keywords to include?" | Will suggest 3-5 |
| **Business context** | "What does your business do and how does this content fit?" | General context |
| **Target audience** | "Who is reading this?" | Your target customer |
| **Content goal** | "What should the reader do after reading?" | Engage with your business |
| **Existing content** | "Do you have related content to link to?" | None |

**GATE: Confirm inputs before building the brief.**

---

## Phase 2: SERP Analysis

### Analyze Current Rankings

For the target keyword, assess the top 5-10 results:

```
## SERP Analysis

**Current Page 1 Results:**
| Position | Title | Domain | Type | Word Count | Gaps |
|----------|-------|--------|------|-----------|------|
| 1 | [Title] | [Domain] | [Guide/List/How-to] | ~[X] | [What's missing] |
| 2 | [Title] | [Domain] | [Type] | ~[X] | [Gap] |
| ... | | | | | |

**SERP Features Present:**
- [ ] Featured snippet (paragraph / list / table)
- [ ] People Also Ask
- [ ] Video results
- [ ] Image pack
- [ ] Local pack

**Content Gap Analysis:**
- What questions are NOT answered well by current results?
- What angles are missing?
- What depth or specificity could you add?
```

### Competitive Insight Summary

```
## What Competitors Do Well
- [Strength 1]
- [Strength 2]

## Where Competitors Fall Short
- [Gap 1 — your opportunity]
- [Gap 2 — your opportunity]

## Your Angle
[How to differentiate from what's already ranking]
```

**GATE: Review the SERP analysis before building the content outline.**

---

## Phase 3: Content Brief Document

### The Brief

```
## Content Brief: [Target Keyword]

**Target keyword:** [Primary keyword]
**Secondary keywords:** [3-5 related terms]
**Search intent:** [Informational / Commercial / Transactional]
**Content type:** [How-to guide / Listicle / Comparison / Deep dive]
**Target word count:** [X]-[Y] words
**Target audience:** [Who and what they care about]
**Unique angle:** [What makes this piece different from existing results]

---

### Outline

**H1:** [Title with target keyword]

**H2:** [Section 1] (~[X] words)
- Cover: [Key points]
- Include: [Data, example, or resource]

**H2:** [Section 2] (~[X] words)
  **H3:** [Subtopic A]
  **H3:** [Subtopic B]

[Continue for all sections...]

---

### SEO Requirements

- Target keyword in H1, first 100 words, and at least 1 H2
- Secondary keywords sprinkled naturally through body
- Meta description: 150-160 characters with keyword and CTA
- Internal links: [Specific pages to link to]
- External links: Cite 2-3 authoritative sources
- Image alt text: Include keyword variant in at least one image

### SERP Feature Targets

- Featured snippet opportunity: [Question to answer in snippet format]
- People Also Ask: [3-5 questions to address in the content]

### What NOT to Do

- Do not [specific thing to avoid based on competitor analysis]
- Do not [content pitfall for this topic]
- Do not exceed [word count] — longer is not always better

### Success Metrics

- Ranking on page 1 for target keyword within 90 days
- [X]+ organic visits per month within 6 months
- [Conversion action]: [X]% of readers take next step
```

---

## Phase 4: Polish

### 1. Writer Instructions

Add any style, tone, or formatting guidance specific to the brand or publication.

### 2. Reference Materials

List URLs, studies, or resources the writer should consult during drafting.

### 3. Review Criteria

Checklist for the editor or reviewer to evaluate the draft against the brief.

---

## Anti-Patterns

- **Brief with no outline** — "Write 2,000 words about email marketing" is not a brief. Structure is the entire point.
- **Ignoring the SERP** — writing without analyzing what's already ranking means you're guessing at format, depth, and angle.
- **Over-specifying every sentence** — a brief guides structure and strategy. If you dictate every paragraph, you might as well write it yourself.
- **No unique angle** — if the brief produces content that looks like every other result, it will not outrank them.
- **Targeting unrealistic keywords** — a brief for a keyword your site cannot rank for wastes the writer's time and your budget.

---

## Recovery

- **No SERP tools available:** Manually review top 5 Google results. Note titles, headings, word count estimates, and missing topics.
- **Writer doesn't follow the brief:** Add a "mandatory checklist" section where the writer confirms each requirement before submitting.
- **Multiple keywords, unsure which to target:** Pick the keyword with the best combination of relevance, rankability, and volume. Create separate briefs for separate keywords.
- **Content already exists on the site:** Assess whether to update the existing page or create new content. Avoid keyword cannibalization.
