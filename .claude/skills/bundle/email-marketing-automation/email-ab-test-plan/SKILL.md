---
name: email-ab-test-plan
description: "Designs A/B testing plans for email campaigns with hypothesis, test variables, sample sizes, and success metrics. Use when you need data-driven email optimization."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email A/B Test Plan

## When to Use This Skill

Use this skill when you need to:
- Design a structured A/B test plan for email campaigns
- Define clear hypotheses, test variables, and success criteria
- Calculate sample sizes needed for statistically meaningful results
- Build a testing roadmap that compounds email performance over time

**DO NOT** use this skill for website A/B testing, ad creative testing, or general analytics setup. This is for email-specific split testing.

---

## Core Principle

TEST ONE VARIABLE AT A TIME WITH A CLEAR HYPOTHESIS — A TEST WITHOUT A PREDICTION IS JUST RANDOM VARIATION.

---

## Phase 1: Testing Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Email type** | "What email are you testing? (newsletter, promo, nurture)" | No default — must be provided |
| **Current performance** | "What are your current open and click rates?" | Industry average (20% open, 2.5% click) |
| **List size** | "How many subscribers will be in this test?" | No default — must be provided |
| **Testing goal** | "What metric do you most want to improve?" | Open rate |
| **Email platform** | "What tool are you using?" | Platform-agnostic |
| **Sending frequency** | "How often do you send this type of email?" | Weekly |

**GATE: Confirm inputs before designing the test plan.**

---

## Phase 2: Test Design

### Hypothesis Framework

Every test starts with a hypothesis in this format:

```
IF we [change this variable]
THEN [this metric] will [increase/decrease]
BECAUSE [reasoning based on audience behavior]
```

Example:
```
IF we change the subject line from benefit-focused to curiosity-based
THEN open rate will increase by 5+ percentage points
BECAUSE our audience responds to information gaps more than stated benefits
```

### Testable Variables (One at a Time)

**Subject Line Tests:**
- Length (short vs. long)
- Formula (curiosity vs. benefit vs. urgency)
- Personalization ({first_name} vs. no name)
- Emoji vs. no emoji
- Number vs. no number

**Send Time Tests:**
- Morning vs. afternoon
- Weekday vs. weekend
- Specific day comparison (Tues vs. Thurs)

**Content Tests:**
- Long vs. short email body
- Plain text vs. designed HTML
- Single CTA vs. multiple links
- Image-heavy vs. text-only
- PS line vs. no PS line

**CTA Tests:**
- Button vs. text link
- CTA copy variations
- CTA placement (top vs. bottom vs. both)
- Color/design of CTA button

### Sample Size Guidance

```
## Minimum Sample Sizes

To detect a 2 percentage point lift at 95% confidence:
- Open rate test: ~2,500 per variant (5,000 total)
- Click rate test: ~5,000 per variant (10,000 total)

For smaller lists:
- Under 1,000: Test is directional only, not statistically significant
- 1,000-5,000: Can test subject lines (open rate) only
- 5,000-10,000: Can test most variables
- 10,000+: Can test subtle differences
```

**GATE: Present the test design with hypothesis for approval.**

---

## Phase 3: Build the Test

### Test Plan Document

```
## A/B Test Plan

**Test name:** [Descriptive name]
**Hypothesis:** IF... THEN... BECAUSE...
**Variable tested:** [One specific element]
**Control (A):** [Current version]
**Variant (B):** [Changed version]
**Metric:** [Primary: open rate | Secondary: click rate]
**Sample size:** [X per variant]
**Test duration:** [Send date or date range]
**Winner criteria:** Variant wins if primary metric is [X]% higher with 95% confidence
**Rollout plan:** Winner sends to remaining [X]% of list [X hours] after test
```

### Writing Both Versions

Write the complete Control (A) and Variant (B) versions of whatever is being tested. If testing subject lines, write both. If testing email body, write both complete emails.

---

## Phase 4: Polish

### 1. Testing Roadmap

Map out 6-8 tests in priority order:

```
## 12-Week Testing Roadmap

Week 1-2: Subject line formula (curiosity vs. benefit)
Week 3-4: Send time (Tuesday 10am vs. Thursday 10am)
Week 5-6: Email length (200 words vs. 500 words)
Week 7-8: CTA style (button vs. text link)
Week 9-10: Personalization (first name vs. no name)
Week 11-12: Design (HTML template vs. plain text)
```

### 2. Results Tracking Template

```
| Test | Date | Variable | Control | Variant | Lift | Significant? | Action |
|------|------|----------|---------|---------|------|--------------|--------|
| #1 | [Date] | Subject formula | 22% open | 27% open | +5pp | Yes | Adopt curiosity formula |
```

### 3. Common Pitfalls Checklist

- [ ] Only one variable is different between A and B
- [ ] Both versions sent at the same time
- [ ] Sample is randomly split (not segmented by behavior)
- [ ] Test runs long enough for reliable data (minimum 24 hours for open rate)
- [ ] Winner criteria defined before sending

---

## Anti-Patterns

- **Testing multiple variables at once** — if you change the subject line AND the send time, you cannot attribute results to either change.
- **Declaring a winner too early** — wait at least 24 hours for open rate tests, 48 hours for click rate tests.
- **Testing with tiny samples** — 50 people per variant tells you nothing. You need thousands for meaningful results.
- **No hypothesis** — "Let's just try something different" produces random results you cannot learn from.
- **Never implementing winners** — testing is pointless if you do not apply what you learn to future emails.

---

## Recovery

- **List too small for statistical significance:** Run tests as directional indicators. Track patterns across multiple tests instead of relying on single results.
- **No baseline metrics:** Send 3-4 emails without testing first to establish baseline open and click rates.
- **User wants to test 5 things at once:** Prioritize by expected impact. Subject lines affect open rates most — start there.
- **Platform doesn't support A/B testing:** Manually split the list into two segments and send different versions. Compare results in a spreadsheet.
