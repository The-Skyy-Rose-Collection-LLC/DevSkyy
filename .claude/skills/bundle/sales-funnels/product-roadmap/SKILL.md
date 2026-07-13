---
name: product-roadmap
description: "Creates product roadmaps in Notion with milestones, feature priorities, release timelines, and status tracking for SaaS products, apps, courses, or any product with iterative development. Use when a user needs to plan product development, wants to communicate a roadmap to stakeholders, or needs to prioritize features for upcoming releases."
allowed-tools: Read Write Glob mcp__claude_ai_Notion__notion-create-database mcp__claude_ai_Notion__notion-create-pages mcp__claude_ai_Notion__notion-search mcp__claude_ai_Notion__notion-fetch
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Product Roadmap

## When to Use This Skill

Use this skill when you need to:
- Build a product roadmap database in Notion to plan features, milestones, and releases
- Prioritize a backlog of feature ideas using ICE scoring or MoSCoW
- Communicate a development timeline to stakeholders, investors, or team members
- Replace a spreadsheet, Trello board, or whiteboard-based product planning process

**DO NOT** use this skill for:
- Project task management with daily to-dos (use project-tracker instead)
- Bug tracking or issue management (different schema and workflow)
- Enterprise portfolio management across dozens of products (too complex for a single database)

---

## Quick Reference

| Feature | Details |
|---------|---------|
| Properties | 12 fields per feature record |
| Prioritization | ICE scoring (default) or MoSCoW framework |
| Status stages | 6 (Backlog > Planned > In Progress > Testing > Shipped > Deferred) |
| Timeframes | 4 horizons (Now, Next, Later, Icebox) |
| Database views | 4 filtered views |
| Seeding | Bulk import from feature list or product brief |

## Database Schema

| Property | Type | Options/Default |
|----------|------|-----------------|
| Feature Name | Title | Required |
| Description | Rich text | Empty |
| Priority | Select | Must Have (red), Should Have (orange), Could Have (yellow), Won't Have (gray) |
| Status | Select | Backlog (gray), Planned (blue), In Progress (purple), Testing (orange), Shipped (green), Deferred (red) |
| Quarter/Phase | Select | Now (green), Next (blue), Later (yellow), Icebox (gray) |
| Effort | Select | XS (gray), Small (green), Medium (yellow), Large (orange), XL (red) |
| Impact | Number | 1-10 scale |
| Confidence | Number | 1-10 scale |
| Ease | Number | 1-10 scale |
| Owner | Rich text | Empty |
| Category | Select | Core (blue), Growth (green), Monetization (purple), Infrastructure (gray), UX/Design (pink), Integrations (orange) |
| Dependencies | Rich text | Empty |

### Status Flow

| Status | Meaning | Action |
|--------|---------|--------|
| Backlog | Idea captured, no timeline | Score with ICE, assign priority |
| Planned | Committed to a quarter | Assign owner, refine description |
| In Progress | Actively being built | Owner provides progress updates |
| Testing | Built, undergoing QA or beta | Testers provide feedback within 5 days |
| Shipped | Live and available to users | Mark release date in Description |
| Deferred | Intentionally postponed | Log reason, revisit next quarter |

### Effort Sizing

XS = less than 1 day | Small = 1-3 days | Medium = 1-2 weeks | Large = 3-4 weeks | XL = 5+ weeks

---

## ICE Scoring Framework

DEFAULT PRIORITIZATION METHOD. Use ICE unless the user explicitly requests MoSCoW-only.

**ICE Score = (Impact x Confidence x Ease) / 10**

| Dimension | Question | Scale |
|-----------|----------|-------|
| Impact | How much does this move the needle on revenue, retention, or satisfaction? | 1 (minimal) to 10 (transformative) |
| Confidence | How certain are we this will deliver the expected impact? | 1 (pure guess) to 10 (validated with data) |
| Ease | How easy is this to implement given current resources? | 1 (massive effort) to 10 (trivial to ship) |

| ICE Range | Action |
|-----------|--------|
| 50-100 | Prioritize immediately; move to Now |
| 25-49 | Plan for Next quarter |
| 10-24 | Keep in Later; refine scope |
| 1-9 | Move to Icebox; revisit when data improves |

**Scoring rules:**
- Score Impact on **business outcomes**, not feature coolness. A billing fix that reduces churn outscores a flashy animation.
- Score Confidence on **evidence.** Customer interviews = 8-10, gut feeling = 2-3, competitor has it = 5-6.
- Score Ease **relative to team size.** Solo developer rates a 2-week feature as 3; a 5-person team rates it 7.
- **NEVER give every feature the same scores.** If all features score 5/5/5, the framework provides zero signal.

