---
name: featured-snippet-optimizer
description: "Optimizes content to win featured snippets with format analysis, answer structure, and formatting. Use when targeting position zero in Google search results."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Featured Snippet Optimizer

## When to Use This Skill

Use this skill when you need to:
- Optimize existing content to win featured snippets (position zero)
- Analyze which snippet format Google prefers for a target query
- Structure answers in paragraph, list, or table format for snippet extraction
- Identify featured snippet opportunities across your content

**DO NOT** use this skill for general SEO content writing, meta tag optimization, or link building. This is specifically for formatting content to capture featured snippets.

---

## Core Principle

FEATURED SNIPPETS ANSWER THE QUESTION DIRECTLY, CONCISELY, AND IN THE FORMAT GOOGLE PREFERS — STRUCTURE YOUR CONTENT TO BE THE EASIEST ANSWER FOR GOOGLE TO EXTRACT.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Target queries** | "What questions do you want to win snippets for?" | No default — must be provided |
| **Existing content** | "Do you have published content targeting these queries?" | Yes — URL(s) provided |
| **Current ranking** | "Where do you currently rank for these queries?" | Page 1 or 2 |
| **Content type** | "What format is your content? (blog, FAQ, guide)" | Blog post |

**GATE: Confirm target queries before analyzing snippet opportunities.**

---

## Phase 2: Snippet Analysis

### Current SERP Assessment

For each target query, document:

```
## Snippet Opportunity Analysis

**Query:** [Target question]
**Current snippet holder:** [URL / "No snippet currently"]
**Snippet format:** Paragraph / Numbered list / Bulleted list / Table
**Your current position:** [X]

**Snippet eligibility:** High / Medium / Low
- High: You rank on page 1 and the query has a clear answer format
- Medium: You rank on page 1-2, snippet exists but is weak
- Low: You don't rank top 20 or the query rarely triggers snippets
```

### Snippet Format Patterns

```
## Format Selection Guide

**Paragraph snippets** (40-50 words) work best for:
- "What is..." definitions
- "Why does..." explanations
- Single-answer factual questions

**Numbered list snippets** work best for:
- "How to..." step-by-step processes
- "Steps to..." procedures
- Ranked lists

**Bulleted list snippets** work best for:
- "Types of..." or "Examples of..."
- Lists of tips, features, or items
- Unranked collections

**Table snippets** work best for:
- Comparisons (X vs Y)
- Pricing or specification data
- Schedules or structured data
```

**GATE: Present the analysis and confirm which queries to optimize for.**

---

## Phase 3: Optimize Content

### Paragraph Snippet Optimization

```
## Structure for Paragraph Snippets

**Step 1:** Use the exact query as an H2 or H3 heading
Example: "## What Is Email Marketing?"

**Step 2:** Immediately below the heading, answer in 40-50 words
Example: "Email marketing is the practice of sending targeted messages
to a subscriber list to build relationships, promote products, and
drive conversions. It remains one of the highest-ROI marketing channels,
generating an average return of $36 for every $1 spent."

**Step 3:** Follow with expanded explanation, examples, and depth
```

### List Snippet Optimization

```
## Structure for List Snippets

**Step 1:** Use the query as a heading
Example: "## How to Set Up an Email List"

**Step 2:** Immediately follow with a numbered or bulleted list
Example:
1. Choose an email service provider
2. Create a signup form
3. Add the form to your website
4. Set up a welcome email
5. Drive traffic to the signup form

**Step 3:** Expand each item below the list with 2-3 sentences of detail
```

### Table Snippet Optimization

```
## Structure for Table Snippets

**Step 1:** Use a comparison heading
Example: "## Email Marketing Platforms Compared"

**Step 2:** Create a clean HTML/Markdown table
| Platform | Price | Best For |
|----------|-------|----------|
| ConvertKit | $29/mo | Creators |
| Mailchimp | $13/mo | Small business |

**Step 3:** Add context paragraphs above or below the table
```

### Content Restructuring Recommendations

For each target query, provide:
1. Exact heading to use
2. Optimized answer text (snippet-ready)
3. Where to place it in the existing content
4. Additional supporting content to add

---

## Phase 4: Polish

### 1. Implementation Checklist

- [ ] Query used as exact H2/H3 heading
- [ ] Answer immediately follows the heading (no preamble)
- [ ] Answer is the right length (40-50 words for paragraph, 5-8 items for list)
- [ ] Answer is factually accurate and self-contained
- [ ] Supporting content provides depth beyond the snippet
- [ ] Content published and submitted for re-indexing

### 2. People Also Ask Opportunities

List related PAA questions that appear for each target query — these are additional snippet opportunities within the same content.

### 3. Monitoring

- Track snippet ownership weekly for target queries
- If snippet is lost, check: did the ranking drop? Did Google change the format preference? Did a competitor optimize better?
- Featured snippets can flip frequently — continued content quality is the best defense

---

## Anti-Patterns

- **Targeting snippets you don't rank for** — you generally need to rank in the top 10 to be considered for a snippet. Rankings first, snippets second.
- **Over-optimizing the answer** — unnaturally stuffing keywords into the snippet answer makes it sound robotic and less likely to be selected.
- **Wrong format** — providing a paragraph answer when Google wants a list wastes the optimization effort.
- **Too long or too short** — paragraph snippets over 60 words get truncated. Lists over 8 items get "More items..." which can work but is less clean.
- **No supporting content** — a page with only a snippet-length answer is thin content. The snippet is the hook; the page must deliver depth.

---

## Recovery

- **Not ranking on page 1:** Focus on improving overall rankings before snippet optimization. You need to be in the top 10 first.
- **Snippet keeps going to a competitor:** Analyze their format and structure. Match or beat their snippet answer quality, and ensure your page has superior depth.
- **Google stopped showing a snippet for the query:** Some queries lose their snippet over time. Shift focus to other snippet opportunities.
- **Multiple pages competing for the same snippet:** Consolidate content into one authoritative page to avoid cannibalization.
