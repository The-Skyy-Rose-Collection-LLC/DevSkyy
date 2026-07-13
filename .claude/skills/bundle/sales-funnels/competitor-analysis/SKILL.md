---
name: competitor-analysis
description: "Conducts a structured competitor analysis with comparison matrices, positioning maps, gap identification, and strategic recommendations. Use when a user wants to understand their competitive landscape, needs to differentiate their offering, or is preparing a go-to-market strategy."
allowed-tools: Read Write Glob mcp__claude_ai_Notion__notion-create-database mcp__claude_ai_Notion__notion-create-pages mcp__claude_ai_Notion__notion-search mcp__claude_ai_Notion__notion-fetch
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Competitor Analysis

## When to Use This Skill

Use this skill when the user needs to:
- Map the competitive landscape for their product, service, or business
- Compare their offering against 3-7 competitors on features, pricing, positioning, and strengths
- Identify market gaps they can exploit and threats they need to defend against
- Prepare a go-to-market strategy that requires competitive positioning
- Make strategic decisions about pricing, messaging, or feature priorities based on what competitors do and miss
- Build a Notion database to track competitors over time

**DO NOT** use this skill for:
- General market research without specific competitors to analyze (use a market research skill)
- Brand identity or messaging work that does not require competitive context
- SEO keyword competitor analysis (use an SEO audit skill)
- One-off price comparisons with no strategic goal

---

## Core Principle

COMPETITIVE ANALYSIS IS ONLY VALUABLE WHEN IT DRIVES A DECISION — NEVER DELIVER A MATRIX WITHOUT STRATEGIC RECOMMENDATIONS THAT TELL THE USER WHAT TO DO NEXT.

---

## Competitive Positioning Categories

