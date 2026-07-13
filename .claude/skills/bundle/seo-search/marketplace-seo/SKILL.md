---
name: marketplace-seo
description: "Plans SEO strategies for marketplace platforms with category page optimization, review schema, and internal linking. Use when driving organic traffic to a marketplace."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Marketplace SEO

## When to Use This Skill

Use this skill when you need to:
- Plan an SEO strategy for a marketplace or platform with many listing pages
- Optimize category pages and listing pages for organic search
- Implement structured data (schema markup) for reviews and products
- Build internal linking structures that scale with marketplace growth

**DO NOT** use this skill for single-product e-commerce SEO, content marketing strategy, or technical SEO audits. This is for marketplace-specific SEO strategy.

---

## Core Principle

MARKETPLACE SEO IS A SCALE GAME — YOU ARE NOT OPTIMIZING ONE PAGE, YOU ARE BUILDING TEMPLATES AND STRUCTURES THAT MAKE THOUSANDS OF PAGES RANK. CATEGORY PAGES ARE YOUR MOST VALUABLE SEO ASSET.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Marketplace type** | "What does your marketplace sell or connect?" | No default — must be provided |
| **Geographic scope** | "Local, regional, national, or global?" | National |
| **Number of listings** | "How many active listings do you have?" | Under 500 |
| **Current organic traffic** | "How much organic search traffic do you get monthly?" | Unknown |
| **Top categories** | "What are your main listing categories?" | No default — must be provided |
| **Competitors in search** | "Who ranks for the keywords you want?" | No default — identify 3 competitors |

**GATE: Confirm the brief before building the strategy.**

---

## Phase 2: Keyword Strategy

### Page Type Keyword Mapping

| Page Type | Keyword Pattern | Example |
|-----------|----------------|---------|
| **Homepage** | Brand + primary category | "[Platform]: Find [category] near you" |
| **Category pages** | [Category] + [location/modifier] | "freelance designers in Austin" |
| **Sub-category pages** | [Specific service/product] + [modifier] | "logo design for startups" |
| **Listing pages** | [Specific offering] + [seller name] | Long-tail, unique per listing |
| **Blog/guides** | Informational intent keywords | "how to hire a freelance designer" |

### Category Page Priority

Rank categories by:
1. Search volume (monthly searches for category keyword)
2. Competition (how hard to rank)
3. Commercial intent (likelihood of transaction)
4. Listing density (do you have enough supply to serve the query?)

Focus SEO efforts on categories where you have strong supply AND search demand.

**GATE: Confirm keyword targets and priority categories before writing optimization plans.**

---

## Phase 3: Optimize

### Category Page Template

Every category page must include:
- **H1:** [Category keyword] naturally phrased
- **Intro paragraph (100-150 words):** What the category offers, why users should browse here
- **Filters and sorting:** Visible and functional (search engines index filter combinations)
- **Listing cards:** Title, image, price/rate, rating, location
- **Internal links:** Related categories and popular sub-categories
- **User-generated content:** Reviews summary, Q&A if applicable
- **Schema markup:** ItemList for the listings collection

### Listing Page Optimization

- **Title tag formula:** [Listing title] | [Category] | [Platform name]
- **Meta description:** Auto-generated from listing description (first 155 characters)
- **H1:** Listing title (unique, descriptive)
- **Structured data:** Product, Service, or LocalBusiness schema with reviews
- **Internal links:** Breadcrumbs (Home > Category > Sub-category > Listing)
- **Related listings:** "Similar [category]" section for cross-linking

### Schema Markup Recommendations

```
Category pages: ItemList schema
Listing pages: Product or Service schema with AggregateRating
Review pages: Review schema with author and rating
Local listings: LocalBusiness schema with geo coordinates
```

### Internal Linking Strategy

