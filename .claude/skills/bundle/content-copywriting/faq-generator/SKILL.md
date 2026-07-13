---
name: faq-generator
description: "Generates comprehensive FAQ sections organized by category with clear, concise answers optimized for websites, sales pages, and help centers. Use when a user needs an FAQ section for their website, wants to preempt common customer questions, or is building a help page for a product or service."
allowed-tools: Read Write Glob Grep
metadata:
  author: matthewhitcham
  version: "1.0"
---

# FAQ Generator

## When to Use This Skill

Use this skill when the user needs to:
- Create an FAQ section for a sales page, landing page, or product page
- Build a dedicated FAQ or help center page for their website
- Preempt common customer objections before they reach support
- Generate structured FAQ content with SEO-friendly schema markup
- Organize scattered customer questions into a clean, categorized format

**DO NOT** use this skill for:
- Building an internal customer support knowledge base (use customer-support-kb)
- Writing long-form help documentation or user guides
- Creating chatbot scripts or automated response flows
- Answering a single specific customer question on the spot

---

## FAQ Category Framework

Every FAQ is organized across six standard categories. Not every category applies to every business — skip categories that are irrelevant.

| Category | What It Covers | Typical For |
|----------|---------------|-------------|
| **Getting Started** | How to buy, sign up, access, get started | All businesses |
| **Product/Service Details** | What is included, how it works, features, specs | All businesses |
| **Pricing & Payment** | Costs, plans, refunds, payment methods, billing | All businesses |
| **Shipping & Delivery** | Timelines, tracking, international, packaging | E-commerce, physical products |
| **Support & Troubleshooting** | How to get help, common issues, account problems | SaaS, courses, memberships |
| **Trust & Credibility** | Guarantees, certifications, testimonials, track record | All businesses (especially new brands) |

**DEFAULT: Use all 6 categories.** Drop Shipping & Delivery for purely digital products/services. Drop Support & Troubleshooting for simple one-time purchases with no account.

---

## Answer Writing Rules

EVERY FAQ ANSWER MUST LEAD WITH THE DIRECT ANSWER — NEVER OPEN WITH FILLER, PLEASANTRIES, OR A RESTATEMENT OF THE QUESTION.

| Rule | Correct | Incorrect |
|------|---------|-----------|
| Direct answer first | "Yes, we offer a 30-day money-back guarantee." | "Great question! We understand that making a purchase decision can be difficult..." |
| 2-4 sentences max | Concise paragraph with one follow-up detail | Multi-paragraph essay covering every edge case |
| Specific, not vague | "Refunds are processed within 5-7 business days to your original payment method." | "Refunds are handled on a case-by-case basis." |
| Action-oriented endings | "Visit your account dashboard to update your plan." | "Feel free to reach out if you have any questions." |
| No invented policies | Only include details the user has confirmed | Making up refund windows, shipping times, or guarantees |

---

## Core Workflow

### Step 1: Understand

Gather these inputs from the user before generating any questions or answers.

1. **Product or service description** — what they sell and how it works
2. **Target audience** — who buys this (demographics, experience level, pain points)
3. **FAQ context type** — where this FAQ will live:
   - Product FAQ (sales page or product listing)
   - Service FAQ (service page for coaches, consultants, agencies)
   - SaaS FAQ (app or platform landing page)
   - E-commerce FAQ (store-wide help page)
   - Course/Program FAQ (enrollment or sales page)
4. **Pricing details** — price points, plans, tiers, or "contact for pricing"
5. **Refund/guarantee policy** — money-back guarantee, return window, exchange rules
6. **Shipping/delivery details** (if applicable) — timelines, carriers, international availability
7. **Existing customer questions** — support emails, DMs, or tickets they can share (read files with `Read` or `Glob` if paths are provided)
8. **Common objections** — what stops people from buying (too expensive, not sure if it works, trust concerns)

**If the user provides items 1-3, proceed with reasonable defaults for the rest.** Ask only about missing critical details.

**Brief template to present if the user gives a vague request:**

```
I'll build your FAQ section. Quick answers needed:

1. What do you sell? (product, service, course, SaaS, etc.)
2. Who is your target customer?
3. Where will this FAQ live? (sales page, help page, product listing)
4. What is your pricing? (price, plans, or "varies")
5. What is your refund/guarantee policy?
6. Do you ship physical products? If so, what are your shipping timelines?
7. Can you share any past customer questions? (paste them or give me a file path)
8. What is the #1 reason people hesitate to buy?
```