Every competitor (and the user's own business) falls into one of these positioning archetypes:

| Category | Definition | Typical Signals |
|----------|-----------|-----------------|
| **Price Leader** | Wins on affordability, targets cost-conscious buyers | Lowest tier pricing, free plans, "affordable" messaging |
| **Quality Leader** | Wins on premium experience, depth, or polish | Higher pricing, fewer features but better execution, strong brand |
| **Niche Specialist** | Wins by owning a narrow segment deeply | Messaging targets one specific audience, limited feature set tuned to that audience |
| **Full-Service** | Wins on breadth, all-in-one positioning | Large feature sets, multiple products, "everything you need" messaging |
| **Disruptor** | Wins by changing the rules — new model, new channel, new pricing | Unconventional pricing (usage-based, free-forever), challenger brand tone |

---

## Threat Assessment Levels

| Level | Definition | Action Required |
|-------|-----------|-----------------|
| **HIGH** | Competitor directly targets the same customer, same price tier, with a strong or growing product | Requires active differentiation strategy — must communicate why you are different |
| **MEDIUM** | Competitor overlaps on audience or features but differs on positioning, pricing, or market segment | Monitor quarterly — differentiate on the overlap points |
| **LOW** | Competitor exists in the same industry but targets a different customer, price tier, or use case | Awareness only — no immediate action needed |

---

## Step 1: Understand

Gather these inputs before analyzing anything:

1. **User's business/product** — what they sell, what problem it solves, who it serves
2. **Industry/category** — the market they compete in (e.g., email marketing SaaS, local personal training, freelance design services)
3. **Known competitors** — names of 3-7 competitors the user is aware of
4. **Key differentiators** — what the user believes makes them different (even if unvalidated)
5. **Target customer** — who their ideal buyer is (demographics, role, pain points)
6. **Pricing tier** — where they sit on the price spectrum (budget, mid-market, premium)

**If the user does not know their competitors**, guide them with these identification methods:

| Method | How It Works | Best For |
|--------|-------------|----------|
| **Direct search** | Search for the product category + "alternatives" or "vs" | SaaS, digital products |
| **Customer question** | Ask: "Where would your customer go if you did not exist?" | Service businesses, coaches |
| **Adjacent category** | Look at businesses solving the same pain differently | Disruptive or new-category products |
| **Local scan** | Search Google Maps or Yelp for nearby businesses in the same category | Local businesses, studios, agencies |

Suggest 3-5 competitors based on the user's business description if they cannot name any. Present the suggestions and let the user confirm, remove, or add.

**GATE: Do not proceed to Step 2 until you have: the user's business description, at least 3 confirmed competitors, and the user's target customer. If the user provides their business and competitors but not a target customer, infer a reasonable default and confirm it.**

---

## Step 2: Analyze

Build four analysis components. Complete all four before presenting anything to the user.

### 2A: Comparison Matrix

Build a feature-by-feature comparison across all competitors and the user's business.

**Default columns (adapt based on industry):**

For product/SaaS businesses:
| Dimension | What to Capture |
|-----------|----------------|
| Core offering | Primary product or service in one sentence |
| Target audience | Who they sell to |
| Pricing | Plans, tiers, starting price |
| Key features | Top 3-5 features or capabilities |
| Strengths | What they do well (2-3 bullets) |
| Weaknesses | Where they fall short (2-3 bullets) |
| Positioning | Which archetype: Price Leader, Quality Leader, Niche Specialist, Full-Service, Disruptor |
| Unique advantage | The one thing they do that nobody else does |

For service/local businesses:
| Dimension | What to Capture |
|-----------|----------------|
| Core service | Primary offering in one sentence |
| Target client | Who they serve |
| Pricing model | Hourly, package, retainer, per-session |
| Price range | Approximate range or starting price |
| Specialization | Niche or specialty area |
| Strengths | What they do well (2-3 bullets) |
| Weaknesses | Where they fall short (2-3 bullets) |
| Positioning | Which archetype |
| Unique advantage | The one thing they do that nobody else does |

### 2B: SWOT Summary Per Competitor

For each competitor, produce a condensed SWOT (2 bullets per quadrant maximum — this is a summary, not a deep dive):

```
## [Competitor Name] — SWOT

| Strengths | Weaknesses |
|-----------|------------|
| - Strong free tier drives adoption | - No advanced automation |
| - Brand recognition in creator market | - Slow customer support |

| Opportunities | Threats |
|---------------|---------|
| - Could expand into SMS/push | - Losing creators to newer platforms |
| - Growing podcast monetization trend | - Pricing pressure from free alternatives |
```

### 2C: Gap Analysis

Identify 3-5 gaps — things competitors collectively miss that the user could own.

For each gap:
- **What is missing** — the unmet need or underserved feature/approach
- **Which competitors miss it** — name them
- **Why it matters** — connect it to the user's target customer pain
- **Difficulty to exploit** — LOW (messaging change), MEDIUM (feature build or new offer), HIGH (fundamental pivot)

### 2D: Threat Assessment

Rate each competitor as HIGH, MEDIUM, or LOW threat using the threat assessment table above. For each:
- **Rating** — HIGH / MEDIUM / LOW
- **Rationale** — one sentence explaining the rating
- **Recommended response** — what the user should do about this competitor specifically

---

## Step 3: Present

Deliver the analysis in a structured format. Present everything before saving anything.

### Presentation Order

**1. Comparison Matrix** — full table with all competitors and the user's business side by side

**2. Positioning Summary** — one paragraph placing each competitor into a positioning category and explaining where the user fits (or should fit)

**3. Threat Assessment Table:**

```
| Competitor | Positioning | Threat Level | Key Concern |
|-----------|-------------|-------------|-------------|
| Mailchimp | Full-Service | HIGH | Dominates SMB mindshare, aggressive free tier |
| ConvertKit | Niche Specialist | MEDIUM | Owns the "creator" positioning but limited automation |
| Beehiiv | Disruptor | HIGH | Fast growth, newsletter-first model resonates with your audience |
| Substack | Niche Specialist | LOW | Writer-focused, minimal marketing tools — different buyer |
```

**4. Top 3 Opportunities** (gaps to exploit):

```
## Opportunities

1. **Advanced automation for solo creators** — Mailchimp has automation but it is built
   for marketing teams. ConvertKit and Beehiiv have basic sequences only. A creator-friendly
   automation builder is an open lane.
   Difficulty: MEDIUM (feature build)

2. **Integrated paid newsletter monetization** — Only Substack and Beehiiv offer native
   paid subscriptions. Neither integrates well with external payment processors.
   Difficulty: MEDIUM (feature build + payment integration)

3. **Template marketplace** — No competitor offers a community-driven template library
   for email designs. Creators want polished templates without hiring a designer.
   Difficulty: LOW (curate existing designs, build a submission flow)
```

**5. Top 3 Threats** (competitive risks):

```
## Threats

1. **Beehiiv's growth trajectory** — gaining creators rapidly with a generous free plan
   and newsletter-first approach. If they add automation, they become a direct competitor.

2. **Mailchimp's brand gravity** — most non-technical users default to Mailchimp because
   of name recognition. Competing on awareness is expensive.

3. **Price compression** — Beehiiv and Substack offering free tiers pushes the whole
   market toward lower prices. Premium positioning requires clear ROI justification.
```

**6. Strategic Recommendations** (3-5 actionable items):

```
## Strategic Recommendations

1. **Own the "automation for creators" positioning** — none of your competitors combine
   creator-friendly UX with powerful automation. Make this your headline differentiator
   on your homepage, pricing page, and in all comparison content.

2. **Build a "vs" content strategy** — create landing pages for "[Your Product] vs Mailchimp,"
   "[Your Product] vs ConvertKit," etc. These capture high-intent search traffic from
   people actively evaluating alternatives.

3. **Launch a free tier with a usage cap, not a feature cap** — Beehiiv and Mailchimp gate
   features behind paid plans. Offering all features free up to 1,000 subscribers
   removes the "will I outgrow the free plan?" anxiety.

4. **Partner with creator communities** — sponsor or co-create with YouTube creator
   communities, podcasting groups, and newsletter collectives. This is where your target
   customer discovers tools — not through Google ads.

5. **Publish a quarterly competitor landscape report** — position yourself as the authority
   on the email marketing space for creators. This builds SEO, trust, and brand
   while keeping your competitive intelligence fresh.
```

**GATE: Present the full analysis and ask the user to review before saving. Offer to adjust any ratings, add/remove competitors, or modify recommendations.**

---

## Step 4: Act

Save the analysis based on the user's preference.

### Option A: Save to Notion Database

1. **Search for existing context** — call `notion-search` to check if the user has a strategy, competitors, or market research page already. If found, confirm where to place the new database.

2. **Create the database** — call `notion-create-database` with these properties:

   | Property | Type | Purpose |
   |----------|------|---------|
   | **Competitor** | Title | Company or product name |
   | **Category** | Select | Price Leader, Quality Leader, Niche Specialist, Full-Service, Disruptor |
   | **Threat Level** | Select | HIGH, MEDIUM, LOW |
   | **Target Audience** | Rich text | Who they sell to |
   | **Pricing** | Rich text | Plans, tiers, price range |
   | **Key Strengths** | Rich text | Top 2-3 strengths |
   | **Key Weaknesses** | Rich text | Top 2-3 weaknesses |
   | **Unique Advantage** | Rich text | Their one differentiator |
   | **Our Response** | Rich text | What we should do about this competitor |
   | **Last Reviewed** | Date | Date of this analysis |
   | **Notes** | Rich text | Additional context, links, observations |

   Database title: `Competitor Analysis — [Industry/Category]`

3. **Populate entries** — call `notion-create-pages` to add each competitor as a row with all fields filled from the analysis.

4. **Add the user's own business as a row** — mark it with a different category or note so it is distinguishable. This lets the user see themselves in context.

5. **Confirm:**

```
Notion database created: "Competitor Analysis — Email Marketing SaaS"

  5 entries: Mailchimp, ConvertKit, Beehiiv, Substack, [Your Product]
  Properties: Category, Threat Level, Audience, Pricing, Strengths, Weaknesses, Unique Advantage, Our Response, Last Reviewed
  All entries dated to today

  Notion link: [database URL]

  Suggested cadence: Review and update this database quarterly.
  Set a reminder for 90 days from now to refresh competitor data.
```

### Option B: Save as Markdown File

If the user prefers a local file or does not have Notion connected:

1. Write the full analysis to a markdown file at the user's preferred path
2. Default filename: `competitor-analysis-[category].md`
3. Include all sections: matrix, SWOTs, gaps, threats, recommendations

```
competitor-analysis/
└── competitor-analysis-email-marketing.md
```

### Suggest Review Cadence

Regardless of save format, close with:

```
Competitive landscapes shift. I recommend reviewing this analysis quarterly:
- Update pricing and feature changes
- Re-assess threat levels based on competitor moves
- Check if the gaps you identified have been filled by anyone
- Refresh recommendations based on your own progress

Set a reminder for [date 90 days from now] to run this analysis again.
```

---

## Example 1: SaaS Email Marketing Tool

**User says:** "I am building an email marketing platform for solo creators — podcasters, YouTubers, newsletter writers. My main competitors are Mailchimp, ConvertKit, Beehiiv, and Substack. We are priced at $29/month for up to 5,000 subscribers. Our differentiator is AI-powered automation sequences."

**Step 1 — Understand:**
- Business: Email marketing SaaS for solo creators
- Industry: Email marketing / creator tools
- Competitors: Mailchimp, ConvertKit, Beehiiv, Substack
- Differentiator: AI-powered automation sequences
- Target customer: Solo creators (podcasters, YouTubers, newsletter writers) with growing audiences
- Pricing tier: Mid-market ($29/month for 5K subscribers)

**Step 2 — Analyze:**

Comparison Matrix:

| Dimension | User's Product | Mailchimp | ConvertKit | Beehiiv | Substack |
|-----------|---------------|-----------|------------|---------|----------|
| Core offering | AI-powered email for creators | All-in-one email marketing | Email marketing for creators | Newsletter growth platform | Writing and subscription platform |
| Target audience | Solo creators | SMBs and marketers | Online creators | Newsletter operators | Writers and journalists |
| Pricing | $29/mo (5K subs) | Free to $350/mo | Free to $29+/mo | Free to $99/mo | Free (10% rev share on paid) |
| Key features | AI automation, templates, analytics | Automations, CRM, ads, landing pages | Visual automations, creator network, commerce | Newsletter SEO, referral program, ad network | Writing editor, paid subscriptions, network |
| Strengths | AI sequences save time, creator-focused | Brand recognition, feature depth, integrations | Creator community, visual automation builder | Newsletter-first growth tools, SEO discovery | Simplicity, built-in audience, zero upfront cost |
| Weaknesses | New brand, small user base | Overcomplicated for solos, expensive at scale | Limited analytics, basic landing pages | No advanced automation, young platform | No automation, no advanced design, revenue share |
| Positioning | Niche Specialist | Full-Service | Niche Specialist | Disruptor | Niche Specialist |
| Unique advantage | AI writes and optimizes sequences automatically | Largest integration ecosystem | Creator Network cross-promotion | Built-in ad monetization and SEO | Zero-cost entry with built-in reader network |

Threat Assessment:

| Competitor | Positioning | Threat Level | Key Concern |
|-----------|-------------|-------------|-------------|
| Mailchimp | Full-Service | MEDIUM | Brand gravity pulls uninformed buyers, but UI complexity drives creators away |
| ConvertKit | Niche Specialist | HIGH | Same target audience, established trust with creators, could add AI features |
| Beehiiv | Disruptor | HIGH | Fast growth, free tier, newsletter-first model resonates with target audience |
| Substack | Niche Specialist | LOW | Writer-focused with revenue share model, different buyer intent |

Top Opportunities:
1. AI-powered automation as a category differentiator — no competitor offers AI-generated email sequences. Lead every comparison with this.
2. Template marketplace for creators — none of the competitors offer community-driven design templates.
3. Cross-platform analytics (email + social) — creators want to see newsletter growth alongside social metrics in one dashboard.

Strategic Recommendations:
1. Own "AI automation for creators" in all messaging and comparison content
2. Build "[Product] vs Mailchimp" and "[Product] vs ConvertKit" landing pages for high-intent search traffic
3. Launch a generous free tier (all features, capped at 1,000 subscribers) to compete with Beehiiv and Substack on acquisition
4. Partner with creator communities — podcast networks, YouTube groups, newsletter collectives
5. Publish a quarterly "State of Email for Creators" report to build authority and SEO

**Step 4 — Act:** User chose Notion. Database created with 5 entries (4 competitors + user's product). Review reminder set for 90 days.

---

## Example 2: Local Personal Training Studio

**User says:** "I run a personal training studio in Austin. I mainly do small group training and 1:1 sessions for people aged 30-50. My competitors are Orangetheory downtown, a CrossFit box called Iron Tribe, and a boutique studio called ATX Strength. I charge $200/month for group and $100/session for 1:1."

**Step 1 — Understand:**
- Business: Personal training studio (small group + 1:1)
- Industry: Local fitness / personal training
- Competitors: Orangetheory (downtown Austin), Iron Tribe CrossFit, ATX Strength
- Differentiator: Not yet defined (will emerge from analysis)
- Target customer: Adults 30-50 in Austin wanting structured training
- Pricing tier: Mid-market ($200/month group, $100/session 1:1)

**Step 2 — Analyze:**

Comparison Matrix:

| Dimension | User's Studio | Orangetheory | Iron Tribe CrossFit | ATX Strength |
|-----------|-------------|-------------|-------------------|-------------|
| Core service | Small group + 1:1 personal training | Heart-rate-based group fitness classes | CrossFit group classes + fundamentals | Boutique strength training, semi-private |
| Target client | Adults 30-50, structured training | Fitness-curious adults 25-55 | Competitive fitness enthusiasts 25-45 | Strength-focused adults 28-45 |
| Pricing model | Monthly group + per-session 1:1 | Monthly unlimited or per-class | Monthly membership | Monthly membership + add-on PT sessions |
| Price range | $200/mo group, $100/session 1:1 | $169/mo unlimited | $175/mo unlimited | $250/mo semi-private |
| Specialization | Personalized programming | Heart-rate zone training, calorie burn | Functional fitness, Olympic lifts | Strength and hypertrophy |
| Strengths | Personal attention, flexible format | National brand, tech-driven experience, social atmosphere | Strong community, competition culture | Focused niche, serious clientele |
| Weaknesses | Less brand recognition, smaller class capacity | Cookie-cutter programming, high turnover | Injury reputation, intimidating for beginners | Premium price limits market, no group energy |
| Positioning | Niche Specialist | Full-Service | Niche Specialist | Quality Leader |
| Unique advantage | Custom programming for each client within group setting | Heart-rate tech and orange light board experience | Community competitions and events | Dedicated strength coaching methodology |

Threat Assessment:

| Competitor | Positioning | Threat Level | Key Concern |
|-----------|-------------|-------------|-------------|
| Orangetheory | Full-Service | MEDIUM | Brand recognition and convenient booking pull casual fitness seekers, but their one-size-fits-all approach differs from personalized training |
| Iron Tribe CrossFit | Niche Specialist | LOW | Different audience — appeals to competitive fitness enthusiasts, not your target of structured-but-approachable training |
| ATX Strength | Quality Leader | HIGH | Most similar target client, similar format, higher price point — direct competitor for serious trainers in the area |

Top Opportunities:
1. "Personalized programming in a group setting" — no competitor offers individualized programs within group classes. Orangetheory is one-size-fits-all, CrossFit follows the WOD model, ATX Strength is semi-private but not truly customized.
2. Beginner-to-intermediate bridge — Orangetheory and CrossFit attract beginners, but many outgrow them. Position as "your next step" for people who want real training after their Orangetheory phase.
3. Nutrition coaching add-on — none of the three competitors prominently offer integrated nutrition programming. A $99/month nutrition add-on paired with training creates a higher-value bundle.

Strategic Recommendations:
1. Lead with "personalized programming, group energy" in all marketing — this is the gap none of your competitors fill
2. Create a "graduate from Orangetheory" landing page and social content series targeting their members who want more
3. Launch a nutrition coaching add-on to increase per-client revenue and create a differentiator
4. Collect and display transformation stories with specific metrics — ATX Strength competes on perceived quality, so you need proof
5. Run a quarterly open house or free community workout to increase local visibility and combat ATX Strength's premium positioning with accessibility

**Step 4 — Act:** User chose markdown file. Full analysis saved to `competitor-analysis-austin-fitness.md`. Review reminder suggested for 90 days.

---

## Recovery and Troubleshooting

### Fewer Than 3 Competitors Known

1. Ask the user: "Where would your ideal customer go if your business did not exist?"
2. Search for the user's product category + "alternatives" or "competitors" to suggest options
3. Check adjacent categories — businesses solving the same pain with a different approach count as competitors
4. If the user can only identify 1-2, proceed with those but note: "This analysis covers your known competitors. As you discover more, add them to the Notion database and re-run the threat assessment."

### No Pricing Data Available

1. Check competitor websites for public pricing pages
2. If pricing is not public (common for services and enterprise SaaS): mark pricing as "Contact for quote" and note the likely tier based on positioning and target market
3. Use comparative language instead of exact numbers: "Premium tier — positioned above your price point" or "Budget tier — significantly below yours"
4. **Do not fabricate pricing.** If you cannot determine it, say so and focus the analysis on non-price dimensions.

### Competitor Is Much Larger (Enterprise vs. Solo)

1. Acknowledge the scale difference explicitly: "Mailchimp serves millions of users. You do not need to compete with them on breadth."
2. Reframe the comparison around the overlap segment only — the specific customer type where you both compete
3. Adjust threat level to reflect actual overlap, not total market size. A $500M company that targets enterprises is LOW threat to a solopreneur targeting freelancers, even though they are in the same industry.
4. Focus recommendations on the segments and positioning angles where size is a disadvantage for the large competitor (speed, personalization, community, niche depth).

### User's Product Does Not Exist Yet (Pre-Launch)

1. Proceed with the analysis normally — competitive analysis is even more valuable pre-launch
2. In the comparison matrix, fill the user's column with planned features, intended pricing, and target positioning
3. Label the user's column clearly: "[Product Name] (Planned)" so nobody confuses plans with reality
4. Add a "Launch Positioning" recommendation: based on the gap analysis, recommend which positioning archetype and differentiation angle to lead with at launch
5. Emphasize gaps and opportunities over threats — pre-launch, the user has the advantage of building specifically to fill the gaps they identify.

### Notion Save Fails

1. Call `notion-search` to verify workspace access — if no results return, the user may not have connected their Notion workspace
2. Inform the user: "I cannot access your Notion workspace. Please make sure the Notion integration is connected."
3. **Fallback:** Save the full analysis as a markdown file at the user's preferred path. Include all tables, SWOTs, gaps, threats, and recommendations in the markdown.
4. If the user wants to try Notion again later, the markdown file serves as the source — all data can be transferred.

### Analysis Feels Too Generic

If the user says the analysis does not feel specific enough:
1. Ask for more context: "Can you share specific features, pricing pages, or customer complaints you have seen from these competitors?"
2. Narrow the comparison dimensions — instead of comparing everything, focus on the 3-4 dimensions the user cares about most
3. Add a "Customer Perception" row to the matrix — what do real reviews and social media say about each competitor
4. Replace generic strengths/weaknesses with specific evidence: instead of "good customer support," use "4.8-star Trustpilot rating with 1,200+ reviews citing fast response times"

---

## Anti-Patterns

- **DO NOT** present a comparison matrix without strategic recommendations — a matrix alone is a spreadsheet, not an analysis
- **DO NOT** rate every competitor as HIGH threat — if everything is critical, nothing is. Use the full range of HIGH, MEDIUM, and LOW
- **DO NOT** recommend "be better at everything" — each recommendation must target a specific gap or threat with a specific action
- **DO NOT** fabricate pricing, feature details, or market data — if information is unavailable, say so and work with what you have
- **DO NOT** skip the user's own business in the comparison — they must see themselves in the matrix to understand their position
- **DO NOT** save to Notion before the user reviews and approves the analysis — always present first, save second
- **DO NOT** compare on more than 10 dimensions in the matrix — cognitive overload makes the analysis unusable. Default to 8 dimensions, go deeper only if the user asks
