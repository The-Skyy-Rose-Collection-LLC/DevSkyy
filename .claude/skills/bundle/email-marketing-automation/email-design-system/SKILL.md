---
name: email-design-system
description: "Designs email template systems with header/footer standards, button styles, image guidelines, responsive rules, and type-specific layouts. Use when standardizing email communications."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Email Design System

## When to Use This Skill

Use this skill when you need to:
- Create a set of branded email templates for different use cases
- Standardize email design across marketing, transactional, and internal communications
- Define responsive email design rules for mobile and desktop
- Brief a developer or email platform on template requirements

**DO NOT** use this skill for writing email copy, email marketing strategy, or email deliverability optimization. This is for visual and structural email template design.

---

## Core Principle

EMAIL DESIGN MUST WORK ON THE WORST-CASE SCENARIO — A 5-YEAR-OLD PHONE, OUTLOOK 2016, AND DARK MODE SIMULTANEOUSLY. DESIGN FOR CONSTRAINTS, NOT IDEALS.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Email types** | "What types of emails do you send? (newsletter, promotional, transactional, onboarding, announcement)" | Newsletter and transactional |
| **Platform** | "What email tool? (Mailchimp, ConvertKit, Klaviyo, SendGrid, custom)" | Mailchimp |
| **Brand guidelines** | "Brand colors, fonts, and logo?" | Must be provided |
| **Current issues** | "What is wrong with your current emails? (inconsistent, ugly on mobile, low clicks)" | Inconsistent design |
| **Audience** | "Who receives these emails? (customers, subscribers, internal team)" | Customers and subscribers |
| **Frequency** | "How often do you send each type?" | Weekly newsletter, daily transactional |

**GATE: Confirm brief before proceeding.**

---

## Phase 2: Design

### Email Template System Components

1. **Global header** — logo placement, navigation links, preheader text zone
2. **Global footer** — social links, unsubscribe, physical address, legal text
3. **Content modules** — reusable blocks (hero image, text block, CTA button, image + text, testimonial, divider)
4. **Button styles** — primary CTA, secondary CTA, text link
5. **Typography** — email-safe fonts, size hierarchy, line height
6. **Color application** — background, text, CTA, accent usage rules
7. **Image guidelines** — dimensions, alt text requirements, file size limits

### Template Types

| Type | Purpose | Key Elements |
|------|---------|-------------|
| Newsletter | Regular content delivery | Hero, 2-3 content blocks, CTA |
| Promotional | Sale or offer announcement | Hero image, offer details, urgency CTA |
| Transactional | Order confirmation, receipts | Clean layout, order details, next steps |
| Onboarding | Welcome sequence | Personal greeting, single action CTA |
| Announcement | Product launch, company news | Bold headline, concise body, CTA |

**GATE: Present the system design and confirm template types needed.**

---

## Phase 3: Build

### Deliverables

**1. Email Design System Document**
- Component library with specifications for each module
- Color and typography standards for email specifically
- Responsive breakpoints and mobile rules
- Dark mode considerations and fallbacks

**2. Template Specifications (per type)**
- Layout wireframe with module arrangement
- Content zones with character limits
- Image dimensions and alt text requirements
- CTA button specifications (size, color, padding, border radius)

**3. Technical Constraints Guide**
- Email-safe font stack (fallbacks for every font)
- Maximum email width: 600px
- Image guidelines: max 200KB per image, always include alt text
- Button: minimum 44x44px tap target on mobile
- Avoid: CSS grid, custom fonts without fallbacks, video embeds

**4. QA Checklist**
- [ ] Renders correctly in Gmail, Apple Mail, Outlook
- [ ] Mobile responsive at 375px width
- [ ] Dark mode tested and readable
- [ ] All images have alt text
- [ ] Links work and track correctly
- [ ] Unsubscribe link functional
- [ ] Preheader text displays correctly
- [ ] Load time under 3 seconds

---

## Phase 4: Polish

### Implementation Guide

- How to build each template in the chosen email platform
- Module reuse instructions for the team
- Brand-approved image library or resource links

### Governance

- Who can modify templates (role-based access)
- How to request a new template type
- Quarterly review to retire unused templates and add new ones

---

## Example 1: SaaS Weekly Newsletter

**Structure:** Logo header → Hero image with headline → 3 content blocks (image + text) → CTA button → Social footer. Width: 600px. Single column on mobile.

## Example 2: E-commerce Promotional Email

**Structure:** Logo header → Full-width hero with offer overlay → Product grid (2x2) → Countdown timer zone → CTA button → Footer. Dynamic product blocks from catalog.

---

## Anti-Patterns

- **Custom fonts without fallbacks** — if the custom font does not load (common in Outlook), text displays in Times New Roman. Always declare fallbacks.
- **Designing desktop-first** — 60%+ of email opens are on mobile. Design mobile-first, enhance for desktop.
- **Giant images with no alt text** — when images are blocked (default in many clients), the email is blank. Alt text is not optional.
- **Tiny CTA buttons** — a 30px button on mobile is untappable. Minimum 44x44px touch target.
- **Ignoring dark mode** — transparent PNGs and black text on white backgrounds invert poorly. Test dark mode explicitly.

---

## Recovery

- **Email client rendering issues:** Simplify the design. Tables-based layout is ugly but universally supported. Progressive enhancement on top.
- **No developer available:** Use the email platform's drag-and-drop builder with brand colors and fonts configured as defaults.
- **Emails look different on every device:** Accept that pixel-perfect is impossible in email. Aim for "consistently good" not "identical everywhere."
- **Team sends off-brand emails:** Lock down templates in the platform. Restrict editing to content zones only, not design elements.
