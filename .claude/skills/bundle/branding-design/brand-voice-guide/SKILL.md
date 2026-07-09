---
name: brand-voice-guide
description: "Creates a comprehensive brand voice guide with tone attributes, vocabulary lists, do's and don'ts, and platform-specific adaptations. Use when a user needs to document their brand voice for consistency, is onboarding writers or team members, or wants to establish clear messaging guidelines."
allowed-tools: Read Write Glob Grep
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Brand Voice Guide

## When to Use This Skill

Use this skill when you need to:
- Document a brand's voice and tone for the first time
- Onboard new writers, freelancers, or team members who need to write in-brand
- Establish consistent messaging guidelines across platforms and content types
- Translate vague brand personality ("we want to sound professional but approachable") into actionable writing rules
- Create a quick-reference guide that anyone on the team can scan in under 2 minutes

**DO NOT** use this skill for:
- Visual brand identity (logos, colors, typography) — that is a brand style guide, not a voice guide
- Full marketing strategy or content planning (use content-calendar for that)
- Writing actual content (use blog-post, email-sequence, or social-media-graphics instead)
- Rewriting existing content to match a voice — build the guide first, then apply it

---

## Quick Reference: Voice Attribute Spectrum

Every brand voice sits somewhere on these spectrums. The guide will pin 3-4 positions.

| Spectrum | Left End | Right End | Example Left | Example Right |
|----------|----------|-----------|--------------|---------------|
| Formality | Formal | Casual | "We invite you to explore our offerings." | "Check out what we've got." |
| Tone | Serious | Playful | "Financial security requires discipline." | "Let's make your money work harder (so you don't have to)." |
| Complexity | Technical | Simple | "Our API leverages asynchronous callbacks." | "It connects to your tools automatically." |
| Energy | Reserved | Bold | "We believe in steady, thoughtful progress." | "Stop waiting. Build the damn thing." |
| Warmth | Distant | Intimate | "Customers may contact support." | "We're right here when you need us." |
| Authority | Peer | Expert | "We're figuring this out together." | "After 10,000 hours of testing, here's what works." |

---

## Quick Reference: Tone Modifier Table

Voice stays constant. Tone shifts by context. This table shows how the same brand voice adjusts.

| Context | Energy Level | Formality Shift | Emoji/Punctuation | Example Shift |
|---------|-------------|-----------------|-------------------|---------------|
| Social media | Higher | More casual | Emojis allowed | "We just dropped something big." |
| Email newsletter | Medium | Slightly casual | Minimal emoji | "Here's what we've been working on this month." |
| Support reply | Calm | More formal | No emoji | "I understand the frustration. Here's how we'll fix it." |
| Sales page | High | Medium | Sparingly | "This is the system that changed everything for us." |
| About page | Medium | Medium-formal | None | "We started in a garage with one idea and zero budget." |
| Legal/terms | Low | Formal | None | "By using this service, you agree to the following terms." |
| Blog post | Medium-high | Matches brand default | Optional | "Three mistakes that are costing you clients right now." |

---

## Quick Reference: Brand Archetypes

Use these as starting points during the Discover phase. Most brands are a blend of two.

| Archetype | Core Trait | Voice Sounds Like | Example Brands | Best For |
|-----------|-----------|-------------------|----------------|----------|
| The Expert | Authority + Precision | Confident, data-driven, clear | McKinsey, Wirecutter, Ahrefs | Consultants, B2B, SaaS |
| The Friend | Warmth + Approachability | Conversational, supportive, relatable | Mailchimp, Basecamp, Glossier | Lifestyle, community brands |
| The Rebel | Boldness + Disruption | Punchy, direct, unapologetic | Liquid Death, Cards Against Humanity | Coaches, challenger brands |
| The Coach | Motivation + Structure | Encouraging, action-oriented, clear | Tony Robbins, Ramit Sethi, Peloton | Course creators, fitness, coaching |
| The Curator | Taste + Selectivity | Refined, intentional, understated | Kinfolk, Aesop, Monocle | Premium, design-forward brands |

---

## Core Workflow

