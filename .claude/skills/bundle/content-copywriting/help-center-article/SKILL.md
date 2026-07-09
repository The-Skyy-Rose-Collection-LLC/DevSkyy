---
name: help-center-article
description: "Writes help center articles with step-by-step instructions, screenshot placeholders, and troubleshooting sections for customer self-service."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Help Center Article

## When to Use This Skill

Use this skill when you need to:
- Write a customer-facing help center or knowledge base article
- Create step-by-step instructions with screenshot placeholders
- Build troubleshooting guides for common customer issues
- Reduce support ticket volume by enabling self-service

**DO NOT** use this skill for internal SOPs (use knowledge-base-builder), blog posts, or support response templates. This is for customer-facing self-service documentation.

---

## Core Principle

A HELP CENTER ARTICLE SHOULD ANSWER THE CUSTOMER'S QUESTION WITHOUT THEM NEEDING TO CONTACT SUPPORT — IF THEY STILL NEED TO EMAIL YOU AFTER READING IT, THE ARTICLE FAILED.

---

## Phase 1: Article Brief

Define what the article will cover and for whom.

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Topic** | "What question or task does this article address?" | No default |
| **Audience** | "What is the customer's technical skill level?" | Beginner-friendly |
| **Article type** | "Is this a how-to, troubleshooting guide, FAQ, or conceptual explainer?" | How-to |
| **Related articles** | "Are there any related articles to link to?" | None |
| **Common mistakes** | "What do customers get wrong most often with this?" | No default |

**GATE: Confirm the article brief before writing.**

---

## Phase 2: Write Article

Create the article following help center best practices.

### How-To Article Template

```
# How to [Task Name]

**Last updated:** [Date]
**Applies to:** [Plan level / product version / user role]
**Time required:** [X minutes]

## Overview

[1-2 sentences: what this article covers and the end result]

## Before You Start

- [Prerequisite 1 — what the customer needs before beginning]
- [Prerequisite 2]

## Steps

### Step 1: [Action]

[1-2 sentences of instruction]

[Screenshot: Description of what the customer should see]

### Step 2: [Action]

[1-2 sentences of instruction]

[Screenshot: Description of what the customer should see]

### Step 3: [Action]

[1-2 sentences of instruction]

**Result:** [What the customer should see when they complete this step]

## Troubleshooting

### [Common problem 1]

**Symptom:** [What the customer sees]
**Cause:** [Why it happens]
**Fix:** [Step-by-step solution]

### [Common problem 2]

**Symptom:** [What the customer sees]
**Fix:** [Solution]

## Related Articles

- [Article title and link]
- [Article title and link]

## Still Need Help?

If these steps did not resolve your issue, [contact support link] and include:
- [Info to include: screenshots, error messages, account details]
```

### Troubleshooting Guide Template

```
# Troubleshooting: [Issue Name]

## Quick Fixes

Try these first (most issues resolve here):

1. [Quick fix 1 — e.g., "Clear your browser cache and refresh"]
2. [Quick fix 2 — e.g., "Log out and log back in"]
3. [Quick fix 3]

## Detailed Solutions

### If you see [Error/Symptom A]

**Cause:** [Explanation]
**Fix:**
1. [Step]
2. [Step]

### If you see [Error/Symptom B]

**Cause:** [Explanation]
**Fix:**
1. [Step]
2. [Step]

## Still Not Working?

Contact support at [link] with:
- What you were trying to do
- The exact error message (screenshot preferred)
- Your browser and device type
```

**GATE: Present the article draft for review.**

---

## Phase 3: Optimize

Improve the article for findability and usability.

### SEO and Search Optimization

- **Title:** Use the exact words customers would search for
- **Meta description:** Summarize the answer in 1 sentence
- **Tags/categories:** Add relevant tags for internal search

### Readability Checklist

```
- [ ] Title matches what a customer would type into a search bar
- [ ] Steps are numbered and each step has ONE action
- [ ] Screenshots (or placeholders) show what the customer should see
- [ ] No jargon — if a technical term is necessary, define it
- [ ] Article is under 500 words (longer articles should be split)
- [ ] Troubleshooting section covers the top 2-3 issues
- [ ] "Still need help?" section includes clear contact path
- [ ] Related articles are linked for deeper exploration
```

### Writing Rules

- Use "you" language: "Click the Settings button" not "The user should click Settings"
- One action per step — never combine two actions in one step
- Bold the clickable element: "Click **Save Changes**"
- Use present tense: "The page displays..." not "The page will display..."
- Include what success looks like: "You should see a green confirmation message"

---

## Phase 4: Maintain

Keep articles accurate and relevant.

### Maintenance Triggers

Update the article when:
- The product UI changes
- A new feature affects the workflow
- Support tickets reference this article with confusion
- Screenshots become outdated

### Performance Metrics

```
| Metric | Target | Current |
|--------|--------|---------|
| Article views per month | Trending up | — |
| Support tickets on this topic | Trending down | — |
| Article helpfulness rating | 80%+ positive | — |
| Average time on article | 1-3 minutes | — |
```

---

## Anti-Patterns

- **Wall of text without steps** — customers scan, they do not read paragraphs. Use numbered steps and headers.
- **Assuming knowledge** — "Navigate to the API settings" assumes the customer knows what an API is and where to find it.
- **Outdated screenshots** — nothing erodes trust faster than instructions that do not match what the customer sees.
- **Burying the answer** — put the most common solution first. Do not make customers read 500 words to find a 1-sentence fix.
- **No escape hatch** — every article needs a "Still need help? Contact us" at the bottom.

---

## Recovery

- **Customers still contact support about a documented topic:** The article is hard to find, hard to understand, or missing a common scenario. Review and revise.
- **User has no screenshots yet:** Use description placeholders: `[Screenshot: The Settings page with the "Billing" tab highlighted]`. Add actual screenshots later.
- **Article is too long:** Split into multiple articles. A how-to and a troubleshooting guide are better as two articles than one mega-article.
- **User does not know what to document first:** Start with the top 5 support ticket topics. Each one becomes an article.
- **Help center gets no traffic:** Link to relevant articles in onboarding emails, support responses, and product UI.