---

## Core Workflow

EVERY PRODUCT ROADMAP STARTS BY GATHERING PRODUCT DETAILS AND CREATING THE DATABASE WITH THE FULL 12-PROPERTY SCHEMA BEFORE ADDING ANY FEATURES -- NEVER ADD PAGES TO A DATABASE THAT IS MISSING PROPERTIES.

### Phase 1: Gather Product Details

1. **Product name** -- what is the product called
2. **Product type** -- SaaS, mobile app, web app, online course, physical product, marketplace
3. **Current stage** -- idea, MVP, beta, launched, scaling
4. **Notion parent page** -- where should the roadmap live (page name or URL)
5. **Feature list** -- known features, ideas, or backlog items to import
6. **Team size** -- solo, small team (2-5), or team (6+); affects Ease scoring
7. **Release cadence** -- weekly, biweekly, monthly, quarterly, or milestone-based
8. **Stakeholder audience** -- who will read this (team, investors, customers, board)
9. **Custom categories** -- product areas beyond the 6 defaults

If the user provides only items 1, 4, and 5, proceed with all defaults.

**Brief template:**
```
I'll build your product roadmap in Notion. Quick answers needed:
1. Product name?
2. Product type? (SaaS, app, course, physical, other)
3. Current stage? (idea, MVP, beta, launched, scaling)
4. Which Notion page should I create the roadmap under?
5. Feature list or backlog to import?
6. Team size? (solo, 2-5, 6+)
7. Release cadence? (weekly, biweekly, monthly, quarterly)
8. Who will read this roadmap? (team, investors, customers)
```

### Phase 2: Prioritize Features with ICE Scoring

1. Score every feature with Impact, Confidence, Ease (1-10 each)
2. Calculate ICE Score: (I x C x E) / 10
3. Assign MoSCoW Priority: ICE 50+ = Must Have, 25-49 = Should Have, 10-24 = Could Have, below 10 = Won't Have
4. Assign Quarter/Phase: Must Have -> Now, Should Have -> Now/Next, Could Have -> Next/Later, Won't Have -> Icebox
5. Present scored list for user approval:

```
 #  Feature                    Impact  Conf  Ease  ICE   Priority      Phase
 1  Stripe payment integration    9      8     6   43.2  Must Have     Now
 2  Email onboarding sequence     8      7     7   39.2  Should Have   Now
 3  Team member roles             7      6     5   21.0  Could Have    Next
 4  Dark mode                     3      4     8    9.6  Won't Have    Icebox

Approve this prioritization, or tell me which scores to adjust.
```

**NEVER skip prioritization.** Even if the user says "just add them all," score every feature first.

### Phase 3: Search Notion for Parent Page

1. Call `notion-search` with the page name the user provided
2. Confirm the parent page if multiple matches exist

**IF NOT FOUND:** Ask for exact title, try shorter keywords, verify integration access. **After 3 failures:** "I cannot locate that page. Check Settings > Connections in Notion and verify the integration has access."

### Phase 4: Create the Roadmap Database

1. Call `notion-create-database` with parent page ID, title `[Product Name] Roadmap`, and all 12 properties from the schema above (including color assignments)
2. Verify with `notion-fetch` on the returned database ID
3. Confirm creation with property summary

**IF CREATION FAILS:** Verify parent page ID with `notion-fetch`, check permissions, retry once. **If it fails again:** "Please go to the parent page > three-dot menu > Connections and ensure the integration has 'Can edit' access."

### Phase 5: Seed Features and Deliver

1. Using the approved scored list from Phase 2, call `notion-create-pages` for all features
2. Populate all 12 properties per feature. Must Have/Now features start as "Planned"; all others start as "Backlog"
3. Report results grouped by Quarter/Phase with feature name, priority, effort, ICE score, and owner
4. Provide view setup instructions (Notion MCP cannot create views programmatically):

```
RECOMMENDED VIEWS:

1. TIMELINE VIEW (Table) — Group by: Quarter/Phase, Sort: Priority then ICE descending, Filter: not Deferred
2. PRIORITY BOARD (Board) — Group by: Priority, Sort: Impact descending, Filter: not Shipped/Deferred
3. STATUS KANBAN (Board) — Group by: Status, Sort: Priority, No filter
4. QUICK WINS (Table) — Filter: Impact >= 7 AND Ease >= 7 AND Status = Backlog, Sort: Ease descending
```