EVERY VOICE GUIDE STARTS WITH DISCOVERY -- NEVER SKIP STRAIGHT TO WRITING RULES WITHOUT UNDERSTANDING THE BRAND FIRST.

### Step 1: Discover

Gather the raw material for the voice profile. Ask the user these questions in order:

1. **Business basics** -- "What does your business do, and who is your ideal customer?"
2. **Adjective test** -- "Name 3-4 adjectives that describe how your brand should sound. For example: bold, witty, warm, authoritative, playful, calm."
3. **Admired brands** -- "Name 2-3 brands whose voice you admire (they don't have to be in your industry)."
4. **Anti-brands** -- "Name 1-2 brands you do NOT want to sound like, and why."
5. **Content samples** -- "Share a link or paste a paragraph of your existing content that feels most 'you.' If you don't have any, that's fine."
6. **Platform mix** -- "Where does your brand show up? (social media, email, blog, podcast, sales pages, support)"

**If the user provides existing content files, read them with the Read tool and analyze the current voice patterns before proceeding.**

**IF THE USER CANNOT DESCRIBE THEIR VOICE:**
Present the Voice Attribute Spectrum table above and ask them to place a mark on each spectrum:
```
Let's find your voice. For each pair, tell me where you land on a scale of 1-5:

Formal (1) ←——→ Casual (5):
Serious (1) ←——→ Playful (5):
Technical (1) ←——→ Simple (5):
Reserved (1) ←——→ Bold (5):
Distant (1) ←——→ Intimate (5):
Peer (1) ←——→ Expert (5):
```

Then match their scores to the closest archetype blend and confirm: "Based on your answers, you sound like a mix of The Coach and The Friend -- encouraging, personal, and action-oriented. Does that feel right?"

### Step 2: Define

Build the complete voice profile from the discovery inputs.

1. **Select 3-4 voice attributes** -- each one gets a name, a one-sentence description, and a "this means / this does not mean" clarification

   Format each attribute like this:
   ```
   ATTRIBUTE: Direct
   Description: We say what we mean without filler or hedging.
   This means: Short sentences. Active voice. Leading with the point.
   This does NOT mean: Rude, abrupt, or dismissive. We're direct, not cold.
   ```

2. **Build the vocabulary lists:**

   | Power Words (USE these) | Banned Words (NEVER use these) |
   |------------------------|-------------------------------|
   | build, launch, unlock | synergy, leverage, disrupt |
   | real, proven, tested | revolutionary, game-changing |
   | you, your, yours | one, the user, the customer |
   | simple, clear, fast | utilize, facilitate, optimize |
   | start, grow, scale | pivot, ecosystem, best-in-class |

   Customize both lists to the specific brand. The power words should reflect the adjectives from Step 1. The banned words should reflect the anti-brands.

3. **Define grammar and style rules:**

   | Rule | Setting | Example |
   |------|---------|---------|
   | Sentence length | Short to medium (8-18 words avg) | "Start your free trial today." not "We would like to invite you to begin..." |
   | Contractions | Yes -- always use them | "We're" not "We are", "don't" not "do not" |
   | Exclamation marks | Max 1 per section | "You're going to love this." not "This is AMAZING!!!" |
   | Emoji | Social only, max 2 per post | Use on Instagram/X, skip on LinkedIn/email |
   | Oxford comma | Yes | "strategy, content, and design" |
   | First person | "We" for company, "I" for solopreneur | Match the business structure |
   | Addressing the reader | Always "you" | "You'll save 10 hours a week." not "Users save 10 hours..." |
   | Jargon | Avoid unless audience expects it | "Grow your email list" not "Optimize your lead acquisition funnel" |

4. **Create the "We Are / We Are Not" table:**

   | We Are | We Are Not |
   |--------|------------|
   | Confident | Arrogant |
   | Friendly | Sycophantic |
   | Direct | Blunt or rude |
   | Knowledgeable | Condescending |
   | Encouraging | Pushy |
   | Opinionated | Preachy |

5. **Build platform adaptation rules** using the Tone Modifier Table as a base, customized to the brand's actual platform mix

### Step 3: Demonstrate

