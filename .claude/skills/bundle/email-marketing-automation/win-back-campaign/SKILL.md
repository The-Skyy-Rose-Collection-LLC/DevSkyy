---
name: win-back-campaign
description: "Builds re-engagement email and message sequences to win back churned subscribers, lapsed customers, or inactive users with personalized triggers, incentive strategies, and graceful exit paths. Use when a user has inactive email subscribers, lapsed customers who stopped buying, or churned users they want to re-engage."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Win-Back Campaign

## When to Use This Skill

Use this skill when you need to:
- Re-engage email subscribers who have gone silent (no opens or clicks in 30+ days)
- Win back lapsed customers who stopped buying from an e-commerce store or service
- Recover churned users from a SaaS tool, membership, or subscription
- Build a segmented re-engagement sequence that treats at-risk, lapsed, and churned contacts differently
- Create a graceful exit path that cleans your list of people who no longer want to hear from you

**DO NOT** use this skill for welcome sequences, cold outreach to strangers, or subscribers who never engaged in the first place (they are not lapsed, they are uninterested). For general email automations, use email-sequence instead. For cold contacts, use cold-outreach instead.

---

## Core Principle

WIN-BACK IS NOT BEGGING — IT IS REMINDING PEOPLE WHY THEY CARED IN THE FIRST PLACE AND GIVING THEM A CLEAR REASON TO COME BACK OR A CLEAN WAY TO LEAVE.

---

## Phase 1: Segment

Before writing any email, define who you are writing to and why they went quiet. Different levels of inactivity require different approaches.

### Gather These Inputs

Ask the user for the following. Defaults in parentheses.

1. **Business type** — SaaS, e-commerce, service, membership, newsletter, course (no default)
2. **Product or service** — what the person was buying or using (no default)
3. **Why people churn** — main reason people disengage, if known (unknown)
4. **Average customer lifetime** — how long a typical customer stays (6 months)
5. **Incentive budget** — discount, bonus, or free trial available? (yes, up to 15%)
6. **Email platform** — ConvertKit, Mailchimp, ActiveCampaign, Klaviyo, other (ConvertKit)
7. **Inactive list size** — rough count for segmentation (no default)

### Inactivity Segments

Segment the inactive audience into three tiers. These drive the entire campaign.

| Segment | Inactivity Period | Behavior Signal | Strategy | Incentive Level |
|---------|------------------|----------------|----------|----------------|
| **At-Risk** | 30-60 days inactive | Stopped opening emails, last purchase 1-2 months ago | Gentle nudge, value reminder | None needed |
| **Lapsed** | 60-120 days inactive | No opens, no clicks, no purchases in 2-4 months | Value reminder + soft incentive | Soft (free resource, small bonus) |
| **Churned** | 120+ days inactive | Completely dark for 4+ months, may have cancelled subscription | Strong incentive or graceful goodbye | Strong (discount, free month, exclusive access) |

### Segment Definition Template

Present this to the user before writing any emails:

```
## Win-Back Segments

**Business:** Bloom & Brew, online plant subscription box
**Product:** Monthly curated houseplant box ($39/month)
**Churn reason:** Customers feel they have "enough plants" after 4-5 months

Segment A: At-Risk (~340 contacts)
  Skipped last box or no opens in 3 emails. Approach: remind, no discount.

Segment B: Lapsed (~580 contacts)
  Cancelled 2-4 months ago. Approach: show what they missed + free bonus item.

Segment C: Churned (~910 contacts)
  Cancelled 4+ months ago. Approach: strong offer or clean goodbye.
```

**GATE: Do not proceed to Phase 2 until the user confirms the business type and at least one segment is defined. If the user cannot describe their audience, help them define segments based on their platform data before moving on.**

---

## Phase 2: Write

Write email templates for each segment. Each email has a distinct purpose and escalates toward either re-engagement or a clean exit.

### Email Templates by Segment

#### Email A: "We miss you" (At-Risk — Day 1)

