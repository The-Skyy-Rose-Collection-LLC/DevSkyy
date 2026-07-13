---
name: transactional-email
description: "Writes transactional emails (order confirmations, shipping updates, receipts) with brand voice and upsell opportunities. Use when creating or improving automated emails triggered by customer actions."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Transactional Email

## When to Use This Skill

Use this skill when you need to:
- Write transactional emails that reflect your brand voice (not default platform templates)
- Create order confirmations, shipping notifications, receipts, and account emails
- Add strategic upsell or cross-sell elements to transactional messages
- Improve customer experience through better post-purchase communication

**DO NOT** use this skill for marketing emails, newsletters, or sales campaigns. This is for triggered, transactional messages.

---

## Core Principle

TRANSACTIONAL EMAILS HAVE THE HIGHEST OPEN RATES OF ANY EMAIL TYPE — USE THEM TO DELIVER INFORMATION CLEARLY AND BUILD THE RELATIONSHIP, NOT JUST CONFIRM THE TRANSACTION.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Business type** | "What do you sell? Physical product, digital product, service, SaaS?" | No default — must be provided |
| **Emails needed** | "Which transactional emails? Order confirmation, shipping, receipt, account creation, password reset?" | All standard types |
| **Brand voice** | "How should these sound?" | Warm, professional, on-brand |
| **Upsell opportunity** | "Do you have related products or a next step to suggest post-purchase?" | Yes — related products or content |
| **Platform** | "Where do these send from? Shopify, Stripe, custom, etc.?" | Any |

**GATE: Confirm scope before writing.**

---

## Phase 2: Outline

### Transactional Email Types

```
1. Order Confirmation — "We got your order"
2. Payment Receipt — "Here's your receipt"
3. Shipping Notification — "Your order is on the way"
4. Delivery Confirmation — "Your order has arrived"
5. Digital Product Delivery — "Here's your download"
6. Account Creation — "Welcome to your account"
7. Password Reset — "Reset your password"
```

**GATE: Confirm which emails to write.**

---

## Phase 3: Write

### Order Confirmation

```
## Order Confirmation

**Subject:** "Order confirmed — [Order #]"
**Preview text:** "Thanks for your purchase! Here's what happens next."

**Body:**

Hey [Name],

Your order is confirmed. Here's a summary:

**Order #[Number]**
**Date:** [Date]

| Item | Qty | Price |
|------|-----|-------|
| [Product name] | [Qty] | $[Price] |
| Shipping | — | $[Price] |
| **Total** | — | **$[Total]** |

**What happens next:**
[Step 1 — e.g., "We're preparing your order now."]
[Step 2 — e.g., "You'll get a shipping email with tracking within 24 hours."]

**Need help?** Reply to this email or visit [support link].

[Optional upsell section — see below]

Thanks for your order,
[Brand name]
```

### Digital Product Delivery

```
## Digital Product Delivery

**Subject:** "Your [product name] is ready to download"
**Preview text:** "Access your purchase now — here's your link."

**Body:**

Hey [Name],

Your purchase is ready! Click below to access [product name]:

[CTA BUTTON: "Download Now" or "Access Your [Product]"]

**What you got:**
- [Product name] — [1 sentence description]
- [Any bonuses included]

**Quick start:** [1-2 sentences on what to do first with the product]

**Need help?** Reply to this email — I personally read every message.

[Optional: "You might also like..." section]

Thanks for your purchase,
[Name / Brand]
```

### Shipping Notification

```
## Shipping Notification

**Subject:** "Your order is on the way — tracking inside"
**Preview text:** "Track your package: [carrier] #[tracking number]"

**Body:**

Hey [Name],

Great news — your order has shipped!

**Tracking number:** [Number]
**Carrier:** [Carrier name]
**Estimated delivery:** [Date range]

[CTA BUTTON: "Track Your Package"]

**What's in the box:**
- [Item 1]
- [Item 2 if multiple]

When it arrives, we'd love to hear what you think. [Link to review page or "reply to this email"]

[Sign-off]
```

### Account Creation

