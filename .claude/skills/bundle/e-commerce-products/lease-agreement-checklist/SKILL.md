---
name: lease-agreement-checklist
description: "Creates lease agreement review checklists ensuring all essential terms, disclosures, and addenda are included."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Lease Agreement Checklist

## When to Use This Skill

Use this skill when you need to:
- Review a residential lease agreement for completeness before signing
- Ensure all essential terms, disclosures, and addenda are included
- Identify missing clauses that could create problems during the tenancy
- Create a standardized checklist for consistent lease preparation

**DO NOT** use this skill for drafting lease agreements from scratch, commercial lease review, or legal advice. This is a completeness checklist — always consult an attorney for legal review.

---

## Core Principle

A COMPLETE LEASE PROTECTS BOTH LANDLORD AND TENANT — EVERY MISSING CLAUSE IS A POTENTIAL DISPUTE WAITING TO HAPPEN.

---

## Phase 1: Lease Context

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Role** | "Are you the landlord or tenant reviewing this lease?" | Landlord |
| **State** | "What state is the property in?" | No default — state law affects requirements |
| **Property type** | "Single-family, apartment, condo, duplex?" | Single-family |
| **Lease term** | "Fixed-term or month-to-month?" | 12-month fixed |
| **Special circumstances** | "Any unusual terms — furnished, utilities included, roommates, pets?" | Standard unfurnished |

**GATE: Confirm role and jurisdiction before applying the checklist.**

---

## Phase 2: Essential Terms Checklist

### Party & Property Information

- [ ] Full legal names of all tenants (adults)
- [ ] Landlord/management company legal name and contact
- [ ] Complete property address including unit number
- [ ] Lease start date and end date
- [ ] Move-in date (if different from lease start)

### Financial Terms

- [ ] Monthly rent amount
- [ ] Rent due date (typically 1st of the month)
- [ ] Accepted payment methods
- [ ] Grace period specified (number of days)
- [ ] Late fee amount and when it applies
- [ ] Security deposit amount
- [ ] Security deposit return timeline and conditions
- [ ] Any non-refundable fees (application, cleaning, admin)
- [ ] Prorated rent for partial first/last month (if applicable)
- [ ] Rent increase terms and notice requirements

### Occupancy & Use

- [ ] Maximum number of occupants
- [ ] Guest policy and limitations
- [ ] Permitted use (residential only)
- [ ] Restrictions on home businesses
- [ ] Subletting and assignment policy
- [ ] Quiet hours or noise restrictions

---

## Phase 3: Policies & Responsibilities

### Maintenance & Repairs

- [ ] Landlord maintenance responsibilities defined
- [ ] Tenant maintenance responsibilities defined
- [ ] Maintenance request procedure (how to submit)
- [ ] Emergency maintenance contact and procedure
- [ ] Lawn care, snow removal, and exterior maintenance assigned
- [ ] Tenant liability for damage beyond normal wear and tear

### Utilities & Services

- [ ] Which utilities landlord pays
- [ ] Which utilities tenant pays
- [ ] Utility transfer responsibility and timeline
- [ ] Shared utility arrangements (if multi-unit)

### Pets

- [ ] Pet policy clearly stated (allowed/not allowed)
- [ ] Pet deposit or fee amount
- [ ] Monthly pet rent (if applicable)
- [ ] Breed, size, or number restrictions
- [ ] Pet damage liability

### Insurance

- [ ] Renter's insurance requirement stated
- [ ] Minimum coverage amount specified
- [ ] Proof of insurance deadline
- [ ] Landlord named as interested party (if required)

---

## Phase 4: Legal Protections & Addenda

### Termination & Renewal

- [ ] Early termination clause and penalties
- [ ] Lease-breaking fee or buyout option
- [ ] Move-out notice period (30/60 days)
- [ ] Renewal terms (auto-renew, month-to-month conversion, or expire)
- [ ] Landlord's right to terminate and required notice
- [ ] Move-out inspection procedure
- [ ] Property condition documentation (move-in/move-out)

### Required Disclosures (Verify by State)

- [ ] Lead-based paint disclosure (pre-1978 properties — federal requirement)
- [ ] Mold disclosure (where required)
- [ ] Bed bug disclosure (where required)
- [ ] Sex offender registry notification
- [ ] Flood zone disclosure
- [ ] Known defects or hazards
- [ ] Asbestos disclosure (where required)
- [ ] Shared utility disclosure (where required)

### Common Addenda

- [ ] Move-in/move-out condition report
- [ ] Pet addendum (if pets allowed)
- [ ] Parking addendum (assigned spots, rules)
- [ ] Smoking policy addendum
- [ ] Mold prevention addendum
- [ ] HOA rules attachment (if applicable)
- [ ] Appliance inventory list
- [ ] Key/access device inventory

### Signatures & Execution

- [ ] All adult tenants have signed
- [ ] Landlord or authorized agent has signed
- [ ] Date of execution
- [ ] Copies provided to all parties
- [ ] All addenda initialed and attached

---

## Review Summary Template

```
## Lease Review Summary

**Property:** [Address]
**Reviewed by:** [Name]
**Date:** [Date]

### Status: [Complete / Missing Items / Needs Legal Review]

### Missing or Incomplete Items:
1. [Item] — [Why it matters]
2. [Item] — [Why it matters]

### Items Needing Clarification:
1. [Clause] — [What is unclear]

### Recommendations:
- [Action item 1]
- [Action item 2]
```

---

## Anti-Patterns

- **Using a generic online template without state customization** — lease laws vary dramatically by state and even city. Generic templates miss required local provisions.
- **No move-in condition report** — without documented property condition at move-in, security deposit disputes are unresolvable.
- **Vague maintenance responsibilities** — "Tenant is responsible for upkeep" without specifics leads to disagreements.
- **Missing disclosures** — failing to include required disclosures can void lease provisions or create legal liability.
- **No early termination clause** — life happens. Having a clear buyout process is better than a messy breach.

---

## Recovery

- **Lease already signed with missing terms:** Create an addendum covering the missing items. Both parties sign.
- **State-specific requirements unknown:** Research your state's landlord-tenant statutes or consult a local real estate attorney.
- **Tenant disputes a lease term:** Reference the specific clause. If the clause is genuinely ambiguous, negotiate a reasonable interpretation and document it.
- **Using an outdated lease template:** Review and update annually. Laws change, and your lease should reflect current requirements.
- **Multiple properties with different lease versions:** Standardize to one template per property type and jurisdiction. Customize only the property-specific details.
