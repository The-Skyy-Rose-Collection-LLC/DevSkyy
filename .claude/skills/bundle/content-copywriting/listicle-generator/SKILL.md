---
name: listicle-generator
description: "Creates engaging listicle articles with consistent entry structure, examples, and SEO optimization. Use when writing numbered list posts like 'Top 10' or 'Best X for Y' articles."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Listicle Generator

## When to Use This Skill

Use this skill when you need to:
- Write a numbered list article (top 5, 10 tips, 7 mistakes, etc.)
- Create a "best of" roundup post optimized for search
- Produce scannable, high-engagement list content for a blog
- Build a listicle with consistent structure across all entries

**DO NOT** use this skill for comparison articles (use comparison-article skill) or unnumbered long-form guides. This is for structured list posts.

---

## Core Principle

EVERY ITEM IN A LISTICLE MUST EARN ITS SPOT — IF AN ENTRY COULD BE CUT WITHOUT THE READER NOTICING, IT SHOULD NOT BE THERE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Topic / list premise** | "What is this list about?" | No default — must be provided |
| **Number of items** | "How many items in the list?" | 7-10 |
| **Target keyword** | "What keyword should this rank for?" | Derived from topic |
| **Audience** | "Who is reading this?" | Solopreneurs and business owners |
| **List type** | "Tips, tools, mistakes, strategies, examples, or resources?" | Tips |
| **Word count** | "Target length?" | 1,500-2,000 words |

**GATE: Confirm brief before building the list.**

---

## Phase 2: Outline

### Listicle Architecture

```
**H1:** [Number] [Things] [About Topic] [Benefit or Hook]

**Intro** (~100-150 words) — Why this list matters

**H2: 1. [Item Title]** (~[words])
**H2: 2. [Item Title]** (~[words])
...
**H2: [N]. [Item Title]** (~[words])

**Bonus / Honorable Mentions** (optional)

**Conclusion + CTA** (~100 words)
```

### Ordering Strategy

Choose one ordering approach:
- **Priority order** — most important first (best for tips/strategies)
- **Ascending impact** — build to the best (best for tools/resources)
- **Logical sequence** — follow a natural progression (best for steps)

**GATE: Approve list items and order before writing.**

---

## Phase 3: Write

### Entry Structure (consistent for every item)

Each list entry follows this format:

```
## [N]. [Item Title]

[1-2 sentence explanation of what this item is and why it matters]

[Concrete example, data point, or actionable instruction — 2-4 sentences]

[Pro tip, caveat, or "how to implement this" — 1-2 sentences]
```

### Writing Rules

| Rule | Detail |
|------|--------|
| **Consistent structure** | Every entry follows the same format — explanation, example, action |
| **Varying length is OK** | Some entries deserve 200 words, others 100 — but stay within 100-300 per entry |
| **Specific over generic** | "Send invoices within 24 hours of project completion" not "Send invoices promptly" |
| **Bold the item title** | Skimmers should get value from scanning just the H2s |
| **H2 for every item** | Each list entry is an H2 — critical for SEO and scannability |
| **No filler entries** | If you cannot write 100 meaningful words about an item, cut it |
| **Intro hooks fast** | 2-3 sentences max before the first list item begins |

### Intro Template

```
[Bold opening — stat, question, or pain point]

[Why this list matters to the reader — 1-2 sentences]

[What they will walk away with — 1 sentence]

Let's dive in.
```

### Conclusion Template

```
## [Wrap-Up / Key Takeaway]

[One sentence summarizing the theme across all items]

[Tell the reader which 1-2 items to implement first]

[CTA — what to do next]
```

---

## Phase 4: Polish

### 1. Listicle Checklist

```
## Pre-Publish Checklist

- [ ] H1 includes the number and target keyword
- [ ] Every list entry follows the same structural format
- [ ] Each entry includes a concrete example or actionable step
- [ ] No filler entries — every item earns its spot
- [ ] H2 headings are descriptive enough to provide value on their own
- [ ] Intro is under 150 words
- [ ] Conclusion recommends where to start
- [ ] Target keyword in H1, first 100 words, and meta description
- [ ] Word count is within 10% of target
- [ ] List order is intentional (priority, ascending, or sequential)
```

### 2. Meta Description

```
[Number] [topic] that [benefit]. From [item example] to [item example] — [audience] guide with actionable tips.
```

### 3. Featured Image Brief

```
Concept: The number [N] prominently displayed with visual icons representing top list items
Dimensions: 1200x630px
Style: Clean, bold, brand colors
```

---

## Example: "7 Invoice Mistakes That Cost Freelancers Money" (1,500 words)

```
H1: 7 Invoice Mistakes That Cost Freelancers Money (And How to Fix Each One)

1. Not Including Payment Terms — leads to "I'll pay when I can" situations
2. Sending Invoices Late — the longer you wait, the longer they wait
3. Using Vague Line Items — "consulting" tells the client nothing
4. Forgetting to Number Your Invoices — makes tracking impossible
5. Not Following Up on Overdue Payments — silence is not a collections strategy
6. Skipping the Late Fee Line — even if you never charge it, it accelerates payment
7. Making It Hard to Pay — no online payment option = delayed payment

Conclusion: Fix #1 and #6 this week — they take 5 minutes and have the biggest impact.
```

---

## Anti-Patterns

- **Filler entries** — padding a "10 tips" list with 3 weak items to hit the number. Better to publish 7 great items than 10 mediocre ones.
- **Inconsistent entry format** — some entries are 50 words, others 400. Keep structure consistent.
- **Generic H2s** — "Tip 3: Communication" tells the reader nothing. "Tip 3: Send a Weekly Status Update Every Monday" is useful on its own.
- **No examples** — abstract advice without concrete examples is forgettable. Every entry needs specificity.
- **Burying the best items** — if the strongest item is #8 of 10, most readers will never see it. Put the best items early (unless building to a climax).
- **Long intros** — listicle readers want the list. Get to item #1 within 150 words.

---

## Recovery

- **Cannot hit the target number:** Lower the number. "5 Essential Tips" beats "10 Tips (5 of which are filler)."
- **All items feel similar:** Differentiate by adding distinct categories (mindset vs tactical vs tools) or merge similar items.
- **Too many items for the word count:** Either cut items or raise the word count. Do not squeeze 15 items into 1,000 words.
- **User wants items they have no expertise on:** Suggest replacing with items they can speak to authentically, or research thoroughly and note sources.
- **List feels obvious:** Add a "Most people miss this" or "Advanced tip" for each item to elevate beyond surface-level advice.
