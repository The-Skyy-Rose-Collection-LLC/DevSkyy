---
name: re-engagement-email
description: "Creates re-engagement campaigns for dormant subscribers with segmentation rules and sunset policy. Use when cleaning your email list and winning back inactive subscribers."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Re-Engagement Email

## When to Use This Skill

Use this skill when you need to:
- Write a re-engagement email sequence for inactive subscribers
- Create a strategy to win back dormant email list members
- Build segmentation rules for identifying inactive subscribers
- Design a sunset policy for removing unengaged contacts

**DO NOT** use this skill for welcome sequences, newsletters, or promotional campaigns. This is specifically for re-engaging inactive subscribers.

---

## Core Principle

A SMALLER, ENGAGED LIST OUTPERFORMS A LARGE, DEAD ONE — RE-ENGAGEMENT IS AS MUCH ABOUT CLEANING YOUR LIST AS IT IS ABOUT WINNING PEOPLE BACK.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **List size** | "How many total subscribers?" | No default — must be provided |
| **Inactive definition** | "How long with no opens or clicks counts as inactive?" | 90 days |
| **Email platform** | "What email tool do you use?" | Any |
| **Incentive available** | "Can you offer something to win them back? Discount, free resource, exclusive content?" | Free resource or discount |
| **Sequence length** | "How many re-engagement emails? (2-3 recommended)" | 3 emails |
| **Sunset policy** | "Are you willing to remove subscribers who don't re-engage?" | Yes — after the sequence |

**GATE: Confirm brief before writing.**

---

## Phase 2: Outline

### Re-Engagement Sequence

```
**Email 1: The "We Miss You"** (Day 1)
- Acknowledge the absence, remind them of the value, no pressure

**Email 2: The Incentive** (Day 3-5)
- Offer something valuable to earn a click

**Email 3: The Breakup** (Day 7-10)
- Last chance — re-engage or be removed

**Post-sequence: Sunset** (Day 14)
- Remove non-responders from the active list
```

**GATE: Approve sequence before writing.**

---

## Phase 3: Write

### Segmentation Rules

```
## Identifying Inactive Subscribers

**Inactive criteria:**
- No email opens in the last [90/120/180] days
- No link clicks in the last [90/120/180] days
- Has received at least [10] emails during the inactive period

**Segment name:** "Inactive — [date range]"
**Segment size estimate:** Typically 20-40% of a list that has never been cleaned

**Exclude from re-engagement:**
- Subscribers who joined in the last 30 days (not enough data)
- Subscribers who purchased in the last 90 days (may still be engaged)
```

### Email 1: We Miss You (Day 1)

```
**Subject line options:**
1. "It's been a while — are you still there?"
2. "We haven't heard from you in a while"
3. "Quick check-in: still want to hear from us?"

**Preview text:** "We'd love to keep you — here's what you've been missing."

**Body:**

Hey [Name],

I noticed you haven't opened my emails in a while, so I wanted to check in.

I get it — inboxes are noisy. But I'd love to keep sending you [brief description of value — tips, resources, insights].

Here's what you've missed recently:
- [Recent highlight 1 — link to best recent content]
- [Recent highlight 2 — link]
- [Recent highlight 3 — link]

If you want to keep receiving these, just [click this link / reply "YES" / click the button below].

If not, no hard feelings — I'll clean things up so I'm only emailing people who want to hear from me.

[CTA BUTTON: "Yes, Keep Me Subscribed"]

[Sign-off]
```

### Email 2: The Incentive (Day 3-5)

```
**Subject line options:**
1. "A gift for you (because I'd love you to stay)"
2. "Before you go — I made you something"
3. "[Free resource / X% off] — just for coming back"

**Preview text:** "[Specific incentive] — our way of saying we'd love to keep you."

**Body:**

Hey [Name],

I sent a check-in a few days ago and wanted to follow up with something useful.

I put together [free resource / discount / exclusive content] and I'd like you to have it:

**[Incentive description — what it is and why it's valuable]**

[CTA BUTTON: "Get My [Incentive] →"]

This is my way of saying: your attention matters to me, and I want to earn it.

If you'd rather not hear from me, I completely understand — you can unsubscribe anytime using the link below.

[Sign-off]
```

