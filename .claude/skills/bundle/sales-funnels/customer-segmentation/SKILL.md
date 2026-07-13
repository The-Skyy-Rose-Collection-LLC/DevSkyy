---
name: customer-segmentation
description: "Segments customers by behavior, value, and needs with tailored communication strategies per segment for targeted engagement."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Customer Segmentation

## When to Use This Skill

Use this skill when you need to:
- Segment your customer base into actionable groups
- Tailor communication, offers, and service levels by segment
- Identify your most valuable and most at-risk customer groups
- Allocate resources based on customer segment value

**DO NOT** use this skill for customer personas (use customer-persona), market research, or lead scoring. This is for segmenting your existing customer base.

---

## Core Principle

NOT ALL CUSTOMERS ARE EQUAL — SEGMENTATION REVEALS WHO DESERVES MORE ATTENTION, WHO NEEDS DIFFERENT MESSAGING, AND WHO IS COSTING YOU MORE THAN THEY ARE WORTH.

---

## Phase 1: Data Collection

Assess what customer data is available for segmentation.

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Customer count** | "How many active customers do you have?" | No default |
| **Data available** | "What do you know about your customers? (purchase history, demographics, usage, engagement)" | Basic — name, purchase history |
| **Business model** | "How do you charge? (subscription, per-project, product sales)" | No default |
| **Segmentation goal** | "Why are you segmenting? (better marketing, tiered service, identify churn risk)" | Better marketing |
| **Current segments** | "Do you currently treat any customer groups differently?" | No — same for all |

**GATE: Confirm available data and goal before choosing segmentation method.**

---

## Phase 2: Segment

Apply segmentation frameworks to the customer base.

### Segmentation Methods

Choose the method that matches the data and goal:

**Value-Based Segmentation (RFM):**
```
## RFM Segmentation

Score each customer 1-5 on three dimensions:

| Dimension | 1 (Low) | 5 (High) |
|-----------|---------|----------|
| **Recency** — When did they last buy? | 6+ months ago | This week |
| **Frequency** — How often do they buy? | Once | 10+ times |
| **Monetary** — How much do they spend? | Bottom 20% | Top 20% |

### Segments from RFM

| Segment | RFM Profile | Description |
|---------|------------|-------------|
| Champions | 5-5-5 to 4-4-4 | Best customers — high value, frequent, recent |
| Loyal | 3-4-4 to 2-3-3 | Consistent buyers with good lifetime value |
| At Risk | 2-3-3 to 1-2-2 | Were good but engagement declining |
| Dormant | 1-1-1 to 1-2-1 | Have not bought recently, low engagement |
| New | 5-1-1 | Recent first purchase, potential unknown |
```

**Behavior-Based Segmentation:**
```
## Behavioral Segments

| Segment | Behavior | Indicators |
|---------|----------|-----------|
| Power Users | Heavy, frequent usage | Daily logins, all features used, high engagement |
| Regular Users | Consistent but moderate | Weekly usage, core features only |
| Occasional Users | Sporadic engagement | Monthly or less, minimal feature adoption |
| Inactive | No recent activity | No login in 30+ days |
```

**Needs-Based Segmentation:**
```
## Needs Segments

| Segment | Primary Need | Characteristics |
|---------|-------------|----------------|
| [Segment A] | [Need] | [What defines this group] |
| [Segment B] | [Need] | [What defines this group] |
| [Segment C] | [Need] | [What defines this group] |
```

### Segment Summary

```
## Customer Segments Overview

| Segment | Count | % of Total | Revenue Share | Avg Value | Trend |
|---------|-------|-----------|--------------|-----------|-------|
| [Segment 1] | [#] | [%] | [%] | $[X] | Growing / Stable / Declining |
| [Segment 2] | [#] | [%] | [%] | $[X] | Growing / Stable / Declining |
```

**GATE: Present segmentation for validation before building strategies.**

---

## Phase 3: Strategy per Segment

Define tailored approaches for each segment.

### Segment Strategy Matrix

```
## Segment Strategies

### [Segment: Champions / High Value]
**Goal:** Retain and expand
**Communication frequency:** [Weekly / Biweekly]
**Communication tone:** Exclusive, appreciative, insider
**Offers:** Early access, premium features, loyalty rewards
**Service level:** Priority support, dedicated contact
**Messaging:** "As one of our top customers, you get..."

### [Segment: Loyal / Regular]
**Goal:** Increase value and deepen engagement
**Communication frequency:** [Biweekly / Monthly]
**Communication tone:** Helpful, educational
**Offers:** Upsell relevant features, bundle deals
**Service level:** Standard with fast response
**Messaging:** "Here is how to get even more value from..."

### [Segment: At Risk / Declining]
**Goal:** Re-engage before churn
**Communication frequency:** [Weekly outreach for 30 days]
**Communication tone:** Personal, caring, non-pushy
**Offers:** Incentive to re-engage (discount, free session, exclusive content)
**Service level:** Proactive outreach, escalation priority
**Messaging:** "We noticed it has been a while — everything OK?"

### [Segment: New]
**Goal:** Activate and establish habit
**Communication frequency:** [Daily for first week, then weekly]
**Communication tone:** Welcoming, guiding
**Offers:** Onboarding support, quick-win resources
**Service level:** Onboarding-focused
**Messaging:** "Welcome! Here is your first step..."
```

---

## Phase 4: Operationalize

Implement and maintain segments over time.

### Segmentation Maintenance

```
## Segment Review Schedule

**Monthly:** Update customer segment assignments based on latest data
**Quarterly:** Review segment sizes and trends — are segments growing or shrinking?
**Biannually:** Reassess segment definitions — are the segments still relevant?
```

### Migration Tracking

Track how customers move between segments:

```
## Segment Migration — [Period]

| From → To | Count | Action Taken | Result |
|-----------|-------|-------------|--------|
| Regular → Champion | [#] | [What drove the upgrade] | Positive |
| Regular → At Risk | [#] | [Warning sign] | Needs attention |
| At Risk → Dormant | [#] | [Re-engagement failed] | Review approach |
```

### Automation Opportunities

- Auto-tag customers in CRM based on RFM scores
- Trigger email sequences when customers enter a new segment
- Alert the owner when a Champion becomes At Risk

---

## Anti-Patterns

- **Too many segments** — more than 5 segments is hard to maintain and act on. Start with 3-4.
- **Segments without strategies** — segmenting customers and then treating them all the same wastes the effort.
- **Static segmentation** — customers change. Update segments at least monthly.
- **Ignoring the "dormant" segment** — deciding they are a lost cause without trying to re-engage wastes existing relationships.
- **Segmenting by demographics only** — behavior and value predict outcomes better than age or location.

---

## Recovery

- **User has too few customers to segment:** Even with 20 customers, you can split into 3 groups: high value, medium value, needs attention. The principle applies at any scale.
- **No data to segment with:** Start with purchase history only (recency + monetary). That is enough for a useful 2-dimension segmentation.
- **User does not have a CRM:** Use a spreadsheet with columns for each segmentation dimension. Manual tagging works under 100 customers.
- **Segments are too similar:** Reduce to fewer segments or use a different segmentation dimension. If all customers look the same, try behavioral data instead of value data.
- **User cannot maintain segment strategies:** Automate what you can (email sequences) and focus manual effort on the top and bottom segments only.
