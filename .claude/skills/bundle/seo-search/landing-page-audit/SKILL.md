---
name: landing-page-audit
description: "Audits landing pages for conversion optimization with layout, copy, social proof, and CTA recommendations. Use when you need to improve a landing page's conversion rate or identify why a page is underperforming."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Landing Page Audit

## When to Use This Skill

Use this skill when you need to:
- Audit an existing landing page for conversion optimization opportunities
- Identify why a landing page has a low conversion rate
- Get actionable recommendations to improve layout, copy, social proof, and CTAs
- Prepare a structured audit report for a client or team

**DO NOT** use this skill for full website audits, SEO audits, or building a new landing page from scratch. This is specifically for evaluating and improving an existing landing page.

---

## Core Principle

EVERY RECOMMENDATION MUST TIE DIRECTLY TO A CONVERSION OUTCOME — NEVER SUGGEST CHANGES FOR AESTHETIC REASONS ALONE.

---

## Phase 1: Page Intake

Before auditing, gather the information needed to evaluate the page in context.

### Required Inputs

Ask the user for each of these. If they do not provide one, use the default.

| Input | What to Ask | Default |
|-------|------------|---------|
| **Page URL or content** | "Share the landing page URL or paste the HTML/copy." | No default — must be provided |
| **Page goal** | "What is the single conversion action? (buy, sign up, book a call, download)" | Lead capture (email opt-in) |
| **Target audience** | "Who is this page designed for?" | Small business owners and solopreneurs |
| **Traffic source** | "Where does most traffic come from? (ads, organic, email, social)" | Paid ads |
| **Current conversion rate** | "What is the current conversion rate, if known?" | Unknown |

**GATE: Do not proceed until the user provides the page content or URL and confirms the goal.**

---

## Phase 2: Audit Framework

Evaluate the landing page across these five pillars. Score each 1-10 and provide specific findings.

### 1. Above-the-Fold Impact (First Screen)

- **Headline clarity:** Does it communicate the offer in under 5 seconds?
- **Value proposition:** Is the benefit obvious without scrolling?
- **Visual hierarchy:** Does the eye flow naturally to the CTA?
- **Hero image/video:** Does it support the message or distract?
- **CTA visibility:** Is there a clear, visible call-to-action above the fold?

### 2. Copy and Messaging

- **Headline-ad match:** Does the page headline match the traffic source promise?
- **Benefit vs. feature ratio:** Are benefits leading, with features supporting?
- **Specificity:** Are claims backed by numbers, timeframes, or concrete outcomes?
- **Objection handling:** Does the copy address the top 3 buying objections?
- **Reading level:** Is the copy accessible (target 6th-8th grade level)?

### 3. Social Proof and Trust

- **Testimonials:** Are there specific, attributed testimonials with results?
- **Trust badges:** Logos, certifications, security seals, media mentions?
- **Numbers:** User count, results achieved, years in business?
- **Risk reversal:** Money-back guarantee, free trial, no-commitment language?

### 4. CTA and Conversion Elements

- **CTA copy:** Does the button text communicate value (not just "Submit")?
- **CTA frequency:** Is there a CTA at least every 2 scroll-lengths?
- **Form friction:** How many fields? Can any be removed?
- **Urgency/scarcity:** Are there legitimate urgency elements?

### 5. Layout and UX

- **Mobile responsiveness:** Does it work on mobile without horizontal scrolling?
- **Page speed:** Are there heavy images or scripts slowing load time?
- **Distraction audit:** Are there navigation links, sidebars, or external links pulling attention away?
- **White space:** Is the page scannable or visually cluttered?

---

## Phase 3: Report

Deliver the audit as a structured report with scores and prioritized recommendations.

### Report Format

```
## Landing Page Audit Report

**Page:** [URL or page name]
**Goal:** [Conversion action]
**Audit Date:** [Date]

### Scores

| Pillar | Score (1-10) | Priority |
|--------|-------------|----------|
| Above-the-Fold | X | High/Med/Low |
| Copy & Messaging | X | High/Med/Low |
| Social Proof & Trust | X | High/Med/Low |
| CTA & Conversion | X | High/Med/Low |
| Layout & UX | X | High/Med/Low |
| **Overall** | **X/10** | |

### Top 5 Recommendations (Priority Order)

1. [Specific change] — [Expected impact] — [Effort: Low/Med/High]
2. ...

### Detailed Findings

[Section-by-section breakdown with specific observations and fixes]
```

---

## Phase 4: Quick Wins

After the full report, deliver a shortlist of changes the user can implement in under 1 hour.

- Identify 3-5 changes that require minimal effort but high impact
- Provide rewritten headline or CTA copy if those scored low
- Suggest A/B test ideas for the top 2 recommendations

---

## Example: SaaS Free Trial Landing Page

**Intake:** SaaS tool for project management, targeting freelancers, traffic from Google Ads, 2.1% conversion rate, goal is free trial signup.

**Finding excerpt:**
- Headline says "Project Management Made Easy" — generic, no specificity. Rewrite: "Manage Every Client Project in One Dashboard — Free for 14 Days"
- CTA button says "Get Started" — rewrite to "Start My Free Trial"
- No testimonials above the fold — move strongest testimonial to hero section
- Form asks for phone number — remove it, reduces friction

---

## Anti-Patterns

- **Suggesting redesigns without data** — base every recommendation on conversion principles, not personal taste
- **Overloading with 20+ recommendations** — prioritize the top 5 that will move the needle
- **Ignoring traffic source context** — a page receiving cold ad traffic needs different elements than warm email traffic
- **Generic advice** — "make it better" is not actionable. Provide specific copy rewrites and layout changes
- **Aesthetic-only feedback** — "the colors don't match" is not a conversion recommendation unless it impacts readability

---

## Recovery

- **No URL or content provided:** Ask the user to paste the page copy, screenshot, or HTML. Cannot audit without seeing the page.
- **Multiple pages to audit:** Audit one at a time. Offer to create a comparison matrix if they have 2-3 variants.
- **User wants a full website audit:** Redirect — this skill covers one landing page. Suggest auditing their highest-traffic page first.
- **No conversion data available:** Proceed with the audit but note that recommendations are based on best practices, not data-driven insights. Recommend setting up tracking.
