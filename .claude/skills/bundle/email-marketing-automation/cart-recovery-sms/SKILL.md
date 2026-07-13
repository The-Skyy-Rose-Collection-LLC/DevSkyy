---
name: cart-recovery-sms
description: "Writes SMS cart recovery messages with timing, personalization tokens, and compliance disclaimers. Use when you need to recover abandoned carts via text message."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Cart Recovery SMS

## When to Use This Skill

Use this skill when you need to:
- Write SMS messages that recover abandoned shopping carts
- Design a timed SMS sequence triggered by cart abandonment
- Include personalization tokens and dynamic product references
- Ensure compliance with SMS marketing regulations (TCPA, GDPR)

**DO NOT** use this skill for email cart recovery, general SMS marketing campaigns, or transactional order updates. This is specifically for SMS-based cart abandonment recovery.

---

## Core Principle

SMS IS PERSONAL TERRITORY — EVERY MESSAGE MUST FEEL LIKE A HELPFUL NUDGE FROM A BRAND THEY TRUST, NOT AN INTRUSION INTO THEIR PHONE.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product type** | "What do you sell? (physical, digital, service)" | No default — must be provided |
| **Average cart value** | "What's the typical abandoned cart value?" | $50-100 |
| **Incentive available** | "Can you offer a discount or free shipping to recover?" | 10% discount code |
| **Brand voice** | "Casual, professional, playful?" | Friendly and casual |
| **SMS platform** | "What SMS tool are you using?" | Platform-agnostic |
| **Opt-in method** | "How did customers consent to SMS?" | Checkout opt-in checkbox |

**GATE: Confirm the brief before writing messages.**

---

## Phase 2: Message Sequence Design

### Timing Framework

```
## Cart Recovery SMS Sequence

Message 1 — 30 minutes after abandonment
Purpose: Gentle reminder, no incentive
Tone: Helpful

Message 2 — 4 hours after abandonment
Purpose: Address common objection or add social proof
Tone: Conversational

Message 3 — 24 hours after abandonment
Purpose: Offer incentive (discount or bonus)
Tone: Generous

Message 4 (optional) — 48 hours after abandonment
Purpose: Last chance, urgency on expiring incentive
Tone: Direct
```

### Exit Conditions

- Customer completes purchase → stop all messages immediately
- Customer replies STOP → remove from sequence and all SMS marketing
- No response after Message 3/4 → end sequence, do not add to future cart recovery

**GATE: Approve the sequence timing before writing messages.**

---

## Phase 3: Write Messages

### SMS Writing Rules

- **160 characters or less** per message (avoid multi-part messages)
- **Include brand name** in the first message so they know who it's from
- **One link per message** — shortened URL to their cart
- **Personalization tokens:** {first_name}, {product_name}, {cart_url}
- **Opt-out instructions** in the first message: "Reply STOP to opt out"

### Message Templates

**Message 1 (30 min):**
```
Hey {first_name}! You left something in your cart at [Brand]. Still interested? Complete your order here: {cart_url} Reply STOP to opt out
```

**Message 2 (4 hours):**
```
{first_name}, your {product_name} is still waiting. Hundreds of happy customers love theirs. Grab it before it's gone: {cart_url}
```

**Message 3 (24 hours):**
```
Still thinking it over? Here's 10% off your cart at [Brand]. Use code SAVE10 at checkout: {cart_url} Expires in 24hrs.
```

**Message 4 (48 hours):**
```
Last chance, {first_name}. Your 10% off code expires tonight. Complete your order: {cart_url}
```

---

## Phase 4: Polish

### 1. Compliance Checklist

- [ ] Customers opted in to SMS marketing explicitly (not pre-checked boxes)
- [ ] First message includes brand name identification
- [ ] STOP opt-out instructions included in first message
- [ ] All messages sent during compliant hours (8am-9pm recipient's timezone)
- [ ] Discount codes have real expiration dates
- [ ] Privacy policy covers SMS marketing

### 2. Platform Setup Notes

- Link shortener configuration for tracking
- Personalization token mapping from cart data
- Purchase event trigger to stop sequence
- Quiet hours configuration by timezone

### 3. Performance Benchmarks

- SMS cart recovery rate: 10-15% (vs. 3-5% for email alone)
- Click-through rate: 20-30%
- Opt-out rate per message: under 2% (above this, reduce frequency)
- Revenue per message sent

---

## Anti-Patterns

- **Sending SMS without explicit consent** — this violates TCPA and can result in $500-$1,500 per message in fines.
- **Messages over 160 characters** — multi-part messages feel spammy and cost more.
- **No opt-out option** — legally required and must be honored immediately.
- **Sending at 2am** — respect quiet hours. Most platforms enforce 8am-9pm local time.
- **Four messages with no incentive** — if you are not willing to offer a discount, limit to 2 messages.
- **Generic messages** — "You forgot something!" without the product name or brand feels like spam.

---

## Recovery

- **No incentive available:** Remove Messages 3-4. Use only the reminder and social proof messages. Two messages max.
- **User unsure about compliance:** Provide a compliance overview but recommend consulting a legal professional for their specific market (US/TCPA, EU/GDPR, CA/CASL).
- **High opt-out rate:** Reduce to 2 messages, extend timing (1 hour and 24 hours), and soften the tone.
- **Low cart value (under $20):** Single SMS message at 1 hour is sufficient. The cost of multiple messages may not justify the recovery value.
