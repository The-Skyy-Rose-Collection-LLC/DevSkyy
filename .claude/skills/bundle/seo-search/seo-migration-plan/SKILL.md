---
name: seo-migration-plan
description: "Plans website migrations with redirect mapping, risk assessment, and monitoring checklist. Use when changing domains, platforms, or redesigning your site."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# SEO Migration Plan

## When to Use This Skill

Use this skill when you need to:
- Migrate a website to a new domain, platform, or URL structure
- Create a comprehensive redirect map to preserve SEO value
- Assess and mitigate risks of traffic loss during migration
- Build a monitoring plan for post-migration recovery

**DO NOT** use this skill for routine site updates, content changes, or adding new pages. This is for structural website changes that affect URLs, domains, or platforms.

---

## Core Principle

A BOTCHED MIGRATION CAN DESTROY YEARS OF SEO PROGRESS OVERNIGHT — THE GOAL IS ZERO LOST PAGES, ZERO BROKEN LINKS, AND MINIMAL RANKING DISRUPTION THROUGH METICULOUS REDIRECT PLANNING.

---

## Phase 1: Migration Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Migration type** | "What is changing? (domain, platform, URL structure, redesign, HTTPS)" | No default — must be provided |
| **Current site** | "What is the current domain and platform?" | No default — must be provided |
| **New site** | "What is the new domain/platform?" | No default — must be provided |
| **Timeline** | "When is the migration planned?" | No default — must be provided |
| **Current traffic** | "How much organic traffic does the site get monthly?" | Unknown |
| **Page count** | "Approximately how many pages does the current site have?" | Under 100 |

**GATE: Confirm migration details before building the plan.**

---

## Phase 2: Pre-Migration Audit

### Current Site Inventory

```
## Site Crawl Checklist

- [ ] Crawl entire current site (Screaming Frog, Sitebulb, or manual)
- [ ] Export all URLs with status codes
- [ ] Document all pages with organic traffic (Google Analytics)
- [ ] Document all pages with backlinks (Google Search Console or Ahrefs)
- [ ] Save current rankings for top 50 keywords
- [ ] Screenshot key pages (homepage, top landing pages)
- [ ] Export Google Search Console data (last 16 months)
- [ ] Document all current redirects already in place
```

### Redirect Map

```
## Redirect Map Template

| Old URL | New URL | Status | Priority |
|---------|---------|--------|----------|
| /old-page-1 | /new-page-1 | 301 | High (has traffic) |
| /old-page-2 | /new-page-2 | 301 | High (has backlinks) |
| /old-page-3 | / (homepage) | 301 | Low (no traffic) |
| /removed-page | /relevant-alternative | 301 | Medium |

**Rules:**
- EVERY old URL gets a 301 redirect — no exceptions
- Redirect to the most relevant equivalent page
- If no equivalent exists, redirect to the parent category or homepage
- Preserve redirect chains from previous migrations
```

### Risk Assessment

```
## Migration Risk Level

**Low Risk:** HTTPS migration, minor URL changes
- Expected traffic dip: 5-10% for 2-4 weeks

**Medium Risk:** Platform migration with URL changes
- Expected traffic dip: 10-20% for 4-8 weeks

**High Risk:** Domain change or major restructure
- Expected traffic dip: 20-40% for 2-4 months

**Mitigation:** Thorough redirect mapping, staged rollout if possible, immediate monitoring
```

**GATE: Approve the redirect map and risk assessment before proceeding.**

---

## Phase 3: Migration Execution Plan

### Pre-Launch Checklist

```
## Before Flipping the Switch

- [ ] All redirects configured and tested on staging
- [ ] New sitemap.xml generated
- [ ] Robots.txt updated for new site structure
- [ ] Canonical tags pointing to new URLs
- [ ] Internal links updated to new URLs (not relying on redirects)
- [ ] Google Analytics/tracking code installed on new site
- [ ] Google Search Console verified for new domain (if domain change)
- [ ] Schema markup updated with new URLs
- [ ] Social media profiles updated (if domain change)
- [ ] Email links and signatures updated
```

### Launch Day Checklist

```
## Migration Day

- [ ] Deploy redirects
- [ ] Submit new sitemap to Google Search Console
- [ ] Request indexing for top 20 pages via URL Inspection
- [ ] Test 20 random old URLs — confirm redirects work
- [ ] Test all main navigation links on new site
- [ ] Verify analytics tracking is firing on new site
- [ ] Check for crawl errors in Search Console
- [ ] Monitor server response times (migration load)
```

### Post-Migration Monitoring (First 30 Days)

```
## Daily (Week 1):
- Check Google Search Console for crawl errors
- Monitor organic traffic vs. pre-migration baseline
- Test random URLs for redirect functionality
- Check server logs for 404 errors

## Weekly (Weeks 2-4):
- Compare keyword rankings to pre-migration snapshot
- Review indexation rate of new URLs
- Check for redirect chains or loops
- Monitor Core Web Vitals on new platform

## Monthly (Months 2-4):
- Full ranking comparison vs. pre-migration
- Traffic recovery trend analysis
- Backlink profile check (ensure links pass through redirects)
- Address any remaining 404s or redirect issues
```

---

## Phase 4: Polish

### 1. Communication Plan

- Notify key stakeholders of expected traffic dip
- Prepare customer-facing communication if domain changes
- Update third-party listings and directory citations

### 2. Recovery Timeline

Set expectations: most sites recover within 4-12 weeks. Full recovery to pre-migration levels takes 2-4 months for medium-risk migrations.

### 3. Rollback Plan

If critical issues arise:
- Define rollback triggers (traffic drop >50%, major functionality broken)
- Keep old site accessible on staging for 30 days
- Document how to reverse redirects if needed

---

## Anti-Patterns

- **No redirect map** — launching a new site without redirecting old URLs is the fastest way to lose all organic traffic.
- **Using 302 redirects instead of 301** — 302 is temporary and does not pass full SEO value. Always use 301 for permanent migrations.
- **Redirect chains** — old-page → intermediate-page → new-page loses value at each hop. Redirect directly from old to final URL.
- **Removing old content without redirecting** — even "low traffic" pages may have backlinks. Redirect everything.
- **Not monitoring after launch** — problems surface in the first 48 hours. Watch closely or they compound.

---

## Recovery

- **Migration already happened without redirects:** Implement redirects immediately. Some rankings can be recovered even weeks later. Check Search Console for crawl errors.
- **Traffic dropped more than expected:** Verify all redirects are working, check for noindex tags on new pages, and ensure the sitemap is submitted.
- **Too many pages for manual redirect mapping:** Group old URLs by pattern (e.g., /blog/YYYY/MM/slug → /blog/slug) and use regex-based redirect rules.
- **Old domain expiring:** Renew the old domain and keep redirects active for at least 12 months, ideally 24 months.
