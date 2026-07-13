---
name: two-sided-email-strategy
description: "Creates email strategies for two-sided marketplaces with separate buyer and seller communication tracks. Use when designing email programs for platform businesses."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Two-Sided Email Strategy

## When to Use This Skill

Use this skill when you need to:
- Design email communication tracks for both buyers and sellers on a marketplace
- Create transactional, onboarding, and engagement emails for each side
- Build re-engagement sequences for dormant marketplace users
- Coordinate cross-side communications (e.g., notifying sellers of buyer activity)

**DO NOT** use this skill for single-sided email marketing, newsletter design, or SaaS email sequences. This is for two-sided marketplace email programs.

---

## Core Principle

A MARKETPLACE EMAIL STRATEGY MUST SERVE TWO AUDIENCES WITH DIFFERENT MOTIVATIONS — BUYERS WANT SELECTION AND TRUST, SELLERS WANT TRANSACTIONS AND GROWTH. NEVER SEND THE SAME EMAIL TO BOTH.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Marketplace type** | "What does your marketplace connect?" | No default — must be provided |
| **Buyer profile** | "Who are your buyers? What motivates them?" | Price, convenience, selection |
| **Seller profile** | "Who are your sellers? What motivates them?" | Revenue, exposure, ease of use |
| **Current emails** | "What emails do you send today?" | Transactional only (confirmations) |
| **Email tool** | "What email platform do you use?" | Mailchimp or platform-native |
| **Volume** | "How many buyers and sellers are on the platform?" | Under 1,000 combined |

**GATE: Confirm the brief before mapping email tracks.**

---

## Phase 2: Map Email Tracks

### Buyer Email Track

| Category | Emails | Trigger |
|----------|--------|---------|
| **Onboarding** | Welcome, first search guide, trust explanation | Signup |
| **Transactional** | Order confirmation, shipping update, delivery, review request | Transaction events |
| **Engagement** | New sellers in your area, curated picks, seasonal highlights | Weekly/biweekly |
| **Re-engagement** | "Still looking?", new listings in saved categories, special offer | 14+ days inactive |

### Seller Email Track

| Category | Emails | Trigger |
|----------|--------|---------|
| **Onboarding** | Welcome, listing guide, first sale tips, verification status | Signup |
| **Transactional** | New order, payment received, review received, payout sent | Transaction events |
| **Engagement** | Performance summary, listing optimization tips, marketplace trends | Weekly/biweekly |
| **Re-engagement** | "Your listings are waiting", success stories, promotional tools | 14+ days inactive |

### Cross-Side Notifications

| Event | Buyer Receives | Seller Receives |
|-------|---------------|-----------------|
| New listing in buyer's interest area | "New [category] listing from [seller]" | — |
| Buyer favorites a listing | — | "[Buyer] saved your listing" |
| New buyer inquiry | — | "You have a new inquiry" |
| Review posted | "Your review was published" | "You received a new review" |

**GATE: Confirm email tracks before writing templates.**

---

## Phase 3: Write

### Buyer Email Templates

**Welcome email:**
```
Subject: Welcome to [Platform] — here is how to find exactly what you need

Hey [Name],

[Platform] connects you with [description of sellers]. Here is how to get started:

1. Browse [category] → [link]
2. Save your favorites → they are stored in your account
3. Message sellers directly → ask questions before you buy

Every transaction is protected by our [guarantee name].

[Start Browsing]
```

**Engagement email:**
```
Subject: New this week on [Platform]

Hey [Name],

[X] new [sellers/listings] joined [Platform] this week. Here are 3 you might like:

1. [Listing name] by [Seller] — [one-line description]
2. [Listing name] by [Seller] — [one-line description]
3. [Listing name] by [Seller] — [one-line description]

[See All New Listings]
```

### Seller Email Templates

