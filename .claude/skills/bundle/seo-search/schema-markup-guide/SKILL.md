---
name: schema-markup-guide
description: "Generates schema markup recommendations with JSON-LD code for articles, products, FAQs, and local businesses. Use when adding structured data to your website."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Schema Markup Guide

## When to Use This Skill

Use this skill when you need to:
- Generate JSON-LD schema markup code for specific page types
- Identify which schema types are most valuable for your site
- Create FAQ, Product, Article, LocalBusiness, or other structured data
- Improve SERP appearance with rich snippets, star ratings, and enhanced listings

**DO NOT** use this skill for general SEO audits, meta tag optimization, or content writing. This is specifically for structured data markup implementation.

---

## Core Principle

SCHEMA MARKUP HELPS SEARCH ENGINES UNDERSTAND YOUR CONTENT AND DISPLAY IT MORE ATTRACTIVELY IN SEARCH RESULTS — IMPLEMENT THE TYPES THAT MATCH YOUR CONTENT AND CAN TRIGGER RICH RESULTS.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Website URL** | "What is your website?" | No default — must be provided |
| **Page types** | "What types of pages do you have? (blog, product, FAQ, services, local)" | Blog posts and service pages |
| **Business type** | "Are you a local business, online business, or both?" | Online business |
| **CMS/platform** | "What platform is your site built on?" | WordPress |
| **Current schema** | "Do you have any schema markup already?" | None |

**GATE: Confirm before generating markup.**

---

## Phase 2: Schema Audit and Recommendations

### Priority Schema Types

Based on the site, recommend which schema types to implement:

```
## Recommended Schema Types

| Schema Type | Pages to Apply | Rich Result Potential |
|-------------|---------------|---------------------|
| Article | Blog posts | Article rich result |
| FAQ | FAQ pages, blog posts with Q&A | FAQ dropdown in SERP |
| HowTo | Tutorial/guide posts | Step-by-step rich result |
| Product | Product/sales pages | Price, rating, availability |
| LocalBusiness | Homepage, contact page | Local panel, map |
| Organization | Homepage | Knowledge panel |
| BreadcrumbList | All pages | Breadcrumb navigation in SERP |
| WebSite | Homepage | Sitelinks search box |
```

### Implementation Priority

1. Organization or LocalBusiness (homepage) — establishes entity
2. Article (blog posts) — improves content presentation
3. FAQ (anywhere with Q&A content) — triggers FAQ rich result
4. BreadcrumbList (all pages) — improves SERP navigation
5. Product (if applicable) — enables product rich results

**GATE: Approve the schema priorities before generating code.**

---

## Phase 3: Generate Schema Code

### JSON-LD Templates

**Article Schema:**
```json
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Article Title]",
  "description": "[Meta description]",
  "image": "[Featured image URL]",
  "author": {
    "@type": "Person",
    "name": "[Author Name]",
    "url": "[Author URL]"
  },
  "publisher": {
    "@type": "Organization",
    "name": "[Business Name]",
    "logo": {
      "@type": "ImageObject",
      "url": "[Logo URL]"
    }
  },
  "datePublished": "[YYYY-MM-DD]",
  "dateModified": "[YYYY-MM-DD]"
}
</script>
```

**FAQ Schema:**
```json
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[Question 1]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Answer 1]"
      }
    },
    {
      "@type": "Question",
      "name": "[Question 2]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Answer 2]"
      }
    }
  ]
}
</script>
```

**LocalBusiness Schema:**
```json
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "[Business Name]",
  "description": "[Business description]",
  "url": "[Website URL]",
  "telephone": "[Phone]",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[Street]",
    "addressLocality": "[City]",
    "addressRegion": "[State]",
    "postalCode": "[ZIP]",
    "addressCountry": "US"
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
      "opens": "09:00",
      "closes": "17:00"
    }
  ]
}
</script>
```

Generate additional schema types as needed for the user's specific pages.

---

## Phase 4: Polish

### 1. Implementation Guide

- Where to place JSON-LD code (in `<head>` section)
- WordPress plugin options (Yoast, Rank Math, or manual insertion)
- How to add to individual pages vs. templates

### 2. Validation Steps

- Test each markup in Google's Rich Results Test tool
- Check for errors in Google Search Console under Enhancements
- Validate JSON syntax before deploying

### 3. Monitoring

- Track rich result impressions in Google Search Console
- Monitor for schema errors after site updates
- Review new schema types Google supports annually

---

## Anti-Patterns

- **Marking up content that doesn't exist on the page** — schema must match visible page content. Invisible schema is deceptive and violates guidelines.
- **Using deprecated schema types** — check schema.org for current types. Some older types no longer trigger rich results.
- **FAQ schema on every page** — only use FAQ schema where genuine questions and answers exist. Overuse can lead to Google ignoring it.
- **Missing required properties** — each schema type has required fields. Incomplete markup will not trigger rich results.
- **Duplicate schema on the same page** — two Article schemas on one page confuses crawlers. One schema type per page type.

---

## Recovery

- **Not sure what schema types apply:** Run the page through Google's Rich Results Test to see what's currently detected, then add what's missing.
- **Schema errors in Search Console:** Review the specific error message, fix the code, and revalidate using the URL Inspection tool.
- **No rich results appearing after implementation:** Rich results are not guaranteed. Ensure markup is valid, content is high-quality, and wait 2-4 weeks for indexing.
- **Non-technical user:** Recommend a WordPress plugin (Rank Math or Yoast) that handles schema automatically for most page types.
