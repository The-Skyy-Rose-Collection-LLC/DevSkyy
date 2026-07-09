---
name: site-architecture-plan
description: "Plans website information architecture with URL structure, internal linking strategy, and content hierarchy. Use when building or restructuring a website for SEO."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Site Architecture Plan

## When to Use This Skill

Use this skill when you need to:
- Plan a website's URL structure and page hierarchy from scratch
- Restructure an existing site for better SEO and user experience
- Design an internal linking strategy that distributes page authority
- Create a content hierarchy that supports topic clusters and pillar pages

**DO NOT** use this skill for visual web design, wireframing, or technical performance optimization. This is for information architecture and SEO-focused site structure.

---

## Core Principle

EVERY PAGE SHOULD BE REACHABLE IN 3 CLICKS OR FEWER FROM THE HOMEPAGE — FLAT, LOGICAL ARCHITECTURE HELPS BOTH USERS AND SEARCH ENGINES FIND WHAT THEY NEED.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Business type** | "What does your business do?" | No default — must be provided |
| **Core pages needed** | "What pages must your site have?" | Homepage, About, Services, Blog, Contact |
| **Products/services** | "List your products or service categories." | No default — must be provided |
| **Content volume** | "How many blog posts or content pages do you have/plan?" | Under 50 |
| **Target keywords** | "What are your top 5-10 keywords?" | Derived from business type |
| **Current site** | "Is this a new site or a redesign?" | New site |

**GATE: Confirm inputs before designing the architecture.**

---

## Phase 2: Site Structure

### URL Hierarchy

```
## Site Map

/                           ← Homepage
├── /about                  ← About page
├── /services               ← Services overview
│   ├── /services/[service-1]   ← Service detail page
│   ├── /services/[service-2]
│   └── /services/[service-3]
├── /products               ← Products overview (if applicable)
│   ├── /products/[category]
│   └── /products/[category]/[product]
├── /blog                   ← Blog index
│   ├── /blog/[category]    ← Blog category pages
│   └── /blog/[post-slug]   ← Individual posts
├── /resources              ← Guides, tools, downloads
│   └── /resources/[resource-slug]
├── /contact                ← Contact page
└── /[landing-pages]        ← Campaign-specific landing pages
```

### URL Rules

- Lowercase, hyphenated, no special characters
- Include target keyword in the URL slug
- Keep URLs short (under 60 characters ideally)
- No dates in blog URLs (allows evergreen updates)
- Category pages use /blog/category/ not /category/blog/

### Page Type Definitions

```
## Page Types

| Page Type | Purpose | Keyword Target | Template |
|-----------|---------|---------------|----------|
| Homepage | Overview + trust | Brand + primary keyword | Unique |
| Service pages | Convert visitors | Service-specific keywords | Repeated |
| Pillar pages | Comprehensive guides | Head/body keywords | Guide layout |
| Blog posts | Answer specific questions | Long-tail keywords | Post layout |
| Category pages | Organize content | Category keywords | Index layout |
| Landing pages | Campaign conversion | Campaign keywords | Minimal |
```

**GATE: Approve the site structure before designing internal linking.**

---

## Phase 3: Internal Linking Strategy

### Link Architecture

```
## Internal Linking Rules

**Homepage:**
- Links to all main sections (services, blog, resources)
- Links to top 3-5 most important pages
- Receives links from every page (via nav and footer)

**Pillar Pages:**
- Link to every cluster blog post related to the topic
- Receive links from all cluster posts
- Link to relevant service/product pages

**Blog Posts:**
- Link to the parent pillar page
- Link to 2-3 related blog posts
- Link to 1 relevant service/product page
- Use descriptive anchor text (not "click here")

**Service Pages:**
- Link to relevant blog content for depth
- Link to related services for cross-discovery
- Link to testimonial/case study pages
```

### Topic Cluster Map

```
## Topic Clusters

**Cluster 1: [Topic]**
Pillar: /resources/[comprehensive-guide]
├── /blog/[subtopic-1]
├── /blog/[subtopic-2]
├── /blog/[subtopic-3]
└── /blog/[subtopic-4]

**Cluster 2: [Topic]**
Pillar: /resources/[comprehensive-guide]
├── /blog/[subtopic-1]
├── /blog/[subtopic-2]
└── /blog/[subtopic-3]
```

---

## Phase 4: Polish

### 1. Navigation Structure

Define the main navigation menu and footer links:
- Main nav: 5-7 top-level items maximum
- Footer: secondary pages, legal, social links
- Breadcrumbs: enable on all pages below the homepage

### 2. Technical Checklist

- [ ] XML sitemap generated and submitted to Google Search Console
- [ ] Robots.txt allows crawling of all important pages
- [ ] Canonical tags set on all pages
- [ ] 301 redirects planned for any URLs changing (redesign)
- [ ] Breadcrumb markup implemented
- [ ] No orphan pages (every page linked from at least one other page)

### 3. Growth Plan

How the architecture scales as content grows:
- New blog posts slot into existing clusters
- New services get pages under /services/
- New clusters are planned around keyword research
- Site map reviewed quarterly for structural issues

---

## Anti-Patterns

- **Deep nesting** — /services/category/subcategory/sub-subcategory/page is too deep. Keep to 3 levels maximum.
- **Orphan pages** — pages with no internal links pointing to them are invisible to search engines and users.
- **Flat blog with no categories** — hundreds of blog posts at /blog/[slug] with no topical organization wastes cluster potential.
- **Changing URLs without redirects** — every changed URL needs a 301 redirect. Broken links lose all accumulated SEO value.
- **Keyword cannibalization** — two pages targeting the same keyword compete against each other. One page per primary keyword.

---

## Recovery

- **Existing site with no structure:** Audit current pages, group by topic, create category pages, and add internal links. Do not change URLs unless necessary.
- **Too many pages for manual linking:** Prioritize the top 20 pages by traffic and link those manually. Use breadcrumbs and category pages for automatic linking.
- **URL restructure needed:** Create a complete redirect map before changing anything. Test redirects thoroughly after implementation.
- **No blog content yet:** Build the architecture now with placeholder categories. Fill in content based on the topic cluster plan.