Write the exact same core message in the brand voice for 5 different contexts. This is the most important section of the guide -- it shows the voice in action.

**Use this core message as the base:** Take whatever the brand's primary offer or value proposition is and adapt it.

Write these 5 demonstrations:

1. **Social media post** (Instagram or X/Twitter) -- short, punchy, platform-native
2. **Email subject line + preview text** -- designed to get opens
3. **Customer support reply** -- responding to a complaint or question
4. **Sales headline + subheadline** -- for a landing page or sales page
5. **About page excerpt** -- 3-4 sentences describing the brand

Each demonstration should be 2-6 sentences maximum. Show the voice attributes in action with a brief annotation explaining which attribute is driving each choice.

### Step 4: Deliver

Assemble the final voice guide document and write it to disk.

1. Compile all sections into a single markdown file with this structure:

   ```
   # [Brand Name] Voice Guide

   ## Voice at a Glance
   [3-4 attributes with one-line descriptions]

   ## Voice Attributes (Detailed)
   [Full attribute breakdowns from Step 2]

   ## We Are / We Are Not
   [Table from Step 2]

   ## Vocabulary
   [Power words and banned words tables]

   ## Grammar & Style Rules
   [Rules table from Step 2]

   ## Platform Adaptations
   [Tone modifier table customized to their platforms]

   ## Voice in Action
   [All 5 demonstrations from Step 3]

   ## Quick Checklist for Writers
   [10-item yes/no checklist for self-review]
   ```

2. Write the file using the Write tool to the user's preferred location. **Default path: `./brand-voice-guide.md` in the current working directory.** Ask the user if they want a different location.

3. Present a summary of what was created and how to use it.

---

## Example 1: The Rebel Coach

**User input:**
- Business: Online fitness coaching for busy professionals
- Adjectives: bold, no-BS, motivating, real
- Admired brands: Liquid Death, Gary Vaynerchuk, Nike
- Anti-brands: Goop ("too woo-woo"), Equinox ("too elitist")
- Platforms: Instagram, email, sales pages, blog

**Voice Profile:**

```
ATTRIBUTE: Bold
Description: We lead with strong opinions and back them up.
This means: Taking a clear stance. Saying "this works, that doesn't."
This does NOT mean: Being mean, shaming people, or tearing others down.

ATTRIBUTE: No-BS
Description: We skip the fluff and get to what matters.
This means: Short paragraphs. No filler words. No corporate speak.
This does NOT mean: Being cold or robotic. We still have personality.

ATTRIBUTE: Motivating
Description: We push people forward with energy and urgency.
This means: Action verbs. Present tense. "Do this now" energy.
This does NOT mean: Toxic positivity or empty hype. We motivate with truth.

ATTRIBUTE: Real
Description: We talk like actual humans, not a marketing department.
This means: Contractions, slang when it fits, admitting when things are hard.
This does NOT mean: Unprofessional or sloppy. Casual is not careless.
```

**We Are / We Are Not:**

| We Are | We Are Not |
|--------|------------|
| Blunt | Cruel |
| Fired up | Manic |
| Relatable | Sloppy |
| Opinionated | Closed-minded |
| Encouraging | Coddling |

**Vocabulary:**

| Power Words | Banned Words |
|------------|-------------|
| crush, build, grind | synergy, optimize, leverage |
| real talk, let's go, no excuses | revolutionary, game-changing |
| you, your body, your goals | the client, one's fitness journey |
| strong, lean, unstoppable | toned, sculpted, transformed |
| start today, show up, commit | embark, commence, utilize |

**Grammar & Style:**

| Rule | Setting |
|------|---------|
| Sentence length | Short. 5-12 words average. |
| Contractions | Always. "You're" not "You are." |
| Exclamation marks | 1 per post max. Let the words carry the energy. |
| Emoji | Instagram: yes, 1-2. Email: no. Sales pages: no. |
| Swearing | Light. "Damn" and "hell" are fine. Nothing heavier. |
| Addressing reader | Always "you." Never "our clients" or "members." |

**5 Demonstrations:**

