---
name: email-deliverability-audit
description: "Audits email practices for deliverability issues including sender reputation, authentication, and list hygiene. Use when emails are landing in spam or engagement rates are dropping."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email Deliverability Audit

## When to Use This Skill

Use this skill when you need to:
- Diagnose why emails are landing in spam or promotions tabs
- Audit sender authentication (SPF, DKIM, DMARC) and domain reputation
- Review list hygiene practices and identify deliverability risks
- Build an action plan to improve inbox placement rates

**DO NOT** use this skill for writing emails, building sequences, or email strategy. This is a technical audit of email deliverability.

---

## Core Principle

THE BEST EMAIL IN THE WORLD IS WORTHLESS IF IT NEVER REACHES THE INBOX — DELIVERABILITY IS THE FOUNDATION THAT EVERY OTHER EMAIL TACTIC DEPENDS ON.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Email platform** | "What email service provider do you use?" | No default — must be provided |
| **Sending domain** | "What domain do you send from (e.g., @yourbusiness.com)?" | No default — must be provided |
| **List size** | "How many subscribers?" | No default — must be provided |
| **Average open rate** | "What are your current open rates?" | Unknown — will benchmark |
| **Known issues** | "Are emails going to spam, promotions, or getting bounced?" | Unknown |
| **Sending volume** | "How many emails do you send per week/month?" | Varies |
| **List source** | "How were subscribers acquired? Opt-in, purchased, imported?" | Opt-in |

**GATE: Confirm scope before starting the audit.**

---

## Phase 2: Audit Framework

### Deliverability Audit Areas

```
1. Sender Authentication — SPF, DKIM, DMARC configuration
2. Domain & IP Reputation — blacklist checks and reputation scores
3. List Hygiene — bounce rates, complaint rates, list quality
4. Content Factors — spam triggers, formatting, image-to-text ratio
5. Sending Practices — volume, consistency, warm-up
6. Engagement Metrics — open rates, click rates, unsubscribe rates
7. Infrastructure — email platform settings and configuration
```

**GATE: Confirm audit scope.**

---

## Phase 3: Write

### 1. Sender Authentication Audit

```
## Authentication Check

| Protocol | Status | Action Required |
|----------|--------|----------------|
| **SPF** (Sender Policy Framework) | [Pass/Fail/Missing] | [Action if needed] |
| **DKIM** (DomainKeys Identified Mail) | [Pass/Fail/Missing] | [Action if needed] |
| **DMARC** (Domain-based Message Authentication) | [Pass/Fail/Missing] | [Action if needed] |
| **Custom sending domain** | [Yes/No] | [Action if needed] |
| **Return-path alignment** | [Aligned/Misaligned] | [Action if needed] |

### How to Check
- SPF: Look up your DNS TXT records for an SPF entry
- DKIM: Check your email platform's authentication settings
- DMARC: Look up your DNS for a _dmarc TXT record
- Use tools: MXToolbox, Google Postmaster Tools, or mail-tester.com

### What to Fix
- **Missing SPF:** Add an SPF record to your DNS that includes your email platform's servers
- **Missing DKIM:** Enable DKIM signing in your email platform and add the DNS record
- **Missing DMARC:** Add a DMARC record starting with p=none (monitor), then escalate to p=quarantine
- **No custom domain:** Stop sending from a free email address (@gmail.com). Set up a custom sending domain.
```

### 2. Domain & IP Reputation

```
## Reputation Check

**Tools to check:**
- Google Postmaster Tools (free — shows domain reputation for Gmail)
- Sender Score by Validity (senderscore.org)
- MXToolbox Blacklist Check
- Talos Intelligence (Cisco)

**Check results:**

| Check | Result | Risk Level |
|-------|--------|-----------|
| Google Postmaster reputation | [High/Medium/Low/Bad] | [OK/Warning/Critical] |
| Sender Score | [0-100] | [Good (80+) / Warning (60-80) / Critical (<60)] |
| Blacklist status | [Clean / Listed on X] | [OK / Critical] |
| Spam trap hits | [None / Detected] | [OK / Critical] |

### If blacklisted:
1. Identify the blacklist(s) through MXToolbox
2. Visit each blacklist's removal request page
3. Address the root cause (usually a list hygiene issue)
4. Request delisting
5. Monitor for 30 days
```

### 3. List Hygiene Audit

```
## List Health Assessment

| Metric | Your Number | Benchmark | Status |
|--------|-------------|-----------|--------|
| Bounce rate | [X]% | Under 2% | [OK/Warning/Critical] |
| Spam complaint rate | [X]% | Under 0.1% | [OK/Warning/Critical] |
| Unsubscribe rate | [X]% | Under 0.5% | [OK/Warning/Critical] |
| List age (oldest segment) | [X months] | Review 6+ months | [OK/Warning] |
| Inactive subscribers (%) | [X]% | Under 30% | [OK/Warning/Critical] |

### List Hygiene Actions
- [ ] Remove hard bounces immediately (automated in most platforms)
- [ ] Run a re-engagement campaign for subscribers inactive 90+ days
- [ ] Sunset subscribers who do not re-engage
- [ ] Verify new subscribers with double opt-in
- [ ] Never purchase or import email lists from third parties
- [ ] Clean list through an email verification service (NeverBounce, ZeroBounce) every 6 months
```

### 4. Content Factors