5. Deliver the planning guide:

```
QUARTERLY REVIEW (60 min):
1. Move shipped features to "Shipped"
2. Re-score features whose Impact/Confidence changed
3. Pull top Backlog features into "Planned" for next quarter
4. Assign owners to all "Now" features

WEEKLY CHECK-IN (15 min):
1. Update statuses in Status Kanban
2. Check for blocked features (note in Dependencies)
3. Review Quick Wins for fast shipping opportunities

ADDING NEW IDEAS: Set Status=Backlog, Phase=Icebox, score ICE, assign Priority

STAKEHOLDER VIEWS:
- Investors: filter Must Have + Should Have, hide ICE scores
- Customers: filter Now + Next, show Status and Quarter only
- Internal: show all views, full detail
```

**IF THE FEATURE LIST IS VAGUE:** Generate reasonable features based on product type and stage, present with ICE scores for approval BEFORE creating pages. **NEVER create inferred features without confirmation.**

---

## Example 1: SaaS Invoicing Tool Roadmap

**User:** "Building a SaaS invoicing tool called BillFlow. Post-MVP with 50 beta users. Team: me (product), Priya (engineer), Marcus (designer). Monthly releases. Notion page: 'BillFlow Product'. Here are 12 features..."

**Execution:**

1. **Gather:** BillFlow, SaaS, post-MVP, 3-person team, monthly, internal audience
2. **Prioritize:** Score 12 features:

```
 #  Feature                       Impact  Conf  Ease  ICE    Priority      Phase
 1  Payment reminder emails          8      8     7   44.8   Must Have     Now
 2  Stripe payment integration       9      8     6   43.2   Must Have     Now
 3  CSV export for accountants       6      7     7   29.4   Should Have   Now
 4  Recurring invoice automation     9      7     5   31.5   Should Have   Now
 5  Dashboard with revenue metrics   7      6     6   25.2   Should Have   Now
 6  Late fee auto-calculation        6      7     5   21.0   Could Have    Next
 7  Team member roles                7      6     5   21.0   Could Have    Next
 8  Custom invoice templates         5      6     6   18.0   Could Have    Next
 9  QuickBooks sync                  8      5     4   16.0   Could Have    Next
10  Dark mode                        2      9     8   14.4   Could Have    Later
11  Client self-service portal       7      5     4   14.0   Could Have    Later
12  Multi-currency support           6      4     3    7.2   Won't Have    Icebox
```

3. **Search:** `notion-search` "BillFlow Product" -> `pg_billflow123`
4. **Create:** Database "BillFlow Roadmap" with custom categories (Core, Billing, Reporting, Integrations, UX) -> `db_roadmap456`
5. **Seed and deliver:**

```
Features imported: 12 of 12

  NOW: Payment reminder emails (Must, ICE 44.8), Stripe integration (Must, ICE 43.2),
       Recurring invoices (Should, ICE 31.5), CSV export (Should, ICE 29.4),
       Dashboard metrics (Should, ICE 25.2)
  NEXT: Late fees (Could, ICE 21.0), Team roles (Could, ICE 21.0),
        Invoice templates (Could, ICE 18.0), QuickBooks sync (Could, ICE 16.0)
  LATER: Dark mode (Could, ICE 14.4), Client portal (Could, ICE 14.0)
  ICEBOX: Multi-currency (Won't, ICE 7.2)

Next steps:
1. Create the 4 recommended views in Notion
2. Assign owners to the 3 unassigned features
3. Write detailed specs for the 2 Must Have features
4. Schedule quarterly review for end of this quarter
```

---

## Example 2: Online Course Roadmap

**User:** "Solopreneur building a cooking course on Teachable called ChefPath. Idea stage. 8 feature ideas. Notion page: 'ChefPath Business'. Just me."

**Execution:**

1. **Gather:** ChefPath, online course, idea stage, solo, milestone-based
2. **Prioritize:** Score 8 features (solo = lower Ease for complex items):

```
 #  Feature                         Impact  Conf  Ease  ICE    Priority      Phase
 1  Teachable sales page setup         9      8     7   50.4   Must Have     Now
 2  Free sample lesson (lead magnet)   7      7     8   39.2   Should Have   Now
 3  Core curriculum (12 modules)      10      9     4   36.0   Must Have     Now
 4  Email waitlist + launch sequence   8      7     6   33.6   Should Have   Now
 5  Recipe PDF downloads (bonus)       5      8     8   32.0   Should Have   Now
 6  Student community (FB group)       6      6     7   25.2   Could Have    Next
 7  Advanced masterclass (upsell)      8      4     3    9.6   Won't Have    Icebox
 8  Affiliate referral program         6      3     5    9.0   Won't Have    Icebox
```