**Purpose:** Personal, value-focused nudge. No discount, no pressure. Remind them why they signed up.

**Subject line formulas:**
- `it's been a while, {first_name}`
- `still growing?`
- `your {product} misses you`
- `a quick update from {brand}`

**Personalization variables:** {first_name}, {last_purchase_item}, {last_login_date}, {membership_tier}

**Example — SaaS tool with 2,000 inactive users (ConvertKit implementation):**

```
Subject: it's been a while, {first_name}

Preview text: We shipped 3 things you'll want to see

---

Hey {first_name},

We noticed you haven't logged into Taskflow in a few weeks,
and we wanted to make sure you didn't miss what's new.

Since your last session, we shipped:

- Board templates — start a new project in 30 seconds instead of building from scratch
- Calendar sync — your Taskflow deadlines now show up in Google Calendar automatically
- Bulk edit — select 20 tasks and update them all at once

Your workspace is still set up exactly how you left it.
Everything you built is waiting for you.

Log in and take a look: [LINK]

If you ran into something that made Taskflow hard to use, I'd
genuinely love to hear about it — just hit reply.

— Priya, Product Lead at Taskflow

P.S. The board templates alone save most teams about 2 hours a
week. Worth a 60-second look.
```

**Example — E-commerce store with lapsed customers:**

```
Subject: still into skincare, {first_name}?

Preview text: We saved your favorites

---

Hey {first_name},

It's been a minute since your last order (the Vitamin C Serum
— great pick, by the way).

Just wanted to pop in and let you know a few things:

Your rewards points are still active — you have 240 points
waiting, which is $12 off your next order.

We also just launched two new products our customers have been
requesting for months:

- Barrier Repair Cream (already our #2 seller)
- SPF 40 Daily Moisturizer (lightweight, no white cast)

Your favorites are saved in your account: [LINK]

No rush, no pressure — just didn't want your points to
expire without a heads-up.

— The Glow Lab Team

P.S. Your points expire in 30 days. Figured you'd rather
use them than lose them.
```

#### Email B: "Here's what you're missing" (Lapsed — Day 5)

**Purpose:** Social proof, new features, and FOMO. Show them the world moved forward without them.

**Subject line formulas:**
- `here's what changed since you left`
- `{first_name}, you missed this`
- `your competitors are using this now`
- `3 things that happened while you were away`

**Example — SaaS tool:**

```
Subject: 3 things that happened while you were away

Preview text: Including the feature you asked for

---

Hey {first_name},

Since you've been away, 1,400 teams joined Taskflow. Here's
what they're seeing that you're not:

1. AI task sorting — Taskflow now auto-prioritizes your backlog
   based on deadlines and dependencies. Teams using it report
   finishing 23% more tasks per sprint.

2. Client portals — give your clients a read-only view of
   project status. No more Monday morning "where are we?" emails.

3. Slack integration — create tasks from Slack messages with
   one click. This was the #1 feature request last quarter.

I'm not going to pretend we're perfect. But we've been listening,
and the product today is not the same one you left.

See what's new: [LINK]

— Priya, Product Lead at Taskflow

P.S. One of our returning users last month said "I can't believe
I waited this long to log back in." Just putting that out there.
```

#### Email C: "Come back for X% off" (Lapsed — Day 10)

**Purpose:** Incentive offer with a clear deadline. This is the first email that includes a discount or bonus.

**Subject line formulas:**
- `a little something to welcome you back`
- `{first_name}, this is just for you`
- `we saved you a spot (and a discount)`
- `come back — this one's on us`

**Example — E-commerce store, 15% discount incentive:**

```
Subject: {first_name}, this is just for you

Preview text: 15% off because we actually miss you

---

Hey {first_name},

We'll keep this short.

You've been gone a while, and we'd love to have you back.
So here's a thank-you for being a past customer:

15% off your next order with code WELCOME-BACK

This code works on everything — including the new Barrier
Repair Cream and SPF 40 Moisturizer.

It's active for 7 days. After that, it's gone.

Shop now: [LINK]

No gimmicks. We just want to earn your business again.

— The Glow Lab Team

P.S. Your code WELCOME-BACK expires on {expiry_date}.
One use per customer.
```