```
## Account Welcome

**Subject:** "Your [Brand] account is ready"
**Preview text:** "Here's how to get started."

**Body:**

Welcome to [Brand], [Name]!

Your account is set up and ready to go. Here's how to get started:

**Step 1:** [First action — e.g., "Log in and set up your profile"]
**Step 2:** [Second action — e.g., "Explore [feature]"]
**Step 3:** [Third action — e.g., "Check out our getting started guide"]

[CTA BUTTON: "Log In to Your Account"]

If you have any questions, our support team is here: [support link or email]

Welcome aboard,
[Brand name]
```

### Password Reset

```
## Password Reset

**Subject:** "Reset your password"
**Preview text:** "Click below to set a new password."

**Body:**

Hi [Name],

We received a request to reset your password. Click below to create a new one:

[CTA BUTTON: "Reset My Password"]

This link expires in [X minutes/hours].

If you didn't request this, you can safely ignore this email. Your password will remain unchanged.

— [Brand name]
```

### Upsell Section Template

Add to any transactional email where appropriate:

```
## You Might Also Like

[1-2 related products or resources with brief descriptions and links]

- **[Product name]** — [One sentence on what it does and why it's relevant] [Link]
- **[Product name]** — [One sentence] [Link]
```

Rules for transactional upsells:
- Keep it subtle — 1-2 suggestions max
- Placed BELOW the transaction details (info first, upsell second)
- Relevant to what they just bought
- Never more than 20% of the email's content

---

## Phase 4: Polish

### 1. Transactional Email Checklist

```
## Checklist (per email)

- [ ] Subject line clearly states what the email is about
- [ ] Critical information (order details, tracking, download link) is above the fold
- [ ] Brand voice is consistent with marketing emails (not robotic)
- [ ] Next steps are clearly stated
- [ ] Support/help option is visible
- [ ] Upsell section (if included) is relevant and subtle
- [ ] Email works on mobile (single-column, large buttons)
- [ ] All dynamic fields ([Name], [Order #]) are correctly mapped
- [ ] Reply-to address goes to a monitored inbox
- [ ] Legal requirements met (business address, unsubscribe if marketing content included)
```

### 2. Testing Plan

- Send test emails to yourself on desktop and mobile before going live
- Verify all dynamic fields populate correctly
- Click every link and button to ensure they work
- Check that the email lands in Primary inbox (not Promotions or Spam)

---

## Example: Transactional Emails for a Digital Course

```
Order confirmation: "Your enrollment in [Course Name] is confirmed!"
  - Course name, price, receipt link
  - "What happens next: Check your email for login details within 5 minutes."

Digital delivery: "Your course is live — start with Module 1"
  - Direct link to course platform
  - Quick start guide: "Watch the 5-minute orientation video first."
  - Upsell: "Students who add the workbook complete the course 2x faster."

Account creation: "Welcome to the [Course Name] student portal"
  - Login credentials
  - First 3 steps to get started
  - Support channel info
```

---

## Anti-Patterns

- **Robotic default templates** — "Your order #48291 has been processed. Transaction ID: TXN-2024-8819" reads like a system log. Add brand voice.
- **No next steps** — telling the customer what happened without telling them what happens NEXT creates anxiety.
- **Aggressive upselling** — a transactional email that is 50% upsell feels exploitative. Keep upsells to 20% max.
- **No support path** — every transactional email should tell the customer how to get help.
- **Broken dynamic fields** — "Hi [FIRST_NAME]" or "[ORDER_TOTAL]" in production is embarrassing. Always test.
- **Different voice than marketing** — if your marketing is warm and personal, your transactional emails should not sound like a robot wrote them.

---

## Recovery

- **Platform does not allow custom templates:** Customize what you can (subject line, body text). Supplement with a personal follow-up email from your marketing platform.
- **No upsell ideas:** Skip the upsell section. Not every transactional email needs one.
- **Emails going to spam:** Check that the sending domain is authenticated (SPF, DKIM, DMARC). Reduce image-to-text ratio.
- **Customers reply with issues:** Ensure the reply-to address is monitored. Set up an auto-response acknowledging receipt if response time is over 4 hours.
- **Dynamic data not available:** Use conditional logic in the template — show the section only if the data exists.
