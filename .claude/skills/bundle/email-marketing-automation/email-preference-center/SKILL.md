---
name: email-preference-center
description: "Designs email preference center structure with subscription options, frequency controls, and topic selections. Use when you need to reduce unsubscribes and give subscribers control."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email Preference Center

## When to Use This Skill

Use this skill when you need to:
- Design a preference center page that reduces unsubscribes
- Define subscription categories, frequency options, and topic selections
- Write the copy for a preference center landing page
- Plan the technical structure for email list segmentation based on preferences

**DO NOT** use this skill for unsubscribe page copy alone, email template design, or general email strategy. This is specifically for building a preference center structure.

---

## Core Principle

A PREFERENCE CENTER TURNS AN UNSUBSCRIBE INTO A DOWNGRADE — GIVING SUBSCRIBERS CONTROL OVER WHAT THEY RECEIVE KEEPS THEM ON YOUR LIST LONGER.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Current email types** | "What emails do you currently send? (newsletter, promos, product updates, etc.)" | No default — must be provided |
| **Sending frequency** | "How often do you email each type?" | Weekly newsletter, occasional promos |
| **Audience segments** | "Do you have distinct audience groups?" | Single audience |
| **Email platform** | "What tool do you use?" | Platform-agnostic |
| **Business model** | "What do you sell?" | Digital products/services |

**GATE: Confirm inputs before designing the preference center.**

---

## Phase 2: Structure Design

### Preference Center Sections

Design these components:

**1. Subscription Categories** — what content types they can opt in/out of
```
## Email Types

☑ Weekly Newsletter — Tips and strategies every Tuesday
☑ Product Announcements — New launches and major updates (2-3x/month)
☑ Promotional Offers — Sales, discounts, and special deals (1-2x/month)
☑ Educational Content — Deep-dive guides and tutorials (2x/month)
☐ Partner Offers — Curated recommendations from trusted partners (1x/month)
```

**2. Frequency Controls** — how often they hear from you
```
## Email Frequency

○ All emails (recommended) — everything as it happens
○ Weekly digest — one summary email per week
○ Monthly digest — one summary email per month
○ Important only — product launches and major announcements only
```

**3. Topic Preferences** — what subjects interest them
```
## Topics I'm Interested In

☐ Marketing & Growth    ☐ Finance & Pricing
☐ Productivity & Tools  ☐ Mindset & Leadership
☐ Tech & Automation     ☐ Case Studies
```

**4. Pause Option** — temporary break instead of unsubscribe
```
## Need a Break?

Instead of unsubscribing, pause emails for:
○ 2 weeks  ○ 1 month  ○ 3 months
```

**GATE: Present the structure and get approval before writing copy.**

---

## Phase 3: Write Copy

### Page Copy Elements

1. **Page headline** — "Customize Your Email Experience"
2. **Intro paragraph** — 2-3 sentences explaining what this page does (emphasize control, not guilt)
3. **Category descriptions** — one line per email type explaining what it is and how often
4. **Save confirmation message** — what the user sees after updating preferences
5. **Unsubscribe fallback** — copy for the "unsubscribe from everything" option at the bottom

### Copy Rules

- Never guilt-trip ("We'll miss you" is manipulative)
- Be transparent about frequency for each option
- Use benefit language for each category ("Tips that save you 3+ hours/week")
- Keep the page scannable — checkboxes and short descriptions

---

## Phase 4: Polish

### 1. Technical Implementation Notes

Provide platform-specific guidance:
- Tag/segment structure needed in the email platform
- Automation rules for frequency preferences
- How pause functionality works (date-based tag removal)

### 2. Link Placement Recommendations

Where to link the preference center:
- Email footer (every email)
- Unsubscribe confirmation page (as alternative)
- Welcome email (set expectations early)

### 3. Metrics to Track

- Preference center visit rate
- Unsubscribe rate before vs. after implementation
- Most/least popular categories
- Pause vs. unsubscribe ratio

---

## Anti-Patterns

- **Too many options** — more than 6 categories overwhelms. Group related content.
- **Hidden unsubscribe** — the option to fully unsubscribe must be visible and easy. Hiding it violates trust and regulations.
- **No frequency control** — categories alone are not enough. Some people want your content less often, not less of it.
- **Guilt-trip copy** — "Are you sure? We'll be sad..." is manipulative and damages brand perception.
- **Not honoring preferences** — if someone opts out of promos, never send them promos. Violations destroy trust instantly.

---

## Recovery

- **Only one email type:** Build frequency controls and topic preferences instead of category opt-outs.
- **No email platform chosen:** Provide a generic structure with notes on implementation for common platforms (ConvertKit, Mailchimp, ActiveCampaign).
- **User wants to prevent all unsubscribes:** Explain that preference centers reduce unsubscribes by 20-30% but cannot eliminate them. A clean list is more valuable than a large one.
- **Complex audience segments:** Limit the preference center to 4-5 top-level categories and handle granular segmentation through behavior-based automation behind the scenes.
