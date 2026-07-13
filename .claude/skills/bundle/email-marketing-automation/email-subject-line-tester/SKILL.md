---
name: email-subject-line-tester
description: "Generates and scores 20+ subject line variations using proven formulas and predicts open rate performance. Use when you need high-performing email subject lines."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email Subject Line Tester

## When to Use This Skill

Use this skill when you need to:
- Generate 20+ subject line variations for an email campaign
- Score subject lines against proven open rate formulas
- A/B test subject line pairs optimized for different psychological triggers
- Predict relative open rate performance before sending

**DO NOT** use this skill for SMS copy, push notification text, or ad headlines. This is specifically for email subject lines and preview text.

---

## Core Principle

THE SUBJECT LINE'S ONLY JOB IS TO GET THE EMAIL OPENED — IT MUST CREATE ENOUGH CURIOSITY OR PROMISE ENOUGH VALUE THAT NOT OPENING FEELS LIKE A LOSS.

---

## Phase 1: Brief

Gather the context needed to write relevant, targeted subject lines.

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Email topic/offer** | "What is this email about?" | No default — must be provided |
| **Audience** | "Who is receiving this email?" | Existing email subscribers |
| **Email type** | "What kind of email? (newsletter, promo, announcement, nurture)" | Promotional |
| **Brand voice** | "Casual, professional, playful, urgent?" | Conversational and direct |
| **Any words to avoid** | "Words or phrases that don't fit your brand?" | None |

**GATE: Confirm the brief before generating subject lines.**

---

## Phase 2: Generate Variations

Produce 25 subject lines organized by psychological formula.

### Formula Categories

Generate at least 3 subject lines per category:

**1. Curiosity Gap** — opens a loop the reader must close
- "The pricing mistake that cost me $4,200"
- "I stopped doing this and my revenue doubled"

**2. Benefit-Driven** — states the clear outcome
- "Get 3x more replies with this email template"
- "Save 5 hours this week with one automation"

**3. Urgency/Scarcity** — time or quantity pressure
- "Last chance: price goes up at midnight"
- "Only 12 spots left for the live workshop"

**4. Question-Based** — triggers mental engagement
- "Are you making this invoicing mistake?"
- "What would you do with 10 extra hours per week?"

**5. Social Proof** — leverages others' results
- "How Sarah went from $2K to $10K months"
- "427 solopreneurs already grabbed this"

**6. Pattern Interrupt** — breaks inbox scanning patterns
- "Don't open this email (seriously)"
- "I was wrong about email marketing"

**7. Listicle/Number** — specific and scannable
- "5 subject line tricks that doubled my open rate"
- "3 things I'd do differently starting a business"

**8. Personalization** — uses subscriber data
- "{first_name}, your custom growth plan is ready"
- "Quick question about your business, {first_name}"

### Scoring Criteria

Score each subject line on a 1-10 scale across these factors:

| Factor | Weight | What It Measures |
|--------|--------|-----------------|
| **Curiosity** | 25% | Does it create an open loop? |
| **Clarity** | 20% | Is the value clear in under 2 seconds? |
| **Emotion** | 20% | Does it trigger a feeling (fear, excitement, pride)? |
| **Length** | 15% | 6-10 words / 30-50 characters optimal for mobile |
| **Specificity** | 20% | Does it use concrete numbers or details? |

---

## Phase 3: Rank and Recommend

### Deliverables

1. **Top 5 ranked subject lines** with scores and reasoning
2. **3 A/B test pairs** — each pair tests one variable (curiosity vs. benefit, short vs. long, question vs. statement)
3. **Preview text** for each top 5 subject line (40-90 characters that complement, not repeat, the subject)
4. **Spam trigger check** — flag any words that may trigger spam filters (free, guarantee, act now, etc.)

### Output Format

```
## Top 5 Subject Lines

1. "The pricing mistake that cost me $4,200" — Score: 8.7/10
   Preview: "And the 30-second fix that stopped the bleeding"
   Why: Specific dollar amount + curiosity gap + loss aversion

2. [Next subject line...]
```

**GATE: Present rankings and get user approval before finalizing.**

---

## Phase 4: Polish

### 1. Platform-Specific Notes

Flag any issues for common platforms:
- Gmail clips subject lines over 70 characters
- Mobile shows 30-40 characters before truncating
- Outlook may hide preview text

### 2. Emoji Recommendations

Suggest 2-3 subject line variants with emojis and note that emoji performance varies by audience (B2B generally lower, B2C generally higher).

### 3. Send Time Suggestions

Recommend optimal send times based on email type (promotional: Tuesday/Thursday 10am, nurture: morning, urgent: varies).

---

## Anti-Patterns

- **ALL CAPS subject lines** — feels like shouting and triggers spam filters.
- **Misleading subject lines** — the email must deliver what the subject promises. Bait-and-switch kills trust.
- **Over-using urgency** — if every email is "LAST CHANCE," none of them are.
- **Ignoring mobile length** — most emails are opened on mobile. If the subject gets cut off, the hook is lost.
- **Re:, Fwd: tricks** — fake reply/forward prefixes are deceptive and damage sender reputation.
- **No preview text** — leaving preview text blank wastes prime real estate.

---

## Recovery

- **Vague email topic:** Ask for the one thing the reader should do after opening. Build subject lines around that action.
- **User dislikes all variations:** Ask which category (curiosity, benefit, urgency) feels closest to their voice. Generate 10 more in that style.
- **Spam words flagged:** Provide alternative phrasing that conveys the same urgency without trigger words.
- **No audience info:** Default to general solopreneur audience and note that personalization improves with audience specifics.
