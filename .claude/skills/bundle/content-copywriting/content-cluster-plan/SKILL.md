---
name: content-cluster-plan
description: "Designs topic cluster strategies with pillar pages, cluster content, and internal linking architecture. Use when building topical authority for SEO."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Content Cluster Plan

## When to Use This Skill

Use this skill when you need to:
- Design a topic cluster strategy with pillar pages and supporting content
- Map internal linking architecture between related content pieces
- Build topical authority around key subjects for SEO
- Plan a content calendar organized by topic clusters

**DO NOT** use this skill for individual blog post writing, keyword research, or technical SEO. This is for strategic content architecture planning.

---

## Core Principle

TOPICAL AUTHORITY IS BUILT BY COVERING A SUBJECT COMPREHENSIVELY THROUGH INTERCONNECTED CONTENT — ONE PILLAR PAGE SUPPORTED BY MANY CLUSTER POSTS SIGNALS TO GOOGLE THAT YOU ARE THE AUTHORITY ON THAT TOPIC.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Business niche** | "What is your area of expertise?" | No default — must be provided |
| **Core topics** | "What 3-5 broad topics should you be known for?" | No default — must be provided |
| **Existing content** | "How many published posts/pages do you have?" | Under 20 |
| **Publishing capacity** | "How many pieces can you publish per month?" | 4 per month |
| **Target audience** | "Who are you writing for?" | Your ideal customer |
| **Primary goal** | "What should this content drive? (traffic, leads, sales)" | Organic traffic and leads |

**GATE: Confirm before designing the cluster architecture.**

---

## Phase 2: Cluster Architecture

### Topic Cluster Map

For each core topic, design one cluster:

```
## Cluster 1: [Core Topic]

**Pillar Page:** "[Comprehensive Guide Title]"
- URL: /guides/[topic]
- Target keyword: [head/body keyword]
- Word count: 3,000-5,000 words
- Format: Comprehensive guide covering all subtopics

**Cluster Posts:**
1. "[Subtopic 1 Title]" → /blog/[slug]
   - Target keyword: [long-tail keyword]
   - Word count: 1,500-2,000 words
   - Links TO pillar: [anchor text]
   - Links FROM pillar: [section where link appears]

2. "[Subtopic 2 Title]" → /blog/[slug]
   - Target keyword: [long-tail keyword]
   - Word count: 1,500-2,000 words
   - Links TO pillar: [anchor text]
   - Links FROM pillar: [section]

3. "[Subtopic 3 Title]" → /blog/[slug]
   ...

[8-15 cluster posts per pillar]
```

### Internal Linking Map

```
## Linking Architecture

Pillar Page ←→ Every cluster post (bidirectional)
Cluster posts → 2-3 other cluster posts in same topic (cross-linking)
Cluster posts → 1 cluster post in a DIFFERENT topic (cross-cluster)

Visual:
        [Cluster Post 1] ←→ [Cluster Post 2]
              ↕                    ↕
         [PILLAR PAGE] ←→ [Cluster Post 3]
              ↕                    ↕
        [Cluster Post 4] ←→ [Cluster Post 5]
```

### Cluster Prioritization

```
## Cluster Priority Ranking

| Cluster Topic | Business Value | Keyword Volume | Competition | Priority |
|--------------|---------------|---------------|-------------|----------|
| [Topic 1] | High | High | Medium | 1 — Build first |
| [Topic 2] | High | Medium | Low | 2 — Quick wins |
| [Topic 3] | Medium | High | High | 3 — Long-term play |
```

**GATE: Approve the cluster architecture before building the content calendar.**

---

## Phase 3: Content Calendar

### Publishing Schedule

```
## 6-Month Content Calendar

**Month 1-2: Cluster 1 Foundation**
Week 1: Publish Pillar Page
Week 2: Cluster Post 1
Week 3: Cluster Post 2
Week 4: Cluster Post 3
[Continue through Month 2]

**Month 3-4: Cluster 2 Foundation**
Week 1: Publish Pillar Page
[Continue...]

**Month 5-6: Cluster 1 Expansion + Cluster 3 Start**
- Add 3-4 new cluster posts to Cluster 1
- Begin Cluster 3 pillar and first posts
```

### Content Brief Templates

For each piece in the cluster, provide a mini-brief:
- Target keyword
- Search intent
- Recommended word count
- Key sections to cover
- Internal links to include
- Link from pillar page section

---

## Phase 4: Polish

### 1. Existing Content Audit

Map existing content into the cluster framework:
- Which existing posts fit into which cluster?
- Which posts need updating to match cluster strategy?
- Which posts are orphaned and need integration?

### 2. Measurement Plan

Track per cluster:
- Total organic traffic to the cluster (pillar + all posts)
- Rankings for pillar keyword and cluster keywords
- Internal link click-through between cluster pages
- Lead/conversion attribution to specific clusters

### 3. Scaling Guidelines

- Start with 1-2 clusters and build them fully before adding more
- Each cluster needs 8-15 posts before topical authority signals are strong
- Update pillar pages quarterly as new cluster content is published
- Prune or merge underperforming cluster posts annually

---

## Anti-Patterns

- **Pillar pages that are too thin** — a 1,000-word "ultimate guide" is not comprehensive. Pillar pages need 3,000+ words with real depth.
- **Cluster posts that don't link back** — every cluster post must link to the pillar. Without links, the cluster is just random blog posts.
- **Too many clusters at once** — building 5 clusters simultaneously means none of them are complete. Focus wins.
- **Overlapping topics across clusters** — if Cluster 1 and Cluster 2 have posts targeting the same keyword, they cannibalize each other.
- **Publishing and forgetting** — cluster content needs updating. Outdated pillar pages lose authority over time.

---

## Recovery

- **No existing content:** Start with one pillar page and 3-4 cluster posts. Build the first cluster before planning others.
- **Existing content is disorganized:** Audit everything, categorize by topic, and retroactively add internal links to create cluster structure.
- **Pillar page not ranking:** Check that cluster posts are linking to it, the content is genuinely comprehensive, and the keyword is achievable for your domain authority.
- **Limited publishing capacity (1-2 posts/month):** Build one cluster at a time. A complete cluster of 10 posts takes 5-10 months at this pace, but it will be effective.
