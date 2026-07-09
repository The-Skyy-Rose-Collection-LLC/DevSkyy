---
name: comparison-article
description: "Writes 'X vs Y' comparison articles with feature tables, pros/cons, use cases, and recommendation logic. Use when creating product or service comparison content for SEO or buyer guidance."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Comparison Article

## When to Use This Skill

Use this skill when you need to:
- Write an "X vs Y" comparison article for two products, tools, or approaches
- Create a multi-option comparison ("Best X for Y" format)
- Produce buyer-intent content that ranks for comparison search queries
- Build feature tables, pros/cons lists, and recommendation sections

**DO NOT** use this skill for reviews of a single product or listicles of unrelated tools. This is for head-to-head or multi-option comparisons.

---

## Core Principle

A COMPARISON ARTICLE MUST HELP THE READER MAKE A DECISION — NOT JUST LIST FEATURES. EVERY SECTION SHOULD MOVE THEM CLOSER TO CHOOSING.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Items to compare** | "What are you comparing? (e.g., ConvertKit vs Mailchimp)" | No default — must be provided |
| **Comparison type** | "Head-to-head (X vs Y) or multi-option roundup?" | Head-to-head |
| **Target keyword** | "What search query should this rank for?" | "[Item A] vs [Item B]" |
| **Audience** | "Who is choosing between these options?" | Solopreneurs and small business owners |
| **Author's recommendation** | "Do you have a preferred winner, or should this be neutral?" | Neutral with use-case recommendations |
| **Word count** | "Target length?" | 2,000-2,500 words |

**GATE: Confirm brief before building comparison framework.**

---

## Phase 2: Outline

### Comparison Article Structure

```
**H1:** [Item A] vs [Item B]: [Differentiating angle or audience]

**Quick Verdict** (~100 words) — TL;DR recommendation at the top

**H2: Overview** (~200 words)
- Brief intro to both options and why people compare them

**H2: [Comparison Criteria 1]** (~300 words)
- [Item A analysis]
- [Item B analysis]
- [Winner for this criteria]

**H2: [Comparison Criteria 2]** (~300 words)
...

**H2: Feature Comparison Table**
- Side-by-side feature matrix

**H2: Pricing Comparison** (~200 words)

**H2: Who Should Choose [Item A]** (~150 words)
**H2: Who Should Choose [Item B]** (~150 words)

**H2: Final Verdict** (~150 words)
```

**GATE: Approve outline and comparison criteria before writing.**

---

## Phase 3: Write

### Quick Verdict (top of article)

Place a summary verdict BEFORE the detailed comparison:

```
> **Quick verdict:** [Item A] is better for [use case]. [Item B] is better for [use case]. If you [specific situation], go with [recommendation]. Read on for the detailed breakdown.
```

### Comparison Criteria Sections

For each criteria (pricing, ease of use, features, support, etc.):

1. **What matters** — why this criteria matters for the reader's decision
2. **Item A** — how it performs on this criteria (with specifics)
3. **Item B** — how it performs on this criteria (with specifics)
4. **Winner** — clear verdict for this category with reasoning

### Feature Comparison Table

```
| Feature | [Item A] | [Item B] |
|---------|----------|----------|
| [Feature 1] | [Yes/No/Detail] | [Yes/No/Detail] |
| [Feature 2] | [Detail] | [Detail] |
| Pricing | [Starting price] | [Starting price] |
| Best for | [Use case] | [Use case] |
```

### Use-Case Recommendations

End with clear, situation-based recommendations:

```
## Choose [Item A] if you:
- [Specific situation 1]
- [Specific situation 2]
- [Specific situation 3]

## Choose [Item B] if you:
- [Specific situation 1]
- [Specific situation 2]
- [Specific situation 3]
```

### Writing Rules

| Rule | Detail |
|------|--------|
| **Be specific** | "ConvertKit starts at $29/mo for 1,000 subscribers" not "ConvertKit is affordable" |
| **Name winners** | Each criteria section must declare a winner (ties are allowed with explanation) |
| **Use screenshots/callouts** | Mark where screenshot comparisons should appear |
| **Disclose bias** | If the author uses one product, say so upfront |
| **Link to both** | Include links to both options (affiliate or direct) |

---

## Phase 4: Polish

### 1. Comparison Checklist

```
## Pre-Publish Checklist

- [ ] Quick verdict appears at the top of the article
- [ ] Each comparison criteria names a winner
- [ ] Feature comparison table is included
- [ ] Pricing information is current and specific
- [ ] Use-case recommendations are clear ("Choose X if you...")
- [ ] Final verdict is decisive (not wishy-washy)
- [ ] SEO: keyword in H1, first 100 words, and meta description
- [ ] All facts and pricing are accurate as of publish date
- [ ] Affiliate or bias disclosure is included if applicable
- [ ] Article helps the reader decide, not just compare
```

### 2. Meta Description

```
[Item A] vs [Item B] — which is right for you? We compare [criteria] to help [audience] choose. [Quick verdict hint].
```

### 3. Update Note

Include a "Last updated: [date]" note at the top. Recommend quarterly price and feature accuracy checks.

---

## Example: "ConvertKit vs Mailchimp for Solopreneurs" (2,200 words)

```
Quick verdict: ConvertKit wins for creators selling digital products.
Mailchimp wins for e-commerce businesses sending promotional emails.

Comparison criteria:
1. Ease of use — Winner: Mailchimp (simpler interface)
2. Email automation — Winner: ConvertKit (visual automation builder)
3. Landing pages — Winner: ConvertKit (built for lead gen)
4. Pricing — Winner: Mailchimp (free tier is more generous)
5. Deliverability — Winner: ConvertKit (better inbox placement rates)
6. Integrations — Tie

Choose ConvertKit if: you sell courses, coaching, or digital products
Choose Mailchimp if: you run an e-commerce store or need a free plan
```

---

## Anti-Patterns

- **No clear winners** — "Both are great!" helps nobody decide. Name a winner for each criteria or explain the tie.
- **Feature-listing without context** — "ConvertKit has automation" is useless. "ConvertKit's visual automation builder lets you create a 5-email welcome sequence in 10 minutes" is useful.
- **Outdated pricing** — nothing kills credibility faster. Verify pricing before publishing.
- **Hidden bias** — if you are an affiliate or use one product, disclose it. Readers spot hidden bias.
- **No use-case recommendations** — features do not help readers decide. Use cases do.
- **Wall-of-text comparisons** — tables and bullet points make comparisons scannable. Use them.

---

## Recovery

- **User wants a biased comparison:** Write it with a clear recommendation but still present the other option fairly. Disclose the bias.
- **Products are very similar:** Focus comparison on the 2-3 differences that actually matter for the target audience.
- **Pricing changes frequently:** Include pricing with a "Last verified: [date]" note and recommend quarterly updates.
- **More than 2 items to compare:** Switch to a roundup format with a comparison table and a "Best for [use case]" winner for each category.
- **No personal experience with the products:** Research thoroughly and caveat with "Based on published documentation and user reviews." Do not fake firsthand experience.