**GATE: Do not proceed to Step 2 until you have at minimum: product/service description, target audience, and FAQ context type.**

---

### Step 2: Extract

Generate 15-25 FAQ questions organized across the relevant categories, with 3-5 questions per active category.

1. **Determine active categories** based on the business type:
   - Digital product/service: Getting Started, Product/Service Details, Pricing & Payment, Support & Troubleshooting, Trust & Credibility (5 categories)
   - Physical product/e-commerce: All 6 categories
   - Simple one-time purchase: Getting Started, Product/Service Details, Pricing & Payment, Trust & Credibility (4 categories)

2. **Generate questions from the customer's perspective** — phrase them the way a real buyer would ask, not in formal corporate language:
   - Write "How do I cancel my subscription?" not "What is the cancellation procedure?"
   - Write "Is this worth it if I'm a complete beginner?" not "What skill level is required to participate?"
   - Write "What happens if I don't like it?" not "What is the dissatisfaction resolution process?"

3. **Write answers following the Answer Writing Rules** — direct answer first, 2-4 sentences, specific details, action-oriented ending.

4. **Include at least 2 objection-handling questions** in Trust & Credibility:
   - Address the #1 hesitation the user identified
   - Address a common trust concern for the business type (e.g., "Is this a scam?" for digital products, "What if it doesn't fit?" for clothing, "Will I actually get results?" for coaching)

5. **Verify completeness:**
   - Every active category has 3-5 questions
   - Total questions fall between 15-25
   - No answer exceeds 4 sentences
   - No answer starts with "Great question," "Absolutely," "Of course," or any filler
   - Pricing and refund questions are always included
   - At least one question addresses the user's stated #1 objection

---

### Step 3: Present

Show the complete FAQ draft organized by category for the user to review.

1. **Present the FAQ grouped by category with headers:**

```
## FAQ Draft — [Product/Service Name]

### Getting Started
**Q: How do I sign up?**
A: [answer]

**Q: Do I need any prior experience?**
A: [answer]

...

### Pricing & Payment
**Q: How much does it cost?**
A: [answer]

...
```

2. **Include the Schema.org FAQ structured data snippet** below the markdown version:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How do I sign up?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Visit our website and click the Get Started button..."
      }
    }
  ]
}
</script>
```

3. **Present a summary:**

```
FAQ Summary:
- 18 questions across 5 categories
- Getting Started (3) | Product Details (4) | Pricing & Payment (4) | Support (3) | Trust (4)
- Schema.org markup included for SEO
- Estimated read time: 4 minutes

Review the questions and answers above. I can:
- Add, remove, or reword any question
- Adjust answer length or tone
- Add a new category
- Change the order of questions within a category

Once approved, I'll save the final files.
```

**GATE: Do not proceed to Step 4 until the user reviews and approves (or requests changes to) the FAQ content.**

---

### Step 4: Deliver

Save the FAQ in both markdown and HTML formats.

1. **Ask the user for their preferred save location.** Default: current working directory under `faq/`.

2. **Save the markdown version** — write to `faq/faq.md`:

```markdown
# Frequently Asked Questions

## Getting Started

### How do I sign up?
Visit our website and click the "Get Started" button...

### Do I need any prior experience?
No prior experience is required...
```

3. **Save the HTML version with schema markup** — write to `faq/faq.html`:

```html
<!-- FAQ Section with Schema.org Markup -->
<section class="faq-section">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [...]
  }
  </script>

  <h2>Frequently Asked Questions</h2>

  <div class="faq-category">
    <h3>Getting Started</h3>
    <details>
      <summary>How do I sign up?</summary>
      <p>Visit our website and click the "Get Started" button...</p>
    </details>
  </div>
</section>
```

4. **Suggest placement:**

```
## Files Saved

- faq/faq.md — Markdown version (for CMS, Notion, docs)
- faq/faq.html — HTML with Schema.org markup (for direct web embed)

## Recommended Placement

- **Sales page:** Place the full FAQ section above the final CTA,
  after testimonials and pricing. This handles last-minute objections
  right before the buy button.
- **Dedicated FAQ page:** Link to it from your footer, navigation bar,
  and any support/contact page.
- **Product listing:** Use the top 5-8 most relevant questions directly
  on the product page.

## SEO Note