**1. Instagram Post:**
> You don't need more motivation. You need a plan and 30 minutes. That's it. Stop scrolling. Go move your body. Your future self is begging you.
>
> *[Bold: strong opener. No-BS: no filler. Motivating: action CTA. Real: "stop scrolling" — meets them where they are.]*

**2. Email Subject + Preview:**
> Subject: You skipped the gym again. Let's fix that.
> Preview: 3 workouts that take less time than your commute.
>
> *[Bold: calls out the behavior directly. No-BS: immediate value. Real: acknowledges the struggle without judgment.]*

**3. Support Reply:**
> Hey Marcus — I hear you. The meal plan feels overwhelming at first. That's normal. Here's what I want you to do: pick just 3 meals from the plan this week. Cook those. Ignore the rest. You'll build momentum without the stress. Reply back and let me know how it goes.
>
> *[Real: acknowledges the struggle. Motivating: gives a small actionable step. No-BS: specific instruction, not vague reassurance.]*

**4. Sales Headline + Subheadline:**
> Headline: Stop Guessing. Start Training.
> Subheadline: A 12-week program built for professionals who have 45 minutes a day and zero patience for fitness industry nonsense.
>
> *[Bold: commands attention. No-BS: "zero patience for nonsense" signals the brand. Real: "45 minutes a day" is specific and honest.]*

**5. About Page Excerpt:**
> We started this because we were tired of fitness advice that only works if you have 2 hours a day and a personal chef. Most of us don't. We build training programs for people with real jobs, real schedules, and real bodies. No six-pack promises. No miracle supplements. Just smart programming that fits your life.
>
> *[Real: personal origin story. No-BS: calls out the industry. Bold: "no six-pack promises" is a contrarian stance. Motivating: "fits your life" offers hope.]*

---

## Example 2: The Expert Financial Advisor

**User input:**
- Business: Financial planning for small business owners
- Adjectives: trustworthy, clear, warm, knowledgeable
- Admired brands: Vanguard, Ramit Sethi, The New York Times
- Anti-brands: Crypto Twitter ("too hype"), TurboTax ("too generic and robotic")
- Platforms: LinkedIn, email newsletter, blog, sales pages

**Voice Profile:**

```
ATTRIBUTE: Trustworthy
Description: We earn trust through accuracy, transparency, and consistency.
This means: Citing sources. Being upfront about risks. Never overselling.
This does NOT mean: Being wishy-washy or hedging every statement with disclaimers.

ATTRIBUTE: Clear
Description: We explain complex financial concepts in plain language.
This means: Short definitions. Analogies. "In other words" translations.
This does NOT mean: Dumbing things down or being patronizing. Respect the reader's intelligence.

ATTRIBUTE: Warm
Description: We treat money as personal, not just numerical.
This means: Acknowledging the emotions around money. Using "you" language.
This does NOT mean: Being overly casual or buddy-buddy. We're a trusted advisor, not a friend at a bar.

ATTRIBUTE: Knowledgeable
Description: We demonstrate expertise without showing off.
This means: Specific numbers, real examples, informed opinions.
This does NOT mean: Jargon-dropping or academic language. If a client wouldn't say it, we don't write it.
```

**We Are / We Are Not:**

| We Are | We Are Not |
|--------|------------|
| Authoritative | Condescending |
| Reassuring | Sugarcoating |
| Precise | Pedantic |
| Approachable | Overly casual |
| Transparent | Preachy |

**Vocabulary:**

| Power Words | Banned Words |
|------------|-------------|
| protect, grow, plan | disrupt, hack, crush it |
| steady, proven, reliable | guaranteed, risk-free, explosive |
| your business, your goals | the investor, one's portfolio |
| clear, straightforward, honest | utilize, facilitate, synergize |
| build wealth, reduce risk, save | moonshot, 10x, passive income empire |

**Grammar & Style:**