#### Email D: "Should we part ways?" (Churned — Day 14)

**Purpose:** Honest, respectful final email. Give them a clear choice: come back or unsubscribe cleanly. This protects your sender reputation and respects their inbox.

**Subject line formulas:**
- `should we stop emailing you?`
- `one last thing, {first_name}`
- `stay or go — totally your call`
- `is this goodbye?`

**Example — SaaS tool:**

```
Subject: should we stop emailing you?

Preview text: No hard feelings either way

---

Hey {first_name},

We've sent you a few emails over the past couple of weeks
and haven't heard back. That's completely fine — people's
needs change.

We want to respect your inbox, so here's the deal:

OPTION A: Come back and try Taskflow again
We've made significant improvements since you left. Your
account is still active, and we'll give you 30 days of Pro
free to see what's changed: [REACTIVATE LINK]

OPTION B: Unsubscribe and we'll stop emailing
No guilt, no tricks. Click here and you won't hear from us
again: [UNSUBSCRIBE LINK]

If we don't hear from you in the next 7 days, we'll remove
you from our active list automatically. You can always come
back later — your data stays safe.

Thanks for giving Taskflow a shot in the first place.

— Priya, Product Lead at Taskflow

P.S. If there's one thing we could have done differently to
keep you, I'd genuinely like to know. Hit reply — I read
every one.
```

**GATE: Present all four email templates to the user. Do not finalize until the user approves the tone, incentive levels, and personalization approach.**

---

## Phase 3: Sequence

Assemble the individual emails into a timed, automated sequence with conditional logic.

### Default Sequence: 4 Emails Over 14 Days

```
TRIGGER: Contact meets inactivity threshold for any segment
  |
  v
EMAIL 1: "We miss you" (Day 1)
  Purpose: Gentle value reminder, no incentive
  Segment: At-Risk, Lapsed, and Churned all receive this
  |
  +--- IF re-engaged (opened + clicked) ---> EXIT sequence, tag "won-back"
  |
  v  [Wait 4 days]
  |
EMAIL 2: "Here's what you're missing" (Day 5)
  Purpose: Social proof, new features, FOMO
  Segment: Lapsed and Churned only (At-Risk who didn't engage)
  |
  +--- IF re-engaged (opened + clicked) ---> EXIT sequence, tag "won-back"
  |
  v  [Wait 5 days]
  |
EMAIL 3: "Come back for X% off" (Day 10)
  Purpose: Incentive offer with deadline
  Segment: Lapsed and Churned only
  |
  +--- IF re-engaged (used code / reactivated) ---> EXIT sequence, tag "won-back"
  |
  v  [Wait 4 days]
  |
EMAIL 4: "Should we part ways?" (Day 14)
  Purpose: Final chance — reactivate or unsubscribe
  Segment: Churned only (Lapsed who didn't engage on incentive)
  |
  +--- IF clicked reactivate ---> EXIT sequence, tag "won-back"
  +--- IF clicked unsubscribe ---> Remove from all lists
  +--- IF no action in 7 days ---> Auto-suppress from future campaigns
```

### Conditional Logic Rules

**Re-engagement = opened the email AND clicked at least one link.** An open alone does not count.

| Condition | Action |
|-----------|--------|
| Re-engaged at any point | Exit sequence, apply "won-back" tag, move to active segment |
| Used discount code / reactivated | Exit sequence, tag "won-back," trigger welcome-back confirmation |
| Clicked unsubscribe in Email 4 | Remove from all marketing lists immediately |
| No action after Email 4 + 7 days | Auto-suppress, keep in database for annual re-check only |
| Hard bounce on any email | Remove immediately, stop remaining emails |

### Platform Implementation Notes