```
## Content Audit

| Factor | Status | Recommendation |
|--------|--------|---------------|
| Spam trigger words | [Found/Clean] | Avoid: "free," "act now," "limited time," "click here" in subject lines |
| Image-to-text ratio | [Heavy image / Balanced / Text-focused] | Target 60% text, 40% images max |
| Link count per email | [X links] | Keep under 5 for promotional emails |
| URL shorteners | [Used/Not used] | Avoid — spam filters flag shortened URLs |
| ALL CAPS in subject | [Yes/No] | Never use ALL CAPS |
| Excessive punctuation | [Yes/No] | No "!!!" or "???" in subjects |
| Plain text version | [Included/Missing] | Always include a plain text alternative |
| Unsubscribe link | [Visible/Hidden] | Must be easy to find — hiding it increases spam reports |

### Subject Line Best Practices
- Under 50 characters
- No spam trigger words
- No ALL CAPS
- No excessive punctuation
- Personalization (first name) can improve placement
```

### 5. Sending Practices

```
## Sending Behavior Audit

| Practice | Current | Recommended |
|----------|---------|-------------|
| Sending consistency | [Regular/Sporadic] | Send on a consistent schedule |
| Volume spikes | [Yes/No] | Avoid sudden volume increases (warm up gradually) |
| Sending time | [Time] | Test optimal times; consistency matters more |
| New domain warm-up | [Done/Needed/N/A] | New domains: start with 50-100 emails/day, increase 20-30% weekly |
| Segmentation | [Yes/No] | Send relevant content to segmented lists |
| Preference center | [Yes/No] | Let subscribers choose frequency and topics |

### Warm-Up Schedule for New Domains

| Week | Daily Volume | Focus |
|------|-------------|-------|
| 1 | 50-100 | Send to most engaged subscribers only |
| 2 | 200-500 | Expand to recently active subscribers |
| 3 | 500-1,000 | Add moderately engaged subscribers |
| 4 | 1,000-2,500 | Approach full volume |
| 5+ | Full volume | Monitor and adjust |
```

### 6. Action Plan

```
## Deliverability Improvement Plan

### Immediate (This Week)
1. [Most critical fix — e.g., "Set up DKIM authentication"]
2. [Second priority — e.g., "Remove hard bounces from list"]
3. [Third priority — e.g., "Add plain text version to all emails"]

### Short-Term (Next 30 Days)
1. [e.g., "Run re-engagement campaign for 90+ day inactives"]
2. [e.g., "Set up Google Postmaster Tools monitoring"]
3. [e.g., "Clean list through email verification service"]

### Ongoing
1. Monitor authentication with monthly checks
2. Clean list quarterly
3. Review engagement metrics weekly
4. Test subject lines to improve open rates
```

---

## Phase 4: Polish

### 1. Audit Checklist

```
## Deliverability Audit Checklist

- [ ] SPF, DKIM, and DMARC are properly configured
- [ ] Domain reputation is checked (Google Postmaster, Sender Score)
- [ ] Blacklist status is clean
- [ ] Bounce rate is under 2%
- [ ] Spam complaint rate is under 0.1%
- [ ] Inactive subscribers identified and re-engagement planned
- [ ] Content is free of spam trigger words and formatting issues
- [ ] Sending practices are consistent (no volume spikes)
- [ ] Plain text version is included in all emails
- [ ] Unsubscribe link is visible and functional
- [ ] Action plan is prioritized by impact
```

### 2. Monitoring Dashboard

```
## Monthly Deliverability Metrics to Track

| Metric | Jan | Feb | Mar | ... |
|--------|-----|-----|-----|-----|
| Open rate | | | | |
| Click rate | | | | |
| Bounce rate | | | | |
| Spam complaint rate | | | | |
| Unsubscribe rate | | | | |
| Domain reputation | | | | |
| Inbox placement rate | | | | |
```

---

## Example: Audit Findings for a 10,000-Subscriber List

```
Authentication: SPF set, DKIM missing, no DMARC → Critical
Reputation: Sender Score 72 (warning) → Medium risk
List hygiene: 35% inactive, 3.1% bounce rate → Critical
Content: Subject lines using "FREE" and "!!!" → Fix immediately
Sending: Inconsistent (2 emails one week, 0 the next) → Warning

Top 3 actions:
1. Configure DKIM and DMARC immediately
2. Run re-engagement campaign and sunset 35% inactives
3. Stop using spam trigger words in subject lines
```

---

## Anti-Patterns

- **Ignoring authentication** — sending without SPF, DKIM, and DMARC is like sending unsigned mail. ESPs increasingly require it.
- **Never cleaning the list** — inactive subscribers drag down engagement rates, which signals ISPs to send you to spam.
- **Buying email lists** — purchased lists are the fastest path to blacklisting. Never.
- **Sudden volume spikes** — going from 100 emails/week to 10,000 in one send triggers spam filters.
- **Hiding the unsubscribe link** — this does not prevent unsubscribes. It increases spam reports, which is far worse.
- **Only checking when there is a problem** — deliverability degrades slowly. Monitor monthly, not just when open rates crash.

---

## Recovery

- **Already blacklisted:** Follow the delisting process for each blacklist. Fix the root cause (usually list hygiene). Monitor for 30 days.
- **Open rates crashed suddenly:** Check if authentication broke, if you hit a blacklist, or if a recent email triggered spam filters.
- **Cannot set up DNS records:** Ask your domain registrar's support or hire a freelance sysadmin for a one-time DNS setup (typically $50-100).
- **Using a shared IP (most small senders):** Your deliverability is partially affected by other senders on the same IP. If issues persist, ask your ESP about a dedicated IP (usually requires 50K+ list).
- **ISP-specific issues (Gmail only, Outlook only):** Use tools like GlockApps or mail-tester.com to diagnose ISP-specific placement issues.
