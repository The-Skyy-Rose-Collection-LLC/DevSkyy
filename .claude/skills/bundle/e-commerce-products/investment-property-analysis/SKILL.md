---
name: investment-property-analysis
description: "Analyzes rental investment properties with cash flow projections, cap rate calculations, and ROI scenarios."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Investment Property Analysis

## When to Use This Skill

Use this skill when you need to:
- Analyze a rental property's financial viability before purchasing
- Calculate cash flow, cap rate, cash-on-cash return, and ROI projections
- Compare multiple investment properties using consistent metrics
- Present an investment analysis to a buyer client or for your own portfolio

**DO NOT** use this skill for commercial real estate analysis, REIT investing, or property appraisals. This is for residential rental property investment analysis.

---

## Core Principle

INVESTMENT DECISIONS ARE MADE ON NUMBERS, NOT FEELINGS — RUN THE ANALYSIS WITH CONSERVATIVE ASSUMPTIONS AND LET THE MATH TELL YOU WHETHER TO BUY.

---

## Phase 1: Property Data

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Property address** | "What property are you analyzing?" | No default — must be provided |
| **Purchase price** | "What is the asking or offer price?" | No default — must be provided |
| **Expected rent** | "What is the estimated monthly rent?" | No default — research comps |
| **Down payment** | "How much are you putting down?" | 25% (investment property standard) |
| **Interest rate** | "What mortgage rate are you estimating?" | Current market rate |
| **Property taxes** | "Annual property tax amount?" | 1.2% of purchase price |
| **Insurance** | "Annual insurance cost?" | $1,200/year |
| **Current condition** | "Does it need repairs? Estimated rehab cost?" | Move-in ready |

**GATE: Confirm all financial inputs before running calculations.**

---

## Phase 2: Financial Analysis

### Monthly Cash Flow Analysis

```
## Cash Flow Analysis — [Property Address]

### Income
| Source | Monthly | Annual |
|--------|---------|--------|
| Gross rent | $[X] | $[X] |
| Other income (laundry, parking, storage) | $[X] | $[X] |
| **Gross income** | **$[X]** | **$[X]** |

### Vacancy Allowance
| Factor | Rate | Monthly | Annual |
|--------|------|---------|--------|
| Vacancy | 5-8% | -$[X] | -$[X] |
| **Effective gross income** | | **$[X]** | **$[X]** |

### Operating Expenses
| Expense | Monthly | Annual |
|---------|---------|--------|
| Property taxes | $[X] | $[X] |
| Insurance | $[X] | $[X] |
| Property management (8-10%) | $[X] | $[X] |
| Maintenance reserve (5-10%) | $[X] | $[X] |
| Capital expenditure reserve (5%) | $[X] | $[X] |
| HOA fees | $[X] | $[X] |
| Utilities (if landlord-paid) | $[X] | $[X] |
| **Total operating expenses** | **$[X]** | **$[X]** |

### Net Operating Income (NOI)
**NOI = Effective Gross Income - Operating Expenses**
**NOI = $[X]/year**

### Debt Service
| Factor | Amount |
|--------|--------|
| Loan amount | $[X] |
| Interest rate | [X]% |
| Loan term | 30 years |
| **Monthly payment (P&I)** | **$[X]** |
| **Annual debt service** | **$[X]** |

### Monthly Cash Flow
**Cash flow = NOI/12 - Monthly debt service = $[X]/month**
**Annual cash flow = $[X]**
```

---

## Phase 3: Return Metrics

### Key Metrics

```
## Investment Metrics — [Property Address]

### Cap Rate
NOI / Purchase Price = $[X] / $[X] = [X]%
[Target: 5-10% depending on market]

### Cash-on-Cash Return
Annual Cash Flow / Total Cash Invested = $[X] / $[X] = [X]%
[Target: 8-12% for a strong deal]

### Total Cash Invested
| Item | Amount |
|------|--------|
| Down payment | $[X] |
| Closing costs (3-5%) | $[X] |
| Rehab/repairs | $[X] |
| Reserves (3 months expenses) | $[X] |
| **Total cash needed** | **$[X]** |

### Gross Rent Multiplier (GRM)
Purchase Price / Annual Gross Rent = [X]
[Lower is better — under 15 is typically favorable]

### 1% Rule Check
Monthly rent / Purchase price = [X]%
[Target: 1% or higher — $2,000/month rent on $200K purchase]

### Debt Service Coverage Ratio (DSCR)
NOI / Annual Debt Service = [X]
[Target: 1.25+ for comfortable coverage]
```

---

## Phase 4: Scenario Analysis

### Scenario Comparison

```
## Scenarios — [Property Address]

| Scenario | Rent | Vacancy | Expenses | Cash Flow | CoC Return |
|----------|------|---------|----------|-----------|------------|
| Conservative | $[X] | 10% | High | $[X] | [X]% |
| Base case | $[X] | 7% | Expected | $[X] | [X]% |
| Optimistic | $[X] | 5% | Low | $[X] | [X]% |
```

### 5-Year Projection

| Year | Rent (2% increase) | Expenses (3% increase) | Cash Flow | Equity Buildup |
|------|--------------------|-----------------------|-----------|---------------|
| 1 | $[X] | $[X] | $[X] | $[X] |
| 2 | $[X] | $[X] | $[X] | $[X] |
| 3 | $[X] | $[X] | $[X] | $[X] |
| 4 | $[X] | $[X] | $[X] | $[X] |
| 5 | $[X] | $[X] | $[X] | $[X] |

### Investment Decision Summary

```
## Recommendation

**Property:** [Address]
**Purchase price:** $[X]
**Total investment:** $[X]
**Monthly cash flow (base case):** $[X]
**Cash-on-cash return:** [X]%
**Cap rate:** [X]%

**Verdict:** [Buy / Pass / Negotiate to $X]

**Key risks:**
- [Risk 1]
- [Risk 2]

**Key strengths:**
- [Strength 1]
- [Strength 2]
```

---

## Anti-Patterns

- **Ignoring vacancy** — assuming 100% occupancy inflates returns. Always factor 5-10% vacancy.
- **Forgetting property management** — even if you self-manage, include the cost. Your time has value, and you may hire out later.
- **No maintenance reserves** — properties require ongoing repairs. Budget 5-10% of gross rent minimum.
- **Using optimistic rent estimates** — base analysis on current market comps, not "what it could rent for after upgrades."
- **Ignoring capital expenditures** — roofs, HVAC, and water heaters are not "if" expenses, they are "when" expenses.
- **Falling in love with the property** — investment decisions are math. If the numbers do not work, walk away.

---

## Recovery

- **Numbers are borderline:** Negotiate a lower purchase price. Even $10-20K off can meaningfully change returns.
- **Negative cash flow at current price:** Calculate the break-even purchase price and use it as your maximum offer.
- **No comparable rental data:** Check Zillow rent estimates, Rentometer, or call local property managers for market rent opinions.
- **Unexpected repair costs discovered:** Adjust total cash invested and recalculate all return metrics before proceeding.
- **Market rent declining:** Factor declining rents into your scenarios. If the deal only works with rising rents, it is too risky.
