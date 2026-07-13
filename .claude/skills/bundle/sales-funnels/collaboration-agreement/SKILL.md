---
name: collaboration-agreement
description: "Drafts collaboration agreements for joint projects with scope, contribution, revenue, and IP ownership terms."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Collaboration Agreement

## When to Use This Skill

Use this skill when you need to:
- Draft a collaboration agreement for a joint project between two or more parties
- Define scope, contributions, revenue sharing, and IP ownership in writing
- Create a lightweight but thorough contract for co-created products or campaigns
- Formalize the terms of a project-based partnership before work begins

**DO NOT** use this skill for employment contracts, full legal partnership agreements, or terms of service. This is for project-based collaboration agreements between independent parties. Always recommend legal review for high-value agreements.

---

## Core Principle

THE BEST TIME TO WRITE A COLLABORATION AGREEMENT IS WHEN BOTH PARTIES ARE EXCITED ABOUT THE PROJECT — NOT AFTER A DISAGREEMENT ABOUT WHO OWNS WHAT.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Project description** | "What are you creating together?" | No default — must be provided |
| **Collaborators** | "Who is involved? (names and roles)" | No default — must be provided |
| **Contributions** | "What does each party contribute? (time, money, expertise, audience)" | No default — must be provided |
| **Revenue model** | "How will money be made and split?" | 50/50 split |
| **Timeline** | "What is the project timeline?" | No default — must be provided |
| **IP expectations** | "Who owns the finished product?" | Joint ownership |

**GATE: Confirm all inputs before drafting.**

---

## Phase 2: Structure

### Agreement Sections

```
1. Parties — who is entering the agreement
2. Project scope — what is being created
3. Contributions — what each party provides
4. Timeline and milestones — key dates and deliverables
5. Revenue and expenses — how money flows
6. Intellectual property — who owns what
7. Decision-making — how disagreements are resolved
8. Confidentiality — what stays private
9. Termination — how to exit the agreement
10. Signatures — making it official
```

### IP Ownership Options

Present these options to the user:

```
## Option A: Joint Ownership
Both parties co-own all created assets. Either party can use them independently.

## Option B: Divided Ownership
Each party owns the assets they contributed. Co-created assets are jointly owned.

## Option C: Single Ownership with License
One party owns all assets. The other receives a perpetual license to use them.

## Option D: Project-Specific Ownership
Assets are owned by the project entity. If the collaboration ends, assets are divided per the agreement.
```

**GATE: Present the structure and IP option for approval.**

---

## Phase 3: Write

### Agreement Template

Write in clear, plain language (not legalese).

```
# Collaboration Agreement

**Date:** [Date]
**Between:** [Party A name, business, address] and [Party B name, business, address]
**Project:** [Project name and one-sentence description]

## 1. Project Scope
[Detailed description of what will be created, including what is NOT included]

## 2. Contributions
**[Party A] will provide:**
- [Specific contribution with estimated value or hours]

**[Party B] will provide:**
- [Specific contribution with estimated value or hours]

## 3. Timeline
| Milestone | Owner | Due Date |
|-----------|-------|----------|
| [Milestone 1] | [Party] | [Date] |
| [Milestone 2] | [Party] | [Date] |
| [Project completion] | [Both] | [Date] |

## 4. Revenue and Expenses
**Revenue split:** [X%] to [Party A], [Y%] to [Party B]
**Expense handling:** [How expenses are shared or reimbursed]
**Payment schedule:** [When and how payments are distributed]
**Accounting:** [Who tracks revenue and provides reports]

## 5. Intellectual Property
[Selected IP ownership model with specific terms]

## 6. Decision-Making
- Day-to-day decisions: [Process]
- Major decisions (scope changes, budget increases): [Requires mutual agreement]
- Deadlocks: [Resolution process — mediation, third-party tiebreaker, etc.]

## 7. Confidentiality
Both parties agree not to share proprietary information, customer data, or financial details related to this project without written consent.

## 8. Termination
- Either party may terminate with [X days] written notice
- Upon termination: [How in-progress work and revenue are handled]
- Surviving clauses: confidentiality and IP terms survive termination

## 9. General Terms
- This agreement represents the entire understanding between parties
- Amendments require written agreement from both parties
- [Governing jurisdiction if relevant]

## Signatures

_________________________     _________________________
[Party A Name]                [Party B Name]
Date: ___________             Date: ___________
```

---

## Phase 4: Polish

### 1. Scenario Testing

Walk through these "what if" scenarios to test the agreement:

```
- What if one party stops contributing midway?
- What if the project earns $0?
- What if it earns 10x projections?
- What if one party wants to use the asset for a different project?
- What if one party wants out early?
- What if a third party wants to join?
```

### 2. Agreement Checklist

```
- [ ] Project scope is specific enough that both parties could describe it identically
- [ ] Every contribution is listed with estimated value or time
- [ ] Revenue split is defined with payment method and schedule
- [ ] IP ownership is explicitly stated
- [ ] Termination process is fair and clear
- [ ] Confidentiality clause is included
- [ ] Both parties have reviewed and understand every section
- [ ] Legal review recommended for projects exceeding $5,000 in value
```

### 3. Legal Disclaimer

Always include:
"This agreement template is for reference purposes. For projects involving significant revenue, complex IP, or multiple parties, consult a licensed attorney in your jurisdiction."

---

## Example 1: Co-Created Online Course

```
Scope: Create and sell a 6-module online course on email marketing
Party A: Creates all course content and teaches live sessions
Party B: Handles marketing, sales page, and email campaigns
Revenue: 50/50 split on all course sales after $2,000 in shared expenses
IP: Joint ownership — both can reference the course in their portfolios
Timeline: 8 weeks to launch
```

## Example 2: Co-Authored E-Book

```
Scope: Write and publish a 30,000-word business guide
Party A: Writes chapters 1-5 and handles editing
Party B: Writes chapters 6-10 and handles design and publishing
Revenue: 50/50 on all sales, Party B handles distribution
IP: Joint ownership with equal rights to derivative works
Timeline: 12 weeks to publication
```

---

## Anti-Patterns

- **Handshake deals** — verbal agreements create disputes. Always put it in writing, even between friends.
- **Vague scope** — "we will create something together" is not a scope. Define exactly what will be built.
- **Ignoring the unhappy path** — agreements that only describe success scenarios fail when problems arise.
- **Equal split by default** — 50/50 is easy but not always fair. Match the split to actual contributions.
- **No termination clause** — every agreement needs an exit. Partners who cannot leave become resentful partners.
- **Skipping legal review for large projects** — this template works for small collaborations. For anything over $10K, get a lawyer.

---

## Recovery

- **Parties disagree on contributions:** Have each party independently list what they will contribute, then compare. Negotiate from data, not feelings.
- **IP ownership is contentious:** Default to divided ownership (each owns what they created, co-created assets are shared). It is the least risky option.
- **User wants a simple one-page agreement:** Condense to scope, contributions, revenue split, IP ownership, and termination. Five sections minimum.
- **Project is already underway without an agreement:** Draft retroactively. Better late than never. Include a "retroactive effective date" clause.
