---
name: seo-reporting-template
description: "Creates SEO reporting templates with KPI tracking, ranking changes, traffic analysis, and conversion attribution. Use when building regular SEO performance reports."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# SEO Reporting Template

## When to Use This Skill

Use this skill when you need to:
- Build a recurring SEO report template for monthly or quarterly reviews
- Define which KPIs to track and how to present them
- Create a reporting framework that connects SEO efforts to business results
- Design dashboards or report documents for stakeholders or personal tracking

**DO NOT** use this skill for technical SEO audits, content strategy, or keyword research. This is for building the reporting structure that tracks SEO performance over time.

---

## Core Principle

AN SEO REPORT MUST ANSWER THREE QUESTIONS: WHAT CHANGED, WHY IT CHANGED, AND WHAT WE ARE DOING ABOUT IT — DATA WITHOUT CONTEXT AND ACTION IS JUST NOISE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Report audience** | "Who reads this report? (yourself, client, team)" | Yourself (solopreneur) |
| **Reporting frequency** | "How often? (weekly, monthly, quarterly)" | Monthly |
| **Business goals** | "What business outcomes should SEO drive?" | Traffic, leads, and sales |
| **Data sources** | "What tools do you have? (GSC, GA4, Ahrefs, etc.)" | Google Search Console + Google Analytics |
| **Key pages** | "Which pages matter most to track?" | Homepage, top 10 content pages, service pages |
| **Baseline** | "Do you have historical data to compare against?" | Last month and last year |

**GATE: Confirm reporting needs before building the template.**

---

## Phase 2: Report Structure

### Monthly SEO Report Template

```
## SEO Report — [Month Year]

### Executive Summary (3-5 sentences)
- [Biggest win this month]
- [Key metric change: traffic up/down X%]
- [Primary action taken and result]
- [Focus for next month]

---

### Traffic Overview

| Metric | This Month | Last Month | MoM Change | Last Year | YoY Change |
|--------|-----------|------------|------------|----------|------------|
| Organic sessions | [X] | [X] | [+/-X%] | [X] | [+/-X%] |
| Organic users | [X] | [X] | [+/-X%] | [X] | [+/-X%] |
| Organic pageviews | [X] | [X] | [+/-X%] | [X] | [+/-X%] |
| Avg session duration | [X] | [X] | [+/-X] | [X] | [+/-X] |
| Bounce rate | [X%] | [X%] | [+/-X%] | [X%] | [+/-X%] |

---

### Keyword Rankings

| Keyword | Current | Last Month | Change | Target Page |
|---------|---------|------------|--------|-------------|
| [keyword] | [X] | [X] | [+/- X] | [URL] |

**New keywords ranking (top 50):** [X] new keywords
**Keywords improved:** [X]
**Keywords declined:** [X]

---

### Top Performing Pages

| Page | Sessions | MoM Change | Top Keyword | Position |
|------|---------|------------|-------------|----------|
| [URL] | [X] | [+/- X%] | [keyword] | [X] |

---

### Conversions from Organic

| Goal | Completions | MoM Change | Conversion Rate |
|------|------------|------------|-----------------|
| [Email signups] | [X] | [+/-X%] | [X%] |
| [Sales] | [X] | [+/-X%] | [X%] |
| [Contact form] | [X] | [+/-X%] | [X%] |

---

### Actions Taken This Month
1. [Published X blog posts targeting [keywords]]
2. [Acquired X new backlinks from [sources]]
3. [Fixed X technical issues]

### Plan for Next Month
1. [Content to publish]
2. [Link building targets]
3. [Technical fixes planned]
```

**GATE: Approve the template structure before customizing.**

---

## Phase 3: Customize and Populate

### Data Collection Guide

For each section, document:
- Where to pull the data (which tool, which report)
- How to calculate the metric (formula if needed)
- What comparison period to use
- How to identify anomalies vs. trends

### Visualization Recommendations

```
## Chart Types by Section

**Traffic overview:** Line chart showing 12-month trend
**Keyword rankings:** Table with color-coded changes (green up, red down)
**Top pages:** Bar chart of top 10 pages by sessions
**Conversions:** Funnel visualization or simple table
**Month-over-month:** Comparison bar charts
```

### Commentary Framework

For each data section, answer:
1. **What happened?** — state the data change in plain language
2. **Why?** — attribute the change to a specific cause (algorithm update, new content, technical fix, seasonal trend)
3. **So what?** — what does this mean for the business
4. **Now what?** — what action to take based on this data

---

## Phase 4: Polish

### 1. Report Automation Tips

- Set up Google Search Console email alerts for coverage issues
- Create saved segments in Google Analytics for organic traffic
- Use Google Looker Studio (free) for automated dashboards
- Schedule monthly calendar reminder to pull and review data

### 2. Reporting Cadence

- Weekly: quick check of GSC for errors, traffic anomalies
- Monthly: full report with all sections
- Quarterly: strategic review with trend analysis and goal reassessment
- Annually: year-in-review with ROI analysis

### 3. Presentation Tips

- Lead with wins, then areas for improvement
- Use percentages for changes, absolute numbers for totals
- Compare to goals, not just previous periods
- Include 1-2 screenshots of SERP wins or notable rankings

---

## Anti-Patterns

- **Data dump with no analysis** — 50 charts with no explanation is not a report. Every metric needs a "so what."
- **Tracking vanity metrics only** — impressions and rankings matter, but conversions and revenue are what the business cares about.
- **No comparison periods** — a number without context means nothing. Always show month-over-month and year-over-year.
- **Reporting on everything** — focus on 8-12 key metrics. Too many metrics dilute attention.
- **No action items** — a report that doesn't end with "here's what we're doing next" is an FYI, not a strategy tool.

---

## Recovery

- **No historical data:** Start tracking now. The first report establishes the baseline. Month 2 is when comparisons begin.
- **Only Google Search Console available:** Build the report around impressions, clicks, CTR, and average position. Add GA4 for traffic and conversion data when available.
- **Report takes too long to produce:** Automate data collection with Looker Studio dashboards. Manual analysis time drops from hours to 30 minutes.
- **Nobody reads the report:** Shorten to a one-page executive summary with a link to the full data. Lead with the most interesting finding.