3. **Search:** `notion-search` "ChefPath Business" -> `pg_chef789`
4. **Create:** Database "ChefPath Roadmap", categories (Content, Marketing, Community, Monetization) -> `db_chef012`
5. **Seed and deliver:**

```
Features imported: 8 of 8

  NOW: Sales page (Must, ICE 50.4), Sample lesson (Should, ICE 39.2),
       Curriculum (Must, ICE 36.0), Email sequence (Should, ICE 33.6),
       Recipe PDFs (Should, ICE 32.0)
  NEXT: Student community (Could, ICE 25.2)
  ICEBOX: Masterclass (Won't, ICE 9.6), Affiliates (Won't, ICE 9.0)

Solopreneur tip: Start with the highest ICE score (sales page setup),
not the biggest effort item (curriculum). The sales page validates demand
before you invest weeks recording video modules.
```

---

## Pre-Delivery Checklist

**DO NOT SKIP ANY ITEM.**

```
Pre-Delivery Checklist:
  [ ] Database created and accessible (notion-fetch with database ID)
  [ ] All 12 properties configured
  [ ] Priority options correct (4 MoSCoW levels)
  [ ] Status options correct (6 stages)
  [ ] Quarter/Phase options correct (4 horizons)
  [ ] Effort options correct (5 sizes)
  [ ] Category options present (default or custom)
  [ ] ICE scores populated for all features
  [ ] All features seeded successfully (count vs. expected)
  [ ] No duplicate features
  [ ] Owners assigned where team info was provided
  [ ] Dependencies documented where applicable
  [ ] View setup instructions delivered
  [ ] Database under correct parent page
  [ ] User approved prioritization before seeding
```

---

## Recovery and Troubleshooting

### Notion Search Returns No Results
1. Ask for the exact page title (case-sensitive)
2. Try a shorter keyword (e.g., "Product" instead of "BillFlow Product Dashboard")
3. Confirm the page is shared with the Notion integration
4. **After 3 failures:** "Check Settings > Connections in Notion and verify the integration has access."

### Database Creation Fails
1. Verify parent page ID with `notion-fetch`
2. Check for permission errors
3. Retry once
4. **If it fails again:** "Go to parent page > three-dot menu > Connections > ensure 'Can edit' access."

### Feature Seeding Partially Fails
1. Report which features succeeded and which failed
2. Retry failed features individually
3. If retries fail, provide details formatted for manual entry

### Notion API Rate Limits
1. Pause 10 seconds between batches, reduce to 5 features per call
2. **DO NOT skip features due to rate limits** -- slow down and retry

### User Disagrees with ICE Scores
1. Ask which features to re-score and discuss their reasoning
2. Adjust scores, recalculate ICE, re-sort priorities
3. Present revised list for approval before proceeding

### Adding Features Later
1. `notion-fetch` to confirm database ID and schema
2. Score new features with ICE, present for approval
3. `notion-create-pages` to add, report updated totals

### Schema Modification After Build
**Notion MCP does not support modifying existing schemas.** Instruct the user:
- Add property: click "+" in header row, choose type, name it
- Modify property: click column header > "Edit property"
- Add new option: click any cell in that column, type the new option name

---

## Anti-Patterns

- **DO NOT** create the database without the full 12-property schema -- adding properties after pages exist causes alignment issues
- **DO NOT** skip ICE scoring -- prioritization is the core value of a roadmap, not the list itself
- **DO NOT** use dates that imply commitments unless the user confirms deadlines -- use relative horizons (Now, Next, Later), not calendar dates
- **DO NOT** add more than 20 features without grouping into categories -- uncategorized lists are backlog dumps, not roadmaps
- **DO NOT** assign all features to "Now" -- if everything is Now, nothing is prioritized
- **DO NOT** give every feature the same ICE scores -- identical scores defeat the framework
- **DO NOT** skip parent page confirmation -- creating under the wrong page is difficult to undo
- **DO NOT** create views programmatically -- Notion MCP does not support this
- **DO NOT** promise automated notifications, sprint planning, or burndown charts -- this is a database, not a full PM tool
- **DO NOT** include time-sensitive milestones like "Q3 2025" -- use relative horizons instead
