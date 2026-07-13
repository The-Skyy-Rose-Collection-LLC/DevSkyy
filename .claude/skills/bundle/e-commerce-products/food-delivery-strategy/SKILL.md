---
name: food-delivery-strategy
description: "Plans food delivery operations with platform selection, packaging, pricing, and quality control procedures. Use when launching or optimizing restaurant delivery service."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Food Delivery Strategy

## When to Use This Skill

Use this skill when you need to:
- Launch or optimize food delivery operations for a restaurant
- Select and manage third-party delivery platforms
- Design delivery-specific menus, packaging, and pricing strategies
- Build quality control procedures for delivery orders

**DO NOT** use this skill for meal prep or meal kit businesses, grocery delivery, or catering logistics. This is for restaurant delivery operations.

---

## Core Principle

DELIVERY IS A DIFFERENT PRODUCT THAN DINE-IN — THE FOOD MUST ARRIVE LOOKING AND TASTING AS INTENDED. IF A DISH DOES NOT TRAVEL WELL, IT DOES NOT BELONG ON THE DELIVERY MENU.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Restaurant type** | "What type of restaurant and cuisine?" | No default — must be provided |
| **Current delivery status** | "Do you currently offer delivery? Through which platforms?" | Not yet — planning to launch |
| **Menu suitability** | "Which menu items travel well? Which do not?" | Unknown — needs evaluation |
| **Delivery radius** | "How far are you willing to deliver?" | 5-mile radius |
| **Capacity** | "Can your kitchen handle delivery volume on top of dine-in?" | Limited — need to manage carefully |
| **Budget** | "Are you willing to absorb platform commissions or pass costs to customers?" | Pass through as delivery fee markup |

**GATE: Confirm the brief before building the strategy.**

---

## Phase 2: Platform Strategy

### Platform Comparison

| Platform | Commission | Reach | Best For |
|----------|-----------|-------|----------|
| **DoorDash** | 15-30% | Largest US reach | Maximum exposure |
| **Uber Eats** | 15-30% | Strong urban presence | Urban markets |
| **Grubhub** | 15-30% | Northeast strong | Regional focus |
| **Direct (own website)** | 0% + processing fees | Your customers | Repeat customers, higher margins |
| **Toast/Square delivery** | Lower commission | Integrated with POS | Existing Toast/Square users |

### Platform Strategy Options

| Strategy | Description | Margin Impact |
|----------|-------------|---------------|
| **Multi-platform** | List on 2-3 platforms for maximum reach | Lowest margin, highest volume |
| **Platform + direct** | Use 1 platform for discovery, push repeat orders to direct | Balanced |
| **Direct only** | Own ordering website or app | Highest margin, requires marketing |

### Pricing Strategy for Delivery

- **Option 1:** Raise delivery menu prices 15-20% to offset commissions
- **Option 2:** Keep same prices, absorb the commission (builds volume)
- **Option 3:** Create delivery-exclusive combo deals with built-in margin

**GATE: Confirm platform and pricing strategy before designing the delivery menu.**

---

## Phase 3: Operations

### Delivery Menu Design

Evaluate each menu item for delivery suitability:

| Criteria | Pass | Fail |
|----------|------|------|
| Holds temperature for 30 minutes | Yes | Disqualified |
| Does not get soggy or wilt | Yes | Modify or remove |
| Looks presentable after transport | Yes | Modify or remove |
| Can be reheated without quality loss | Bonus | Not required |
| Packs efficiently | Yes | Modify container |

**Menu rules:**
- Remove items that do not travel well (crispy items that go soggy, items that require precise plating)
- Add delivery-friendly items (bowls, wraps, sealed containers)
- Create delivery-only combos that increase average order value
- Offer family-size or multi-person options for higher ticket

### Packaging Standards