| Rule | Setting |
|------|---------|
| Sentence length | Medium. 12-20 words average. |
| Contractions | Yes, but not in formal documents (proposals, terms). |
| Exclamation marks | Rarely. Max 1 per email. Zero on sales pages. |
| Emoji | Never. Not on any platform. |
| Numbers | Always use actual figures: "$47,000" not "about fifty thousand." |
| Addressing reader | "You" in content. "Your business" when discussing their finances. |
| Jargon | Define on first use: "An S-Corp (a tax structure that can reduce self-employment tax)..." |

**5 Demonstrations:**

**1. LinkedIn Post:**
> Most small business owners leave $10,000-$30,000 on the table every year in missed tax deductions. Not because they're careless. Because no one showed them where to look. Here are three deductions your accountant might not have mentioned — and how to claim them before year-end.
>
> *[Knowledgeable: specific dollar range. Clear: "where to look" simplifies the problem. Trustworthy: no hype, just facts. Warm: "not because they're careless" removes shame.]*

**2. Email Subject + Preview:**
> Subject: The tax move most business owners miss
> Preview: It takes 15 minutes and could save you thousands this year.
>
> *[Clear: plain language, no jargon. Knowledgeable: implies insider expertise. Trustworthy: "could save" not "will save" — honest framing.]*

**3. Support Reply:**
> Hi Janet — Great question about your SEP-IRA contribution limits. For 2025, you can contribute up to 25% of your net self-employment earnings, with a maximum of $70,000. Based on the income numbers you shared, your max contribution would be around $42,500. I've attached a worksheet so you can see the exact calculation. Let me know if any of the numbers look off or if you want to talk through the strategy.
>
> *[Knowledgeable: specific figures and limits. Clear: walks through the math. Warm: "let me know if any numbers look off" invites continued dialogue. Trustworthy: shows the work, not just the answer.]*

**4. Sales Headline + Subheadline:**
> Headline: Financial Planning That Actually Fits Your Business
> Subheadline: Straightforward strategies for small business owners who want to keep more of what they earn — without a finance degree.
>
> *[Clear: "straightforward" and "without a finance degree." Warm: "fits your business" is personal. Knowledgeable: "strategies" implies depth. Trustworthy: no "get rich" promises.]*

**5. About Page Excerpt:**
> We work exclusively with small business owners because your finances are different from everyone else's. You're not just managing a budget — you're managing payroll, taxes, cash flow, and growth at the same time. We built our practice around that reality. Every recommendation we make is specific to your business, your risk tolerance, and your goals. No cookie-cutter plans. No jargon-filled reports you'll never read.
>
> *[Warm: "your finances are different" validates their experience. Knowledgeable: lists the real complexity they face. Trustworthy: "specific to your business" promises personalization. Clear: "no jargon-filled reports" reinforces the commitment.]*

---

## Pre-Delivery Checklist

Run this checklist before delivering the voice guide. **DO NOT SKIP ANY ITEM.**

| Check | What to Verify | How |
|-------|----------------|-----|
| Voice attributes defined | 3-4 attributes, each with description + "this means / does not mean" | Review the Define section |
| No contradictions | Attributes do not conflict (e.g., "formal" and "casual" simultaneously) | Read all 4 together — do they form one coherent personality? |
| Vocabulary lists populated | At least 10 power words and 10 banned words, customized to the brand | Check the tables are not generic |
| Grammar rules complete | All 8 style rules have a clear setting with an example | Verify every row in the rules table |
| "We Are / We Are Not" table | At least 5 rows, each pair makes sense as a spectrum | Read each row aloud |
| Platform adaptations present | Every platform the user mentioned has tone guidance | Cross-reference with their platform list from Step 1 |
| All 5 demonstrations written | Social post, email subject, support reply, sales headline, about page | Count them |
| Demonstrations show all attributes | Each demo annotates which attributes are at work | Check annotations |
| Writer's checklist included | 10-item self-review checklist at the end of the guide | Verify it exists |
| File written to disk | Guide saved as markdown via Write tool | Confirm Write tool success |

```
Pre-Delivery Checklist:
  [x] 3-4 voice attributes with full breakdowns
  [x] No contradicting attributes
  [x] Vocabulary lists customized (10+ words each)
  [x] Grammar and style rules complete (8 rules)
  [x] "We Are / We Are Not" table (5+ rows)
  [x] Platform adaptations for all stated platforms
  [x] All 5 voice demonstrations written
  [x] Attribute annotations on each demonstration
  [x] Writer's quick checklist included
  [x] File written to disk
```

