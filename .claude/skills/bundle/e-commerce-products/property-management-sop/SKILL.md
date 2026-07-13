---
name: property-management-sop
description: "Builds property management SOPs for maintenance requests, inspections, rent collection, and tenant communication."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Property Management SOP

## When to Use This Skill

Use this skill when you need to:
- Create standard operating procedures for managing rental properties
- Systematize maintenance requests, inspections, and rent collection
- Build tenant communication templates for common situations
- Document processes for consistent property management at scale

**DO NOT** use this skill for property acquisition analysis, construction management, or HOA governance documents. This is for day-to-day rental property management operations.

---

## Core Principle

CONSISTENT PROPERTY MANAGEMENT PROCESSES PROTECT YOUR INVESTMENT, KEEP TENANTS HAPPY, AND REDUCE EMERGENCIES — DOCUMENTING EVERY PROCEDURE ENSURES NOTHING FALLS THROUGH THE CRACKS.

---

## Phase 1: SOP Scope

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Number of properties** | "How many rental units do you manage?" | 1-5 units |
| **Property types** | "Single-family, multi-family, or mixed?" | Single-family |
| **Self-managed or team** | "Do you manage alone or with a team/VA?" | Self-managed |
| **Current pain points** | "What property management tasks cause the most issues?" | Maintenance coordination and rent collection |
| **Tools used** | "What software do you use — Buildium, AppFolio, spreadsheets?" | Spreadsheets and email |

**GATE: Confirm scope and pain points before building SOPs.**

---

## Phase 2: Core SOPs

### SOP 1: Rent Collection

```
## Rent Collection SOP

**Rent due:** 1st of each month
**Grace period:** [3-5] days
**Late fee:** $[amount] or [X]% of monthly rent

### Process:
1. Rent is due on the 1st — no action needed if paid on time
2. Day 2: If not received, send a friendly reminder via text/email
3. Day [grace period + 1]: Apply late fee and send formal late notice
4. Day 10: Phone call to discuss payment plan if needed
5. Day 15: Send pay-or-quit notice (consult local requirements)
6. Day 30+: Begin eviction proceedings if no payment or arrangement

### Reminder Template:
"Hi [Name], this is a friendly reminder that rent of $[amount] was due
on [date]. Please submit payment at your earliest convenience. Let me
know if you have any questions. — [Your name]"

### Late Notice Template:
"Dear [Name], as of [date], your rent payment of $[amount] has not been
received. A late fee of $[amount] has been applied per your lease agreement.
Total amount due: $[rent + late fee]. Please submit payment by [date]
to avoid further action."
```

### SOP 2: Maintenance Requests

```
## Maintenance Request SOP

### Receiving Requests:
- Tenants submit requests via [email/portal/text]
- All requests logged with date, description, and unit
- Acknowledge receipt within [4] hours

### Priority Levels:
| Priority | Response Time | Examples |
|----------|--------------|---------|
| Emergency | Within 2 hours | Water leak, no heat in winter, gas smell, lockout |
| Urgent | Within 24 hours | Broken appliance, AC failure in summer, plumbing issue |
| Routine | Within 3-5 days | Cosmetic repairs, minor fixture issues |
| Scheduled | Next inspection cycle | Non-urgent improvements, painting |

### Process:
1. Receive and log the request
2. Assess priority level
3. Contact tenant with estimated timeline
4. Dispatch vendor or schedule personal visit
5. Complete repair and document (photos, invoice, notes)
6. Follow up with tenant to confirm resolution
7. File documentation and update maintenance log

### Emergency Contact List:
- Plumber: [Name, Phone]
- Electrician: [Name, Phone]
- HVAC: [Name, Phone]
- Locksmith: [Name, Phone]
- General handyman: [Name, Phone]
```

### SOP 3: Property Inspections