The schema markup in faq.html enables Google to display your FAQs
as rich results in search. Paste the <script> block into your page's
<head> or directly above the FAQ section in your page body.
```

---

## Example 1: Online Course ($297) — 18 Questions Across 5 Categories

**User says:** "I sell a self-paced online course called 'Launch Your Freelance Business in 30 Days' for $297. Target audience is people with a skill (design, writing, dev) who want to quit their 9-to-5 and freelance full-time. I offer a 30-day money-back guarantee. The #1 objection is people think they're not ready or experienced enough."

**Step 1 output:**
- Product: Self-paced online course, "Launch Your Freelance Business in 30 Days"
- Audience: Skilled professionals (designers, writers, developers) wanting to freelance
- Context type: Course/Program FAQ (sales page)
- Price: $297 one-time payment
- Guarantee: 30-day money-back, no questions asked
- Shipping: N/A (digital)
- Objection: "I'm not experienced/ready enough"
- Active categories: Getting Started (3), Product/Service Details (4), Pricing & Payment (4), Support & Troubleshooting (3), Trust & Credibility (4)

**Step 2 output (full FAQ):**

### Getting Started

**Q: How do I access the course after I buy it?**
A: You get instant access. After checkout, you will receive an email with your login credentials and a direct link to the course dashboard. You can start the first module within 5 minutes of purchasing.

**Q: How long do I have to complete the course?**
A: You have lifetime access. The course is designed as a 30-day program, but you can work through it at your own pace. All materials, templates, and bonuses stay available to you permanently.

**Q: Do I need any special software or tools to take the course?**
A: You need a computer or tablet with internet access and a web browser. The course is delivered through an online portal with video lessons, downloadable templates, and written guides. No additional paid software is required.

### Product/Service Details

**Q: What exactly is included in the course?**
A: The course includes 30 video lessons (one per day), 12 downloadable templates (contracts, proposals, invoicing), a private community for accountability, and 4 bonus workshops on pricing, cold outreach, portfolio building, and client retention.

**Q: Is this just theory, or will I actually land clients?**
A: The course is built around action. By Day 14, you will have a live portfolio and have sent your first outreach messages. By Day 30, the goal is to have your first paying client or a pipeline of warm leads. Every lesson ends with a specific task to complete before moving on.

**Q: What kind of freelancers is this course for?**
A: The course works for designers, writers, developers, marketers, and other skilled professionals who want to freelance. The business fundamentals (pricing, proposals, client management, finding work) apply across all service-based freelance niches.

**Q: Will the course content be updated over time?**
A: Yes. When strategies or tools change, the course is updated at no extra cost. You will be notified by email when new lessons or resources are added.

### Pricing & Payment

**Q: How much does the course cost?**
A: The course is a one-time payment of $297. There are no recurring fees, upsells, or hidden costs. You pay once and get lifetime access to everything.

**Q: Do you offer a payment plan?**
A: Yes. You can split the cost into 3 monthly payments of $109. The total with the payment plan is $327. You get full access to the course from your first payment.

**Q: What is your refund policy?**
A: There is a 30-day money-back guarantee with no questions asked. If you go through the course and feel it is not right for you, email support@example.com within 30 days of purchase for a full refund.

**Q: What payment methods do you accept?**
A: Visa, Mastercard, American Express, PayPal, and Apple Pay. All payments are processed securely through Stripe.

### Support & Troubleshooting

**Q: What if I get stuck on a lesson or need help?**
A: Post your question in the private community and you will typically get a response within 24 hours from either the instructor or a fellow student. For technical issues with the platform, email support@example.com.

**Q: Can I download the videos for offline viewing?**
A: The video lessons are streaming-only, but all templates, worksheets, and written guides are downloadable as PDF files. You can access the streaming videos from any device with an internet connection.

**Q: I bought the course but did not receive my login email. What do I do?**
A: Check your spam and promotions folders first. If the email is not there, go to the course login page and click "Forgot Password" using the email you purchased with. If that does not work, email support@example.com with your order confirmation and you will be set up within a few hours.

### Trust & Credibility

**Q: I am not sure I am experienced enough. Is this course for beginners?**
A: If you have a marketable skill (you can design, write, code, or provide a service), you are experienced enough. This course does not teach you your craft — it teaches you how to turn your existing skill into a business. Over 60% of students started with zero freelance experience.

**Q: How do I know this course actually works?**
A: Over 2,000 students have completed the program. The average student lands their first paying client within 45 days of enrollment. Student results and testimonials are posted on the course sales page with real names and LinkedIn profiles.

**Q: Who created this course?**
A: The course was created by a freelancer who built a six-figure freelance business in under 18 months and has been freelancing full-time for over 5 years. Full bio and credentials are on the About page.

**Q: What if I want to quit my job but I am not ready to go full-time yet?**
A: The course is designed to work alongside a full-time job. Lessons take 30-45 minutes per day. Most students build their freelance pipeline on evenings and weekends before making the switch. There is no pressure to quit your job on any specific timeline.

---

## Example 2: Handmade Jewelry Etsy Shop — 15 Questions With Shipping Focus

**User says:** "I sell handmade sterling silver jewelry on Etsy. Price range is $35-$150. I ship from Portland, OR. Free US shipping, international is $12 flat rate. Processing time is 3-5 business days since everything is made to order. I accept returns within 14 days for unworn items. People always ask about sizing and whether the jewelry will tarnish."

**Step 1 output:**
- Product: Handmade sterling silver jewelry
- Audience: Women 25-45 looking for unique, quality jewelry
- Context type: E-commerce FAQ (Etsy shop or standalone store)
- Price range: $35-$150
- Guarantee: 14-day returns for unworn items
- Shipping: Free US, $12 international flat rate, 3-5 day processing (made to order)
- Objections: Sizing uncertainty, tarnishing concerns
- Active categories: All 6

**Step 2 output (full FAQ):**

### Getting Started

**Q: How do I place an order?**
A: Browse the shop, select your piece, choose your size (if applicable), and check out through Etsy. You will receive an order confirmation email within minutes.

**Q: Can I order a custom piece or request modifications?**
A: Yes. Message the shop before placing an order to discuss custom requests. Custom pieces start at $75 and take 7-10 business days to complete. Customization includes chain length adjustments, stone swaps, and engraving on select pieces.

**Q: Do you offer gift wrapping?**
A: Every order ships in a branded jewelry box with a polishing cloth included at no extra cost. For gift orders, add a note at checkout with your gift message and it will be included on a handwritten card.

### Product/Service Details

**Q: What materials do you use?**
A: All pieces are made with .925 sterling silver. Stones are genuine semi-precious gemstones unless otherwise noted in the listing. No plating, no nickel, no lead.

**Q: Will the jewelry tarnish?**
A: Sterling silver can develop a natural patina over time, but proper care prevents heavy tarnish. Every order includes a free polishing cloth. Store pieces in the included jewelry box when not wearing them, and avoid contact with perfume, lotion, and water.

**Q: How do I find my ring size?**
A: Use a flexible measuring tape or a strip of paper to measure the circumference of your finger in millimeters. Match the measurement to the size chart in each ring listing. If you are between sizes, go with the larger size. You can also visit any local jeweler for a free sizing.

### Pricing & Payment

**Q: Why are handmade pieces more expensive than mass-produced jewelry?**
A: Every piece is made individually by hand in Portland, OR using high-quality .925 sterling silver and genuine stones. There is no factory, no mass production, and no shortcuts. You are paying for craftsmanship, quality materials, and a piece that is built to last decades.

**Q: Do you offer discounts for multiple items?**
A: Orders of 3 or more pieces receive 10% off automatically at checkout. For bulk orders (10+ pieces for weddings, events, or gifts), message the shop for custom pricing.

**Q: What payment methods do you accept?**
A: Etsy accepts credit cards, debit cards, PayPal, Apple Pay, Google Pay, and Etsy gift cards. All payments are processed securely through Etsy's checkout system.

### Shipping & Delivery

**Q: How long does shipping take?**
A: Every piece is made to order, so processing takes 3-5 business days. After that, US orders ship free via USPS First Class (3-5 business days) or Priority Mail (1-3 business days for an additional $5). International orders ship in 7-14 business days.

**Q: Do you ship internationally?**
A: Yes. International shipping is a flat rate of $12 to most countries. International orders may be subject to customs duties or import taxes, which are the buyer's responsibility and vary by country.

**Q: How do I track my order?**
A: You will receive a tracking number by email and through Etsy once your order ships. You can track your package directly on USPS.com or through your Etsy account under "Purchases and Reviews."

### Support & Troubleshooting

**Q: What is your return policy?**
A: Unworn items can be returned within 14 days of delivery for a full refund. The item must be in its original condition and packaging. Contact the shop to initiate a return. Custom orders are final sale and cannot be returned.

**Q: What if my order arrives damaged?**
A: Message the shop with photos of the damage within 48 hours of delivery. Damaged items are replaced at no cost. You do not need to return the damaged piece.

### Trust & Credibility

**Q: Is sterling silver hypoallergenic?**
A: Sterling silver is generally safe for sensitive skin since it contains no nickel. However, if you have a known silver allergy, contact the shop before ordering to discuss alternative materials.

**Q: How do I care for my jewelry to keep it looking new?**
A: Store pieces in the included jewelry box when not wearing them. Use the free polishing cloth to remove any tarnish. Avoid wearing jewelry in the shower, pool, or while applying lotions and perfumes. With basic care, sterling silver jewelry lasts a lifetime.

---

## Anti-Patterns

- **DO NOT** start any answer with "Great question!" "Absolutely!" "Of course!" "That's a great question!" or any filler phrase — lead with the direct answer immediately
- **DO NOT** write FAQ answers longer than 4 sentences — if the answer needs more detail, the user needs a help article, not an FAQ entry
- **DO NOT** invent policies the user has not confirmed — never fabricate refund windows, shipping timelines, guarantee terms, or pricing details; if the information is missing, ask
- **DO NOT** skip the Pricing & Payment category — every FAQ must address cost and refund questions because these are the top 2 purchase blockers across all business types
- **DO NOT** use corporate jargon or legalese in answers — write "You can cancel anytime from your account settings" not "Subscription termination may be initiated through the account management portal"
- **DO NOT** write generic questions that apply to any business — every question should feel specific to this particular product or service
- **DO NOT** duplicate questions across categories — if "What is your refund policy?" appears in Pricing & Payment, do not also add "Can I get my money back?" in Trust & Credibility
- **DO NOT** present the FAQ without the Schema.org structured data — the JSON-LD snippet is a core deliverable, not an optional add-on
- **DO NOT** save files before the user has reviewed and approved the content — always present the full draft first

---

## Recovery and Troubleshooting

### User Cannot Describe Their Product or Service Clearly

1. Ask: "Can you share a link to your website, sales page, or product listing? I can pull the details from there."
2. If they provide a URL, use available tools to read any local files they may have (product descriptions, about pages, sales copy).
3. If no URL or files exist, ask the three minimum questions one at a time: "What do you sell?" then "Who buys it?" then "Where will this FAQ go?"
4. **If 3 attempts fail:** Suggest the user write a 2-3 sentence elevator pitch for their product first, then return to generate the FAQ.

### User Has No Existing Customer Questions

1. Generate questions based on the product description and target audience alone — most FAQ questions are predictable by business type.
2. Pull from common objection patterns for their niche:
   - Digital products: "Is this a scam?" "Will I actually get results?" "Is there a guarantee?"
   - E-commerce: "What if it doesn't fit?" "How long does shipping take?" "What's the return policy?"
   - Services: "How long does this take?" "What's included?" "Do you offer a free consultation?"
   - SaaS: "Is there a free trial?" "Can I cancel anytime?" "Is my data secure?"
3. Present the generated questions and ask: "Are these the kinds of questions your customers ask? What would you add or change?"

### User Wants More Than 25 Questions

1. Explain: "FAQs work best with 15-25 focused questions. Beyond that, customers stop reading and the page becomes overwhelming."
2. Offer to split into two deliverables: a concise FAQ section (15-20 questions) for the sales or product page, and a separate comprehensive help center document with the remaining questions organized by topic.
3. If they insist on a single long FAQ, proceed but add a table of contents at the top with anchor links to each category.

### User Rejects the Entire Draft

1. Ask: "What feels off — is it the questions themselves, the answers, the tone, or the organization?"
2. If tone is wrong: ask for 2-3 adjectives that describe their brand voice (casual, professional, playful, direct) and rewrite all answers.
3. If questions are wrong: ask the user to list their actual top 10 customer questions and rebuild around those.
4. If answers contain incorrect information: identify which specific details are wrong, get the correct information, and revise only the affected answers.
5. **If 3 revision rounds fail to satisfy:** Deliver the markdown FAQ as a working draft and suggest the user edit the answers directly, treating the structure and questions as the foundation.

### File Save Fails

1. Check if the target directory exists using `Glob`. If not, create it with `Write`.
2. If write permission is denied, ask the user for an alternative save path.
3. **Fallback:** Output the complete FAQ content directly in the conversation so the user can copy-paste it. Inform them: "I could not save the files, but here is the complete FAQ content. Copy it into your project manually."