#### ConvertKit
- Visual Automation triggered by tag ("inactive-30-days," "inactive-60-days," or "inactive-120-days")
- "Condition" steps to route by segment, "Delay" steps between emails (4, 5, 4 days)
- "Goal" step on "Clicked a link in any email" for early exit, "Action" step to apply "won-back" tag
- Auto-suppress: final "Action" step applies "suppressed" tag and removes from broadcast list

#### Mailchimp
- "Customer Journey" triggered by segment membership (last activity date)
- "If/Else" branches after each email for opens/clicks, "Time Delay" between emails
- "Tag" action for "won-back" on re-engagement, "Unsubscribe" or "Inactive" audience at the end

#### Klaviyo (E-commerce Recommended)
- Flow triggered by "Has Not Purchased in X Days" or "Has Not Opened Email in X Days"
- Conditional splits per segment, time delays between emails (4, 5, 4 days)
- "Profile Property" update for "won-back" status, "Suppress" action for non-responders
- Enable "Churn Risk" predictive analytics if available

#### ActiveCampaign
- Automation triggered by "Tag is added" (inactive segment tags), "Wait" conditions between emails
- "If/Else" blocks on "Has opened email" + "Has clicked link" for early exit
- "Add Tag" for "won-back," "End automation" + "Add to suppression list" for non-responders

**GATE: Present the complete sequence map with timing and conditional logic. Do not finalize until the user confirms the flow, timing, and platform.**

---

## Phase 4: Deliver

Once the user approves, compile the complete campaign into a single deliverable document.

### Delivery Contents

Write the complete campaign to `campaigns/win-back-campaign.md` containing: campaign overview, segment definitions table, complete 4-email sequence (subject lines, preview text, body, timing), conditional logic map, platform implementation notes, and pre-send checklist.

### Pre-Send Checklist

Include this at the end of every delivered campaign:

```
## Pre-Send Checklist

- [ ] Cleaned hard bounces from the list BEFORE sending (critical for deliverability)
- [ ] Segmented contacts into At-Risk, Lapsed, and Churned tiers
- [ ] Personalization tokens ({first_name}, {last_purchase_item}) are mapped correctly in the platform
- [ ] Incentive codes are created, tested, and set to expire on the correct date
- [ ] Unsubscribe link works and is clearly visible in every email
- [ ] Sequence exit conditions are configured (re-engagement triggers early exit)
- [ ] Auto-suppress is set for non-responders after Email 4 + 7 days
- [ ] Subject lines are under 50 characters
- [ ] Preview text does not repeat the subject line
- [ ] Emails render correctly on mobile (tested in platform preview)
- [ ] Reply-to address is monitored by a real person
- [ ] SPF, DKIM, and DMARC records are configured for your sending domain
```

### Post-Campaign Recommendations

- **Measure re-engagement rate** — target 5-12% reactivation (varies by industry)
- **Clean non-responders** — suppress permanently anyone who ignored all 4 emails
- **Run quarterly** — new contacts entering inactivity segments auto-flow into the sequence
- **Track revenue recovered** — for e-commerce, calculate revenue from discount code redemptions

---

## Examples

### Example 1: SaaS Tool with 2,000 Inactive Users

**Scenario:** Taskflow, a project management SaaS, 2,000 inactive users (30-120+ days). ConvertKit. Incentive: 30 days Pro free.

**Segments:** At-Risk (430, last login 30-60 days), Lapsed (780, 60-120 days, downgraded), Churned (790, 120+ days, dormant).

**Sequence:** Day 1: "it's been a while" (new features) -- Day 5: "3 things that happened" (social proof) -- Day 10: "this is just for you" (30 days Pro free, 7-day expiry) -- Day 14: "should we stop emailing you?" (reactivate or unsubscribe).

**Platform:** ConvertKit Visual Automation, segment tags, Goal step for re-engagement, auto-suppress Day 21. **Expected:** 5-10% reactivation, highest in At-Risk tier.

### Example 2: E-Commerce Store with Lapsed Customers

