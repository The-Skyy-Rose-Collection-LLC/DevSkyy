---
name: technical-seo-checklist
description: "Creates technical SEO audit checklists covering crawlability, indexation, Core Web Vitals, and structured data. Use when auditing your website's technical health."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Technical SEO Checklist

## When to Use This Skill

Use this skill when you need to:
- Conduct a technical SEO audit of a website
- Identify crawlability, indexation, and performance issues
- Create a prioritized checklist of technical fixes
- Assess Core Web Vitals and structured data implementation

**DO NOT** use this skill for content strategy, keyword research, or link building. This is for the technical foundation that enables content to rank.

---

## Core Principle

TECHNICAL SEO REMOVES THE BARRIERS BETWEEN YOUR CONTENT AND SEARCH ENGINES — IF GOOGLE CANNOT CRAWL, INDEX, AND RENDER YOUR PAGES CORRECTLY, NO AMOUNT OF GREAT CONTENT WILL RANK.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Website URL** | "What is your website?" | No default — must be provided |
| **CMS/platform** | "What platform is your site on?" | WordPress |
| **Page count** | "Approximately how many pages?" | Under 100 |
| **Known issues** | "Are you aware of any technical problems?" | None known |
| **Google Search Console access** | "Do you have GSC set up?" | Yes |
| **Recent changes** | "Any recent redesign, migration, or updates?" | No |

**GATE: Confirm before building the audit checklist.**

---

## Phase 2: Technical Audit Checklist

### Crawlability

```
## Crawlability Checks

- [ ] Robots.txt exists and is accessible at /robots.txt
- [ ] Robots.txt is not blocking important pages or resources
- [ ] XML sitemap exists at /sitemap.xml
- [ ] Sitemap is submitted to Google Search Console
- [ ] Sitemap contains only 200-status URLs (no 404s, no redirects)
- [ ] Sitemap is updated automatically when content is published
- [ ] No orphan pages (pages with zero internal links)
- [ ] Crawl depth: all important pages within 3 clicks of homepage
- [ ] No redirect chains (A→B→C; should be A→C)
- [ ] No redirect loops
- [ ] Server responds within 200ms for the majority of pages
```

### Indexation

```
## Indexation Checks

- [ ] Site:domain.com shows expected number of indexed pages
- [ ] No important pages blocked by noindex tags
- [ ] No important pages blocked by robots.txt
- [ ] Canonical tags present and pointing to correct URLs
- [ ] No duplicate content (multiple URLs for same content)
- [ ] Pagination handled correctly (rel=prev/next or load-more)
- [ ] URL parameters not creating duplicate pages
- [ ] Hreflang tags correct (if multi-language)
- [ ] Google Search Console: Coverage report shows no unexpected errors
```

### Core Web Vitals

```
## Performance Checks

**Largest Contentful Paint (LCP):** Target < 2.5 seconds
- [ ] Hero images optimized (compressed, proper dimensions)
- [ ] Server response time under 200ms
- [ ] No render-blocking CSS/JS above the fold

**Interaction to Next Paint (INP):** Target < 200ms
- [ ] JavaScript execution optimized
- [ ] No long tasks blocking the main thread
- [ ] Event handlers are efficient

**Cumulative Layout Shift (CLS):** Target < 0.1
- [ ] All images have width/height attributes
- [ ] No dynamically injected content above the fold
- [ ] Web fonts loaded with font-display: swap
- [ ] Ad slots have reserved dimensions
```

### On-Page Technical Elements

```
## On-Page Checks

- [ ] HTTPS enabled site-wide (no mixed content)
- [ ] One H1 tag per page
- [ ] Title tags unique and under 60 characters
- [ ] Meta descriptions unique and 150-160 characters
- [ ] Image alt text present on all meaningful images
- [ ] Images compressed and served in modern formats (WebP)
- [ ] Lazy loading implemented for below-fold images
- [ ] Mobile-responsive design (passes Google Mobile-Friendly Test)
- [ ] No broken internal links (404 errors)
- [ ] No broken external links
```

### Structured Data

```
## Structured Data Checks

- [ ] Organization or LocalBusiness schema on homepage
- [ ] Article schema on blog posts
- [ ] BreadcrumbList schema on all inner pages
- [ ] FAQ schema where applicable
- [ ] Product schema on product pages
- [ ] No schema validation errors (test with Rich Results Test)
```

**GATE: Present the checklist with current findings for review.**

---

## Phase 3: Prioritized Fix List

### Priority Matrix

Categorize each issue found:

```
## Fix Priority

**Critical (fix immediately):**
- Issues that block crawling or indexation
- Noindex on important pages
- Sitewide 500 errors
- HTTPS not enabled

**High (fix this week):**
- Core Web Vitals failures
- Broken internal links (404s)
- Missing canonical tags causing duplication
- Redirect chains

**Medium (fix this month):**
- Missing structured data
- Image optimization
- Missing alt text
- Sitemap issues

**Low (fix when possible):**
- External broken links
- Minor CLS issues
- Metadata length optimization
- Font loading improvements
```

### Issue-by-Issue Fix Guide

For each issue found, provide:
1. What the issue is
2. Why it matters for SEO
3. How to fix it (specific steps)
4. Tools to verify the fix

---

## Phase 4: Polish

### 1. Monitoring Setup

- Google Search Console: check weekly for new crawl errors
- Core Web Vitals: monitor via PageSpeed Insights monthly
- Uptime monitoring: set up alerts for downtime
- Broken link checker: run monthly

### 2. Quarterly Audit Schedule

- Full technical audit every quarter
- Focus areas rotate: Q1 crawlability, Q2 performance, Q3 indexation, Q4 structured data
- Document changes and improvements each quarter

### 3. Tool Recommendations

- Free: Google Search Console, PageSpeed Insights, Rich Results Test, Mobile-Friendly Test
- Budget: Screaming Frog (free up to 500 URLs), Lighthouse
- Premium: Ahrefs Site Audit, SEMrush Site Audit, Sitebulb

---

## Anti-Patterns

- **Fixing everything at once** — prioritize critical issues first. Trying to fix 50 things simultaneously leads to nothing being done well.
- **Ignoring Core Web Vitals** — performance is a ranking factor. Slow sites lose rankings and visitors.
- **Blocking CSS/JS in robots.txt** — search engines need to render your pages. Blocking resources prevents proper indexing.
- **No monitoring after fixes** — technical issues recur. Set up monitoring to catch problems early.
- **Over-optimizing at the expense of user experience** — technical SEO serves users first. Don't break the site to fix a minor SEO issue.

---

## Recovery

- **Site not indexed at all:** Check robots.txt for Disallow: /, check for sitewide noindex, verify DNS and hosting are correct.
- **Massive crawl errors after migration:** Implement redirect map immediately. Check the seo-migration-plan skill for recovery steps.
- **Core Web Vitals failing across the site:** Start with the homepage and top 10 traffic pages. Optimize images and eliminate render-blocking resources first.
- **Non-technical user:** Focus on the top 5 highest-impact issues and provide specific step-by-step instructions for their platform (WordPress plugin recommendations, etc.).