**Weekly performance summary:**
```
Subject: Your week on [Platform] — [date range]

Hey [Name],

Here is how your listings performed this week:

- Views: [X] ([+/-]% vs. last week)
- Inquiries: [X]
- Transactions: [X]
- Revenue: $[X]

**Tip of the week:** [One actionable optimization tip]

[View Full Dashboard]
```

**Re-engagement email:**
```
Subject: Your listings have not been updated in [X] days

Hey [Name],

Active sellers on [Platform] get 3x more inquiries than inactive ones. Quick wins to boost your visibility:

1. Update your listing photos (fresh photos = more clicks)
2. Adjust your pricing (we have seen [category] prices shift recently)
3. Respond to any pending inquiries

[Update My Listings]
```

### Copy Rules for Both Sides

- Use the recipient's name and relevant data (views, sales, favorites)
- One CTA per email — never compete for attention
- Keep emails under 150 words (transactional under 100)
- Mobile-friendly: single column, large buttons, short paragraphs
- Unsubscribe link on every non-transactional email

---

## Phase 4: Polish

### 1. Email Cadence Calendar

| Day | Buyer | Seller |
|-----|-------|--------|
| Mon | — | Weekly performance summary |
| Tue | Curated picks (biweekly) | — |
| Wed | — | Optimization tip (biweekly) |
| Thu | — | — |
| Fri | New listings digest | Marketplace trends (monthly) |

Maximum: 2 emails per week per user (excluding transactional).

### 2. Segmentation Strategy

- **Buyer segments:** Active (transacted in 30 days), browsing (searches but no transactions), dormant (no activity in 30+ days)
- **Seller segments:** Power (5+ transactions/month), active (1-4 transactions), new (under 30 days), dormant (no listings/transactions in 30+ days)
- Tailor messaging intensity and content to each segment

### 3. Quality Checklist

```
## Two-Sided Email Checklist

- [ ] Buyer and seller tracks are completely separate
- [ ] Onboarding sequence exists for both sides (3-5 emails each)
- [ ] Transactional emails cover all key events (order, payment, review)
- [ ] Engagement emails use personalized data (activity, preferences)
- [ ] Re-engagement sequences trigger after 14+ days of inactivity
- [ ] Cross-side notifications are designed (favorites, inquiries, reviews)
- [ ] Email cadence does not exceed 2 non-transactional emails per week
- [ ] Every email has exactly one CTA
- [ ] Unsubscribe option is included on all non-transactional emails
- [ ] Segmentation strategy is documented for both sides
```

---

## Example

**Marketplace:** Local home services (connecting homeowners with contractors)

**Buyer re-engagement:**
```
Subject: 3 new electricians in [City] since you last visited

Hey [Name], we noticed you searched for electricians last month. Since then, 3 new licensed electricians joined [Platform] in your area — all with 4.5+ ratings.

[See Available Electricians]
```

**Seller cross-side notification:**
"A homeowner in [Neighborhood] just searched for [your service category]. Update your availability to appear in their results. [Update Availability]"

---

## Anti-Patterns

- **Same email to both sides** — buyers and sellers have opposite motivations. Never send a generic blast to both.
- **Too many emails** — more than 2 non-transactional emails per week drives unsubscribes. Respect the inbox.
- **No personalization** — "New listings on our platform" is generic. "3 new designers in your city specializing in logos" converts.
- **Missing transactional emails** — silence between purchase and delivery creates anxiety. Over-communicate transaction status.
- **No re-engagement** — dormant users do not come back on their own. Design the nudge.

---

## Recovery

- **Low open rates on one side:** Test sender name (platform name vs. personal name), subject line length, and send time. Sellers often respond better to data-driven subjects.
- **High unsubscribe rate:** Reduce frequency, improve relevance, or add preference center for email types.
- **No activity data for personalization:** Start with category-based personalization. Refine as behavioral data accumulates.
- **Small user base makes segmentation impractical:** Send to the full list but write for your most engaged segment. Add segmentation when you pass 500 users per side.
