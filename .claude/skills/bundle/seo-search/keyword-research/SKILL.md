---
name: keyword-research
description: "Conducts keyword research with search volume estimates, difficulty assessment, and content mapping recommendations. Use when planning SEO-driven content."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Keyword Research

## When to Use This Skill

Use this skill when you need to:
- Identify target keywords for SEO content strategy
- Assess keyword difficulty and ranking potential for your site
- Map keywords to content types and search intent
- Build a prioritized keyword list for content planning

**DO NOT** use this skill for paid search keyword lists (use google-ads-campaign), social media hashtag research, or YouTube keyword optimization (use youtube-seo). This is for organic search keyword research.

---

## Core Principle

THE BEST KEYWORD IS NOT THE ONE WITH THE MOST SEARCHES — IT IS THE ONE WHERE YOUR CONTENT CAN REALISTICALLY RANK AND THE SEARCHER IS MOST LIKELY TO BECOME YOUR CUSTOMER.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Business/niche** | "What does your business do?" | No default — must be provided |
| **Seed topics** | "What 3-5 topics are central to your business?" | No default — must be provided |
| **Target audience** | "Who are you trying to attract?" | Potential customers |
| **Website domain** | "What is your website URL?" | No existing site |
| **Domain authority** | "Do you know your Domain Authority or Rating?" | Low (new or small site) |
| **Existing content** | "How many pages/posts do you currently have?" | Under 20 |

**GATE: Confirm the brief before starting research.**

---

## Phase 2: Keyword Discovery

### Research Process

For each seed topic, generate keywords across these categories:

**1. Head Terms** (1-2 words, high volume, high competition)
- Example: "email marketing"
- Use: Awareness content, pillar pages

**2. Body Keywords** (2-3 words, moderate volume)
- Example: "email marketing strategy"
- Use: Category pages, comprehensive guides

**3. Long-Tail Keywords** (4+ words, lower volume, lower competition)
- Example: "email marketing strategy for solopreneurs"
- Use: Blog posts, specific guides — highest conversion intent

**4. Question Keywords** (how, what, why, when queries)
- Example: "how to start email marketing"
- Use: FAQ pages, how-to guides, featured snippet targets

**5. Commercial Intent Keywords** (buyer-ready searches)
- Example: "best email marketing tool for small business"
- Use: Comparison posts, review content, landing pages

### Keyword Evaluation Matrix

For each keyword, assess:

```
| Keyword | Est. Volume | Difficulty | Intent | Priority |
|---------|------------|------------|--------|----------|
| [keyword] | [range] | Low/Med/High | Info/Commercial/Transactional | 1-5 |
```

**Volume estimates:** Provide ranges (e.g., 100-500/month) based on niche knowledge and keyword characteristics.

**Difficulty assessment factors:**
- Current top 10 results: big brands or small sites?
- Content quality of ranking pages: can you do better?
- Domain authority of ranking sites vs. yours
- SERP features present (featured snippets, People Also Ask)

---

## Phase 3: Keyword Mapping

### Content Mapping

Assign each priority keyword to a content type:

```
## Keyword → Content Map

| Keyword | Content Type | Search Intent | Target Page |
|---------|-------------|---------------|-------------|
| [keyword] | Pillar page | Informational | /guide/[topic] |
| [keyword] | Blog post | Informational | /blog/[slug] |
| [keyword] | Landing page | Commercial | /[service] |
| [keyword] | Comparison post | Commercial | /blog/best-[topic] |
```

### Priority Ranking

Rank keywords by a combination of:
1. **Relevance to your business** (will this traffic convert?)
2. **Rankability** (can you realistically reach page 1?)
3. **Search volume** (is there enough traffic to matter?)
4. **Content gap** (does good content already exist on your site?)

### Quick Win Keywords

Identify 5-10 keywords where you have the best chance of ranking quickly:
- Low competition (few quality results currently)
- Clear search intent you can match
- Long-tail with commercial or transactional intent
- Related to content you've already started

---

## Phase 4: Polish

### 1. Keyword Research Report

Deliver a complete spreadsheet-style output:
- 30-50 keywords total, organized by topic cluster
- Volume estimates, difficulty, intent, and priority for each
- Top 10 "start here" keywords highlighted

### 2. Content Calendar Recommendations

Suggest a 3-month content plan based on the keyword priorities:
- Month 1: Quick win keywords (long-tail, low competition)
- Month 2: Body keywords with comprehensive guides
- Month 3: Begin pillar content targeting head terms

### 3. Tracking Setup

Recommend tracking the target keywords:
- Free: Google Search Console for impression and click data
- Paid: Ahrefs, SEMrush, or similar for rank tracking
- Review rankings monthly for the first 6 months

---

## Anti-Patterns

- **Targeting only high-volume keywords** — a new site cannot rank for "email marketing." Start with long-tail keywords and build authority.
- **Ignoring search intent** — ranking for "email marketing" with a blog post when Google shows tools and platforms means you're targeting the wrong content type.
- **Keyword stuffing based on research** — research identifies targets; it does not mean cramming keywords into content.
- **One keyword per page only** — each page should target a primary keyword and 3-5 related secondary keywords naturally.
- **Never revisiting research** — keyword landscapes shift. Refresh research every 6 months.

---

## Recovery

- **No seed topics:** Ask "What questions do your customers ask before buying?" and "What would your ideal customer search for?" to generate seeds.
- **Very competitive niche:** Focus exclusively on long-tail keywords with 4+ words. Build topical authority before targeting competitive terms.
- **No website yet:** Build the keyword map first, then use it to plan site architecture and initial content.
- **User wants exact search volumes:** Explain that without paid tools, volumes are estimates. Relative priority matters more than exact numbers for strategy.