**Scenario:** Glow Lab, DTC skincare brand, 1,200 customers inactive 60+ days. Klaviyo. Incentive: 15% off.

**Segments:** At-Risk (320, last purchase 30-60 days, still opening), Lapsed (540, 60-120 days, stopped opening), Churned (340, 120+ days, no engagement).

**Sequence:** Day 1: "still into skincare?" (rewards points + new products) -- Day 5: "you missed this" (bestsellers, reviews) -- Day 10: "this is just for you" (15% off WELCOME-BACK, 7-day expiry) -- Day 14: "stay or go" (final offer or unsubscribe).

**Platform:** Klaviyo Flow, "Has Not Purchased in X Days" trigger, conditional splits, auto-suppress Day 21. **Expected:** 8-12% lapsed purchase rate, ~$6,400 recovered revenue ($60 AOV, 540 lapsed, 8% conversion).

---

## Anti-Patterns

**NEVER do these in win-back campaigns:**

- **Emailing people who never engaged.** They are not lapsed — they are uninterested. Win-back emails to never-engaged contacts hurt sender reputation. Clean them off the list.
- **Offering a discount in the first email.** Leading with discounts trains people to wait for discounts. Value first, incentives in Email 3 at the earliest.
- **Guilt-tripping language.** "We're sad you left" and "Don't you miss us?" are manipulative. Be honest, be helpful, never be needy.
- **Skipping the unsubscribe option in the final email.** The goodbye email MUST offer a clean exit. No exit means spam complaints, which damages deliverability for your entire list.
- **No segmentation.** A 35-day-inactive subscriber does not need the same urgency as a 150-day-inactive one. Segment first, always.
- **Ignoring hard bounces before sending.** Uncleaned inactive lists hard-bounce at high rates, signaling spam to email providers. Clean BEFORE sending.
- **Fake scarcity or deadlines.** "Only 10 spots left" on an unlimited SaaS product is dishonest. State real expiry dates or do not invent them.
- **More than 4 emails to non-responders.** Four ignored emails means they do not want to hear from you. A fifth just increases spam complaints.
- **Difficult unsubscribe process.** One click. Not "update preferences," not a 3-step form. One click.

---

## Recovery

- **Unknown churn reason:** Use a "life got busy" angle and include a reply-to question in Email 1. The campaign itself becomes research — replies reveal churn reasons for future iterations.
- **No incentive budget:** Replace Email 3 with a "what's changed" email using social proof or new features. Value-only re-engagement converts at 3-5% instead of 8-12%, but still works.
- **Inactive list under 100 contacts:** Skip segmentation. Send a single 3-email sequence to everyone. Groups under 100 are too small to segment meaningfully.
- **No purchase or login data to segment by:** Segment by email engagement. At-Risk = opened in last 60 days but no clicks. Lapsed = no opens in 60-120 days. Churned = no opens 120+ days. Every platform tracks this.
- **Domain reputation already damaged:** Fix deliverability first. Clean hard bounces, warm up by sending to engaged subscribers only for 2-4 weeks, then run the win-back.
- **User wants to add a survey:** Add a one-question survey to Email 4 only. Churned users at the exit point have the highest response rate. One question: "What's the main reason you stopped using {product}?" with 4-5 choices.
- **If 3 revision rounds produce no approval:** Stop and reassess. Ask the user to share a re-engagement email they liked, then match that voice and structure.

---

## Quick Reference: Campaign Timing

| Email | Name | Day | Segments | Incentive | Goal |
|-------|------|-----|----------|-----------|------|
| 1 | We miss you | Day 1 | All | None | Remind them of value |
| 2 | Here's what you're missing | Day 5 | Lapsed + Churned | None | Create FOMO with proof |
| 3 | Come back for X% off | Day 10 | Lapsed + Churned | Discount / free trial | Drive reactivation |
| 4 | Should we part ways? | Day 14 | Churned only | Final offer | Reactivate or clean exit |