### Email 3: The Breakup (Day 7-10)

```
**Subject line options:**
1. "Should I remove you from this list?"
2. "Last email from me (unless you say otherwise)"
3. "This is goodbye... unless you click"

**Preview text:** "I'm cleaning my list — click to stay or I'll remove you automatically."

**Body:**

Hey [Name],

This is my last email to you unless you tell me you want to stay.

I'm cleaning my email list to make sure I'm only sending to people who actually want to hear from me. If that's you — click the button below and you'll keep getting [what you send].

[CTA BUTTON: "Keep Me Subscribed"]

If I don't hear from you, I'll remove you from the list in [X days]. No hard feelings, and you can always re-subscribe later.

Thanks for being here — even if this is goodbye.

[Sign-off]

P.S. If you stay, here's what you can expect: [one sentence about your best upcoming content or offer].
```

### Sunset Policy

```
## After the Sequence

**If subscriber clicked any link in the 3-email sequence:**
- Move back to active list
- Tag as "re-engaged [date]"
- Monitor engagement for the next 60 days

**If subscriber did NOT click any link:**
- Wait 7 days after Email 3
- Remove from active sending list
- Move to a "sunset" or "archived" segment
- Do NOT delete — keep for suppression and potential future outreach

**Reactivation option:** Once per year, send a single "re-subscribe" email to sunset contacts with your best offer or content.
```

---

## Phase 4: Polish

### 1. Re-Engagement Checklist

```
## Checklist

- [ ] Inactive segment is properly defined (90-180 days, 10+ emails received)
- [ ] 3-email sequence is written with escalating urgency
- [ ] Each email has 2-3 subject line options for testing
- [ ] Incentive is compelling and exclusive to re-engagement
- [ ] "Keep me subscribed" link/button works as a re-engagement trigger
- [ ] Sunset policy is documented (what happens to non-responders)
- [ ] Emails are mobile-friendly
- [ ] Unsubscribe link is easy to find (do not hide it)
- [ ] Post-sequence automation is set up (move re-engaged vs sunset)
```

### 2. Expected Results

```
## Benchmarks

- Re-engagement rate: 5-15% of inactive subscribers typically re-engage
- List reduction: Expect to sunset 60-80% of inactive contacts
- Deliverability improvement: Removing inactives improves open rates and inbox placement
- Timeline: Full sequence runs in 10-14 days
```

---

## Example: Re-Engagement for a 5,000-Subscriber Newsletter

```
Inactive segment: 1,800 subscribers (no opens in 120 days)
Email 1: "We miss you" — links to 3 best recent posts
Email 2: "Free template pack" — exclusive resource for re-engaging
Email 3: "Last email unless you click" — stay or be removed
Expected: 150-270 re-engaged, 1,500+ sunset
Result: Cleaner list, higher open rates, better deliverability
```

---

## Anti-Patterns

- **Never cleaning your list** — a large, unengaged list hurts deliverability. Email providers flag senders with low engagement.
- **Guilt-tripping inactive subscribers** — "You're ignoring us!" is not a winning approach. Be gracious and make it easy to leave.
- **No incentive** — "Please open my emails again" without giving them a reason will not work. Offer real value.
- **Removing without warning** — give subscribers at least 2 chances to re-engage before sunsetting.
- **Deleting sunset contacts permanently** — archive them. They may want to re-subscribe later.
- **Re-engaging too frequently** — run re-engagement once every 6-12 months, not monthly.

---

## Recovery

- **Re-engagement rate is under 5%:** Your list may be too far gone. Accept the low recovery, clean aggressively, and focus on attracting new, engaged subscribers.
- **Worried about losing subscribers:** Remember: unengaged subscribers cost money (platform fees) and hurt deliverability. Removing them helps the subscribers who DO engage.
- **Email platform does not track opens reliably (Apple MPP):** Use click-based activity (not opens) as the engagement signal. "No clicks in 120 days" is more reliable.
- **No incentive to offer:** Compile your 5 best emails or resources into an exclusive "best of" collection for re-engaging subscribers.
- **Boss/client resists list cleaning:** Show the deliverability data — ISPs penalize senders with low engagement. A clean list reaches more inboxes.