---

## Recovery and Troubleshooting

### User Cannot Describe Their Voice at All

If the user says "I have no idea what my brand sounds like":

1. Present the Voice Attribute Spectrum scoring exercise (1-5 scale from Step 1)
2. Ask for 2-3 brands they admire — reverse-engineer the voice attributes from those brands
3. If they have any existing content at all, ask to read it and identify the natural voice patterns
4. If none of the above works, start with the archetype table and ask: "Which of these 5 personalities feels closest to your brand?"
5. **Use the closest archetype as the starting draft and iterate from there** — a starting point is better than a blank page

### Existing Content Contradicts Desired Voice

If the user's website says "We leverage cutting-edge synergies" but they say they want to sound casual and real:

1. Acknowledge the gap: "Your current content leans formal and corporate. Your desired voice is much more casual and direct. The guide will target where you want to be, not where you are."
2. Include a "Before / After" section in the guide showing 3 rewrites of their actual existing copy
3. Flag the highest-impact pages to rewrite first (homepage, about page, most-shared social post)

### Multiple Brands or Products Need Different Voices

If the user runs a parent brand with sub-brands or multiple product lines:

1. Ask: "Do these brands share a voice, or does each one have a distinct personality?"
2. If shared: build one guide with minor tone variations per brand (similar to platform adaptations)
3. If distinct: build separate guides for each brand, starting with the primary one
4. **Default to one guide unless the user explicitly requests multiple** — most solopreneurs need one voice, not three

### Three Revision Attempts Fail

If the user rejects the voice profile three times:

1. Stop generating and ask: "Let me try a different approach. Can you write 2-3 sentences the way you want your brand to sound? Just off the top of your head, no pressure to be perfect."
2. Use their raw writing as the source of truth — match the rhythm, word choice, and energy
3. Present the revised profile as: "Based on how YOU naturally write, here's what I see..."
4. **If this still misses, suggest a voice workshop:** "It might help to collect 5-10 pieces of content you love (from any brand) and we can reverse-engineer the patterns."

### User Wants a Voice That Does Not Match Their Audience

If the user wants to sound like Liquid Death but sells financial advisory services:

1. Do not refuse. Instead, flag the tension: "A rebellious, irreverent tone is unusual in financial services. That can be a huge differentiator — or it can erode trust with conservative clients."
2. Ask: "Is your audience the type who would appreciate edgy financial content, or are they more traditional?"
3. If they confirm the edgy direction, build the guide as requested but add a "Boundaries" section that defines where the rebel voice stops (e.g., "Never joke about someone's actual financial losses")
4. If they reconsider, help them find a middle ground — "confident and plain-spoken" achieves much of the rebel energy without the risk

---

## Anti-Patterns

- **DO NOT** create voice attributes that contradict each other -- "formal" and "casual" cannot coexist as primary attributes. Pick a point on the spectrum.
- **DO NOT** write a guide longer than 3 pages -- if nobody reads it, it does not exist. The entire delivered guide should be scannable in under 2 minutes.
- **DO NOT** use subjective descriptions without examples -- "be authentic" means nothing without a demonstration of what authentic sounds like in practice.
- **DO NOT** list more than 4 voice attributes -- the human brain holds 3-4 concepts at once. Five attributes means nobody remembers any of them.
- **DO NOT** present multiple voice options and ask the user to choose -- pick the best one based on their inputs and refine from there. One default, always.
- **DO NOT** skip the demonstration section -- abstract rules without concrete examples are useless. The 5 demonstrations ARE the guide; everything else is scaffolding.
- **DO NOT** copy another brand's voice guide verbatim and change the name -- every brand has a unique combination of attributes, audience, and context.
- **DO NOT** include time-sensitive references -- "sound like brands do in 2025" will age immediately. Write rules that are durable.
- **DO NOT** deliver the guide without writing it to a file -- the user needs a permanent artifact, not a chat message they will lose.