```
## Packaging Requirements

| Food Type | Container | Seal | Notes |
|-----------|-----------|------|-------|
| Hot entrees | Microwave-safe, vented | Tamper-evident sticker | Vent prevents sogginess |
| Cold items | Separate container | Sealed lid | Keep away from hot items |
| Sauces/dressings | Small sealed cups | Snap lid | Always on the side |
| Drinks | Sealed cups with lids | Bag separately | Upright in carrier |
| Sides | Compartmentalized or separate | Sealed | Label each container |

**Additional:**
- Include napkins, utensils, and condiments in every order
- Add a branded sticker or thank-you card
- Use tamper-evident seals on all containers
- Bag hot and cold items separately
```

### Quality Control Process

```
## Delivery Order QC Checklist

Before handing off to driver:
- [ ] All items in the order are present (check against ticket)
- [ ] Hot food is hot, cold food is cold
- [ ] Sauces and dressings are packaged separately
- [ ] All containers are sealed with tamper-evident stickers
- [ ] Utensils, napkins, and condiments included
- [ ] Order is bagged correctly (hot/cold separated)
- [ ] Receipt or order summary visible on the bag
```

---

## Phase 4: Polish

### 1. Delivery-Specific Metrics

```
## Delivery Metrics

- **Delivery order volume:** Orders per day/week
- **Average delivery ticket:** Target 20-30% higher than dine-in
- **Delivery revenue as % of total:** Track growth over time
- **Platform commission costs:** Actual $ paid per platform per month
- **Order accuracy rate:** % of orders with no errors (target: 98%+)
- **Delivery rating:** Platform rating and review scores
- **Refund/complaint rate:** % of orders with issues (target: under 2%)
- **Prep-to-pickup time:** Average minutes from order to driver handoff
```

### 2. Customer Experience Touches

- Include a handwritten or printed thank-you card in every delivery
- Add a QR code linking to your direct ordering site (saves future commissions)
- Offer a small loyalty incentive for direct orders: "Order from our website next time and save 10%"
- Respond to every delivery review on platforms

### 3. Quality Checklist

```
## Delivery Strategy Checklist

- [ ] Delivery platforms selected with commission rates understood
- [ ] Delivery menu curated (items that travel well only)
- [ ] Delivery pricing strategy set (markup, same price, or combos)
- [ ] Packaging standards documented with container specs
- [ ] Quality control checklist posted at the delivery station
- [ ] Kitchen capacity plan accounts for delivery + dine-in volume
- [ ] Delivery metrics defined and tracked weekly
- [ ] Direct ordering option available (own website or system)
- [ ] Customer experience touches planned (thank-you cards, loyalty offer)
- [ ] Staff trained on delivery order workflow
```

---

## Example

**Restaurant:** Fast-casual Thai, launching delivery

**Delivery menu adjustments:**
- Removed: Crispy spring rolls (get soggy in transit)
- Modified: Pad Thai packaged with sauce on the side (prevents mushiness)
- Added: Thai Bowl combo (rice + protein + sauce, $14) — delivery-exclusive
- Added: Family Pack (4 bowls + appetizer, $48) — delivery-exclusive

**Pricing:** 18% markup on delivery platforms. Same price on direct ordering website. Direct ordering promoted with "Save 15% — order from our website" card in every delivery bag.

---

## Anti-Patterns

- **Putting your entire menu on delivery** — not every dish travels well. A soggy delivery order loses a customer permanently.
- **Ignoring packaging** — food that arrives cold, spilled, or mixed together gets a 1-star review. Invest in proper containers.
- **No quality check before handoff** — wrong items and missing utensils are the top delivery complaints. Check every bag.
- **Same prices as dine-in on platforms** — you are paying 20-30% commission. Either raise prices or accept the margin hit consciously.
- **Not promoting direct ordering** — every delivery platform order costs you 20-30% in commission. Push customers to your own ordering channel.

---

## Recovery

- **Low delivery ratings:** Audit the last 10 negative reviews. Most complaints are: wrong items, cold food, or missing items. Fix the QC process.
- **Platform commissions are too high:** Negotiate rates (possible at higher volume), raise delivery prices, or push customers to direct ordering.
- **Kitchen cannot handle delivery volume:** Set delivery order limits during peak dine-in hours. Stagger availability.
- **Food quality suffers in transit:** Redesign packaging. Test by ordering your own delivery and eating it 30 minutes later. Fix what does not work.
