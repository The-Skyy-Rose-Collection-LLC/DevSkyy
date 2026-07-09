---
name: product-faq
description: "Generates product-specific FAQ sections addressing common pre-purchase questions, objections, and concerns to increase conversion rates. Use when reducing buyer hesitation."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Product FAQ

## When to Use This Skill

Use this skill when you need to:
- Create FAQ sections for individual product pages
- Address common pre-purchase objections to increase conversions
- Reduce customer support inquiries with proactive answers
- Build structured FAQ content for SEO (FAQ schema markup)

**DO NOT** use this skill for general company FAQs, return policy documentation, or customer support scripts. This is for product-specific purchase-decision FAQs.

---

## Core Principle

EVERY FAQ ANSWER SHOULD MOVE THE BUYER CLOSER TO "ADD TO CART" — IF THE ANSWER DOES NOT BUILD CONFIDENCE, REWRITE IT.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product** | "What product needs FAQs?" | Must be provided |
| **Product page URL** | "Share the product page if it exists." | None |
| **Common questions** | "What do customers ask most about this product?" | Will generate from product info |
| **Customer objections** | "What stops people from buying? (price, quality, compatibility, trust)" | Unknown — will anticipate |
| **Support ticket themes** | "Any recurring support questions related to this product?" | None available |
| **Competitor FAQs** | "Have you seen competitor FAQ sections worth referencing?" | None |

**GATE: Confirm brief before generating FAQs.**

---

## Phase 2: Research

### FAQ Category Framework

Generate questions across these categories:

1. **Product details** — what is it, what is included, specifications
2. **Compatibility** — will it work with my setup, device, or situation?
3. **Usage** — how do I use it, how long does it last, is it easy to set up?
4. **Comparison** — how is this different from X, why this over competitors?
5. **Purchase logistics** — shipping, returns, warranty, payment options
6. **Results and expectations** — what results can I expect, how fast?
7. **Trust and credibility** — who made this, is it tested, what is the guarantee?

### Question Generation Rules

- Write questions in the customer's voice ("Will this work with my iPhone?" not "Device compatibility information")
- Prioritize questions that address purchase hesitation
- Include 8-15 questions per product (enough to be helpful, not overwhelming)
- Order from most common to most specific

**GATE: Present the question list for approval before writing answers.**

---

## Phase 3: Write

### Answer Writing Rules

- Keep answers 2-4 sentences (concise and scannable)
- Lead with the direct answer, then add supporting detail
- Turn objections into selling points ("Is it worth the price?" → "Yes, and here is why...")
- Include specific numbers and details (not vague reassurances)
- Link to relevant pages where helpful (size guide, comparison chart, reviews)

### Deliverables

**1. Complete Product FAQ Section**
- 8-15 Q&A pairs organized by category
- Answers written in brand voice
- Internal links included where relevant

**2. FAQ Schema Markup Guide**
- Which questions qualify for FAQ schema (Google rich results)
- Structured data format for implementation
- Note: FAQ schema can increase search result real estate

**3. Support Deflection Estimate**
- Which FAQs address known support ticket themes
- Estimated support ticket reduction per FAQ (based on question frequency)

---

## Phase 4: Polish

### Conversion Optimization

- Place the most objection-handling FAQs closest to the CTA button
- Use expandable/accordion format to avoid overwhelming the page
- Bold the key phrase in each answer for skimmers
- Test: add FAQ section and measure conversion rate change over 30 days

### Maintenance

- Review FAQs quarterly based on new support tickets and customer questions
- Add seasonal or promotional FAQs as needed
- Remove outdated FAQs (discontinued features, expired offers)

---

## Example 1: Physical Product (Kitchen Tool)

**Q: Is this dishwasher safe?**
A: Yes, all parts are top-rack dishwasher safe. We recommend hand washing the blades for longest life, but dishwasher cleaning works perfectly for everyday use.

**Q: What's the difference between this and the Pro version?**
A: The standard version includes 8 blade options. The Pro adds 4 specialty blades (julienne, spiralizer, waffle, ribbon) and a larger catch container. If you stick to basic chopping, the standard is all you need.

## Example 2: Digital Product (Online Course)

**Q: How long do I have access?**
A: Lifetime access. Once you purchase, the course is yours forever, including all future updates. No subscriptions, no expiration.

**Q: What if it's not right for me?**
A: We offer a 30-day money-back guarantee. If the course does not deliver value in the first 30 days, email us for a full refund. No questions asked.

---

## Anti-Patterns

- **Vague answers** — "It depends" is not an answer. Give specific guidance, then cover edge cases.
- **Defensive tone** — "We are not responsible for..." sounds like a legal disclaimer, not a helpful FAQ. Write with confidence and generosity.
- **Too many questions** — 30 FAQs is a knowledge base, not a product FAQ. Keep it to 8-15 of the highest-impact questions.
- **Burying important info** — if "Is it compatible with X?" is the #1 question, put it first, not 12th.
- **Never updating** — stale FAQs with outdated information erode trust. Review when products or policies change.

---

## Recovery

- **No customer question data:** Anticipate questions from the product description, reviews of similar products, and "People also ask" on Google for the product category.
- **Product is brand new:** Create initial FAQs based on the product brief and competitor FAQs. Update with real customer questions after 30 days of sales.
- **Answers require technical expertise:** Draft the FAQ structure and flag answers that need input from the product team or manufacturer.
- **FAQ section is not increasing conversions:** Test placement — FAQs below the fold may not be seen. Try placing 3-5 key FAQs directly under the CTA.
