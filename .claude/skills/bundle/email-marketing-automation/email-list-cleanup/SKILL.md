---
name: email-list-cleanup
description: "Plans email list segmentation and cleanup strategies with re-engagement criteria and sunsetting rules. Use when your list has inactive subscribers hurting deliverability."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email List Cleanup

## When to Use This Skill

Use this skill when you need to:
- Identify and segment inactive subscribers dragging down deliverability
- Design a re-engagement campaign to win back cold subscribers
- Create sunsetting rules for permanently removing unengaged contacts
- Improve open rates, click rates, and sender reputation through list hygiene

**DO NOT** use this skill for building new email lists, email content strategy, or technical deliverability audits (SPF, DKIM). This is for cleaning and segmenting an existing list.

---

## Core Principle

A SMALLER, ENGAGED LIST OUTPERFORMS A LARGE, DEAD LIST EVERY TIME — REMOVING UNENGAGED SUBSCRIBERS IMPROVES DELIVERABILITY FOR EVERYONE WHO REMAINS.

---

## Phase 1: List Audit Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **List size** | "How many total subscribers do you have?" | No default — must be provided |
| **Engagement data** | "Can you see open/click rates and last activity date?" | Yes, basic engagement data available |
| **Current open rate** | "What's your average open rate?" | Under 20% (triggering this cleanup) |
| **Sending frequency** | "How often do you email your list?" | Weekly |
| **Email platform** | "What tool are you using?" | Platform-agnostic |
| **Revenue from email** | "Do you make sales directly from email?" | Yes |

**GATE: Confirm the audit brief before creating the cleanup plan.**

---

## Phase 2: Segmentation Plan

### Engagement Segments

Define these segments based on activity:

```
## Subscriber Segments

**Active (keep):** Opened or clicked at least 1 email in the last 90 days
**At-risk:** Opened at least 1 email in last 90-180 days but no clicks
**Inactive:** No opens or clicks in 180+ days
**Ghost:** No opens or clicks in 365+ days, never purchased
**Purchased but inactive:** Bought something but no email engagement in 180+ days
```

### Segment Actions

| Segment | Action |
|---------|--------|
| Active | Continue normal sending |
| At-risk | Send re-engagement sequence |
| Inactive | Send final re-engagement, then sunset |
| Ghost | Remove immediately — they are hurting deliverability |
| Purchased but inactive | Separate re-engagement with purchase reference |

**GATE: Approve segments and actions before writing re-engagement emails.**

---

## Phase 3: Re-Engagement Campaign

### 3-Email Re-Engagement Sequence

Write three emails for the at-risk and inactive segments:

**Email 1 — The Check-In**
- Subject: "Still want to hear from us, {first_name}?"
- Body: Acknowledge it's been a while. Offer value. Ask them to click to stay.
- CTA: "Yes, keep me subscribed" (single click)

**Email 2 — The Value Reminder (3 days later)**
- Subject: "Here's what you've been missing"
- Body: Share your best recent content or offer. Remind them why they signed up.
- CTA: Link to best content or a free resource

**Email 3 — The Goodbye (5 days later)**
- Subject: "We're removing you from our list tomorrow"
- Body: Clear, no-guilt message. One final chance to stay.
- CTA: "Keep me on the list" button
- Note: Anyone who does not click is moved to sunset list

### Sunsetting Rules

```
## Sunset Policy

After the 3-email re-engagement sequence:
- No engagement → remove from active list
- Opened but didn't click → keep for 30 more days, then re-evaluate
- Clicked "keep me" → move back to active segment
- Purchased customer who didn't engage → keep on a separate low-frequency list (monthly only)
```

---

## Phase 4: Polish

### 1. Cleanup Implementation Checklist

- [ ] Export current list with engagement data
- [ ] Create segments based on the criteria above
- [ ] Remove ghost subscribers (365+ days, no purchase) immediately
- [ ] Schedule re-engagement sequence for at-risk and inactive segments
- [ ] Set up automation to tag re-engaged subscribers
- [ ] Remove non-responders after sequence completes
- [ ] Document new list size and expected metric improvements

### 2. Ongoing Hygiene Rules

- Run this cleanup process quarterly
- Automatically sunset subscribers with no engagement after 180 days (after re-engagement attempt)
- Remove hard bounces immediately
- Suppress role-based addresses (info@, support@)
- Monitor deliverability weekly after cleanup

### 3. Expected Results

After a proper cleanup, expect:
- Open rates to increase 5-15 percentage points
- Click rates to improve 1-3 percentage points
- Fewer spam complaints
- Better inbox placement (less likely to land in Promotions/Spam)

---

## Anti-Patterns

- **Never cleaning the list** — a list that grows but never shrinks will see declining engagement and deliverability over time.
- **Removing everyone at once** — always run a re-engagement campaign first. Some inactive subscribers will come back.
- **Guilt-trip goodbye emails** — "We'll miss you SO much" is manipulative. Be clean and professional.
- **Cleaning without fixing the root cause** — if people go inactive because your emails aren't valuable, cleaning alone won't help.
- **Removing purchasers too aggressively** — customers who bought but don't open emails may still buy again. Use a separate, lower-frequency approach.

---

## Recovery

- **No engagement data available:** Use signup date as a proxy. Anyone who signed up 12+ months ago and has no purchase history is likely inactive.
- **User afraid to lose subscribers:** Run the numbers — show them that 5,000 engaged subscribers will generate more revenue than 15,000 with a 10% open rate.
- **Open rate tracking unreliable (Apple MPP):** Focus on click data instead of opens. Clicks are the most reliable engagement signal.
- **Very small list (under 500):** Skip automated cleanup. Manually review the list and send personal re-engagement emails.