- **Breadcrumbs:** Every listing links back through category hierarchy
- **Related listings:** Cross-link similar listings at the bottom of each page
- **Category cross-links:** Link related categories from each category page
- **Footer links:** Top categories linked site-wide
- **Blog to category links:** Content pages link to relevant category pages

### Content Strategy for SEO

Create supporting content that drives organic traffic to category pages:
- "How to hire a [category professional]" → links to category page
- "What does [service] cost in [year]?" → links to category page with pricing data
- "[X] best [category] for [use case]" → links to individual listings
- Buyer guides, comparison articles, and how-to content

---

## Phase 4: Polish

### 1. Technical SEO Checklist

```
## Marketplace Technical SEO

- [ ] Category pages have unique title tags and meta descriptions
- [ ] Listing pages generate unique meta descriptions from content
- [ ] Breadcrumb navigation is implemented and visible
- [ ] Schema markup is valid (test with Google Rich Results Test)
- [ ] Pagination uses rel="next" and rel="prev" (or infinite scroll with crawlable links)
- [ ] Duplicate listing pages are canonicalized
- [ ] Filter combinations that create thin pages are noindexed
- [ ] XML sitemap includes all category and listing pages
- [ ] Page load speed is under 3 seconds (especially category pages)
- [ ] Mobile experience is fully responsive
```

### 2. SEO Metrics to Track

| Metric | Tool | Frequency |
|--------|------|-----------|
| Organic traffic by page type | Google Analytics | Weekly |
| Keyword rankings for category pages | Ahrefs/SEMrush | Weekly |
| Indexed pages | Google Search Console | Monthly |
| Click-through rate by page type | Google Search Console | Monthly |
| Backlinks acquired | Ahrefs | Monthly |

### 3. Quality Checklist

```
## Marketplace SEO Checklist

- [ ] Keyword targets mapped to each page type
- [ ] Top 10 category pages optimized with H1, intro, and schema
- [ ] Title tag formula applied across all page types
- [ ] Internal linking structure connects listings → categories → homepage
- [ ] Content strategy supports 3-5 informational keywords per quarter
- [ ] Schema markup implemented for listings and reviews
- [ ] Technical SEO issues resolved (duplicates, thin content, speed)
- [ ] XML sitemap submitted and updating automatically
- [ ] SEO metrics tracked weekly/monthly
- [ ] Competitor rankings monitored for priority keywords
```

---

## Example

**Marketplace:** Freelance design services, national

**Category page title:** "Freelance Logo Designers — Find a Designer | [Platform]"
**Category H1:** "Freelance Logo Designers"
**Intro excerpt:** "Browse 120+ freelance logo designers ready to bring your brand to life. Filter by style, budget, and turnaround time. Every designer is vetted and every project is covered by our satisfaction guarantee."

**Blog content supporting SEO:**
- "How Much Does a Logo Design Cost in 2026?" → links to logo design category
- "How to Write a Design Brief for a Freelancer" → links to multiple design categories

---

## Anti-Patterns

- **Ignoring category pages** — category pages rank for high-volume keywords. Individual listings rank for long-tail. Both matter, but categories drive the most traffic.
- **Duplicate title tags** — every listing generating "Product | [Platform]" as the title destroys SEO. Make titles unique.
- **Thin category pages** — a category page with just a grid of listings and no text will struggle to rank. Add intro content, filters, and internal links.
- **No schema markup** — rich results (stars, prices, availability) dramatically improve click-through rates. Implement schema early.
- **Indexing every filter combination** — "color=blue&size=large&price=low" creates millions of thin pages. Noindex non-essential filter URLs.

---

## Recovery

- **Very few listings:** Focus on content-driven SEO (blog and guides) until listing volume supports strong category pages.
- **Competing against massive marketplaces:** Target long-tail and local keywords where large competitors are weak.
- **Duplicate content across listings:** Require unique descriptions from sellers. Provide templates that produce unique output.
- **No technical SEO expertise:** Start with category page optimization (titles, H1s, intros) and schema markup. These have the highest ROI for effort.
