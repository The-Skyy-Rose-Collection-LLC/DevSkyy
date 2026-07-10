---
name: rental-listing
description: "Writes rental property listings with amenity highlights, qualification requirements, and application instructions."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Rental Listing

## When to Use This Skill

Use this skill when you need to:
- Write a rental listing that attracts qualified tenants quickly
- Highlight amenities, lease terms, and qualification requirements clearly
- Create listings optimized for Zillow, Apartments.com, Craigslist, or Facebook
- Reduce unqualified inquiries by setting clear expectations upfront

**DO NOT** use this skill for property sale listings (use property-listing), commercial lease listings, or vacation rental descriptions. This is for residential rental listings.

---

## Core Principle

A RENTAL LISTING SHOULD ATTRACT THE RIGHT TENANTS AND REPEL THE WRONG ONES — CLARITY ON TERMS, REQUIREMENTS, AND EXPECTATIONS SAVES EVERYONE TIME.

---

## Phase 1: Property Details

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Property address** | "What is the property address or general area?" | No default — must be provided |
| **Beds/baths/sqft** | "How many bedrooms, bathrooms, and approximate square footage?" | No default — must be provided |
| **Monthly rent** | "What is the monthly rent?" | No default — must be provided |
| **Lease terms** | "Lease length, security deposit, move-in date?" | 12-month lease, 1 month deposit |
| **Pet policy** | "Are pets allowed? Any restrictions or deposits?" | No pets |
| **Key amenities** | "What amenities are included — parking, laundry, utilities, appliances?" | No default — must be provided |

**GATE: Confirm all property details and terms before writing the listing.**

---

## Phase 2: Listing Copy

### Listing Structure

```
## [Beds]BR/[Baths]BA [Property Type] in [Neighborhood] — $[Rent]/mo

**Available:** [Date]
**Lease:** [Term]
**Deposit:** $[Amount]

### The Space

[2-3 sentences describing the property. Lead with the best feature —
natural light, updated kitchen, spacious layout, great views. Describe
what it feels like to live there, not just the specs.]

### Features & Amenities

- [Feature 1 — be specific: "In-unit washer/dryer" not "laundry"]
- [Feature 2]
- [Feature 3]
- [Feature 4]
- [Feature 5]
- [Feature 6]

### Utilities & Included

- [What is included in rent — water, trash, internet, etc.]
- [What tenant pays — electricity, gas, etc.]

### Location

[2-3 sentences about the neighborhood. Mention proximity to transit,
grocery stores, parks, restaurants, and major employers.]

### Requirements

- Minimum credit score: [Score]
- Income requirement: [X]x monthly rent (verifiable)
- Background and credit check required
- [Pet policy]
- No smoking

### How to Apply

[Step-by-step application instructions. Make it clear and simple.]

1. [Schedule a showing: contact method]
2. [Submit application: link or instructions]
3. [Application fee: amount]
4. [Required documents: pay stubs, ID, references]
```

---

## Phase 3: Platform Optimization

### Platform-Specific Tips

| Platform | Optimization |
|----------|-------------|
| Zillow/Trulia | Fill every field in the listing form — completeness boosts ranking. Use all photo slots. |
| Apartments.com | Include virtual tour or video walkthrough for higher engagement. |
| Craigslist | Lead with price and beds in the title. Include neighborhood name. Renew every 48 hours. |
| Facebook Marketplace | Use bright, well-lit cover photo. Respond to inquiries within 1 hour. |
| Your website | Include an application link and showing calendar for self-scheduling. |

### Photo Guidelines

| Photo | What to Capture |
|-------|----------------|
| 1 | Exterior / curb appeal — best angle, good lighting |
| 2 | Living room — widest angle showing space and light |
| 3 | Kitchen — show counters, appliances, and storage |
| 4 | Primary bedroom — include closet and windows |
| 5 | Bathroom — clean, well-lit, show fixtures |
| 6 | Additional rooms, patio, parking, or amenity spaces |

### Title Formulas

- "[Beds]BR [Type] in [Neighborhood] — $[Rent] — [Top Feature]"
- "Newly Renovated [Beds]BR with [Feature] — Available [Date]"
- "$[Rent] | [Beds]BR/[Baths]BA | [Neighborhood] | [Feature]"

---

## Phase 4: Inquiry Management

### Pre-Screening Questions

Ask before scheduling a showing:
1. When are you looking to move in?
2. How many people will occupy the unit?
3. Do you have any pets?
4. What is your approximate household income?
5. Have you been evicted or had a lease terminated early?

### Response Template

```
Subject: Re: [Property Address] — Showing Available

Hi [Name],

Thanks for your interest in [address]. Here are the key details:

- Rent: $[amount]/month
- Available: [Date]
- Lease: [Term]
- Pets: [Policy]

To schedule a showing, [instructions — pick a time, reply with availability, etc.]

Before applying, please note:
- Minimum income: $[amount]/month (3x rent)
- Credit and background check required ($[fee])
- [Any other key requirements]

Let me know if you have questions.

[Your name]
[Phone]
```

---

## Anti-Patterns

- **Hiding the rent** — always include the price. Listings without rent get fewer serious inquiries.
- **No qualification requirements** — omitting income and credit requirements wastes time on unqualified applicants.
- **Dark or few photos** — listings with fewer than 5 photos get significantly less engagement.
- **Discriminatory language** — never reference preferred tenant demographics. Describe the property, not the ideal renter.
- **Burying important terms** — pet policy, parking, and utility responsibilities should be easy to find, not hidden in a paragraph.
- **Responding slowly** — renters move fast. Respond to inquiries within 2-4 hours during business days.

---

## Recovery

- **Low inquiry volume:** Improve photos (natural light, wide angles), adjust price to market, and expand to more listing platforms.
- **Many unqualified applicants:** Add clearer qualification requirements to the listing. Pre-screen before showing.
- **Listing has been up too long:** Refresh photos, rewrite the description with a new angle, and consider adjusting the price.
- **Fair housing concern:** Review all language for compliance. Remove any reference to preferred tenant characteristics. Focus only on property features and objective requirements.
- **Scam concerns from applicants:** Include your real name, brokerage or management company, and offer in-person showings only.