```
## Property Inspection SOP

### Inspection Types:
| Type | Frequency | Notice Required |
|------|-----------|----------------|
| Move-in | Before tenant occupancy | N/A |
| Routine | Every [6] months | [24-48] hours written notice |
| Drive-by | Monthly | No interior access — exterior only |
| Move-out | Within [48] hours of vacancy | N/A |

### Inspection Checklist:
- [ ] Exterior: roof, gutters, siding, landscaping, driveway
- [ ] Interior: walls, ceilings, floors (damage, cleanliness)
- [ ] Kitchen: appliances, counters, cabinets, plumbing
- [ ] Bathrooms: fixtures, caulking, ventilation, plumbing
- [ ] HVAC: filter condition, system function
- [ ] Smoke/CO detectors: test and replace batteries
- [ ] Windows and doors: locks, seals, screens
- [ ] Safety: fire extinguisher, handrails, electrical outlets
- [ ] Lease compliance: occupants, pets, prohibited items

### Documentation:
- Date-stamped photos of every room
- Written notes on condition and any concerns
- Comparison to previous inspection or move-in report
- Tenant notified of any lease violations or required actions
```

---

## Phase 3: Tenant Communication

### Communication Templates

**Lease Renewal Notice (60-90 days before expiration):**
```
Dear [Name], your lease at [address] expires on [date]. We'd like to
offer you a renewal at $[new rent]/month for [term]. Please confirm
by [date] if you'd like to renew. If you plan to move out, please
provide [30/60] days written notice per your lease terms.
```

**Maintenance Completion:**
```
Hi [Name], the [repair type] at your unit has been completed as of [date].
Please let me know if the issue is fully resolved or if you notice any
further problems. Thank you for your patience.
```

**Lease Violation Notice:**
```
Dear [Name], during our recent inspection/observation, we identified
[specific violation] at [address]. Per Section [X] of your lease
agreement, [describe the requirement]. Please [corrective action]
within [X] days. If you have questions, please contact us.
```

---

## Phase 4: Systems & Documentation

### Record Keeping

Maintain these records for every property:

| Document | Retention Period |
|----------|-----------------|
| Lease agreements | Duration of tenancy + [X] years |
| Maintenance logs | 3-5 years |
| Inspection reports | Duration of tenancy + move-out |
| Rent payment records | 7 years (tax purposes) |
| Communication logs | Duration of tenancy + 2 years |
| Vendor invoices | 7 years (tax purposes) |

### Annual Calendar

| Month | Task |
|-------|------|
| January | Review insurance policies, update emergency contacts |
| March | Schedule spring inspections and preventive maintenance |
| May | HVAC servicing before summer |
| June | Mid-year financial review per property |
| September | Schedule fall inspections, winterization prep |
| October | Send lease renewal notices for December/January expirations |
| November | HVAC servicing before winter, gutter cleaning |
| December | Year-end financial summary, tax prep |

---

## Anti-Patterns

- **No documentation** — verbal agreements and memory-based management create legal liability and operational chaos.
- **Inconsistent enforcement** — applying rules differently across tenants invites fair housing complaints.
- **Ignoring maintenance requests** — delayed repairs escalate into expensive problems and tenant turnover.
- **No emergency plan** — not knowing who to call at 2 AM when a pipe bursts costs time and money.
- **Skipping inspections** — small issues caught early prevent major expenses later.

---

## Recovery

- **Inherited a poorly managed property:** Conduct a full inspection, document current conditions, and introduce SOPs with the next lease cycle.
- **Tenant refuses inspection access:** Reference the lease clause allowing inspections with proper notice. Document the refusal in writing.
- **Chronic late payers:** Enforce late fees consistently. Offer auto-pay setup. If it continues, consider non-renewal at lease end.
- **Vendor quality issues:** Build a roster of 2-3 vendors per trade. Get multiple quotes and check references before adding to your list.
- **Scaling beyond self-management:** Transition to property management software and consider hiring a VA or property manager when you exceed 10 units.
