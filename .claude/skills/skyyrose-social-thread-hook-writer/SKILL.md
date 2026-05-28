---
name: skyyrose-social-thread-hook-writer
description: "Generates 10 scroll-stopping X/Twitter thread hooks in SkyyRose brand voice — tagged by collection register, scored, and ready to A/B test for maximum click-through."
allowed-tools: Read Write Edit Glob
---

# SkyyRose Social — Thread Hook Writer

## When to Use This Skill

- Generating multiple hook variants before writing a full thread (pair with `skyyrose-social-twitter-thread`)
- A/B testing first-tweet performance across different psychological triggers
- Finding the sharpest opening for a collection drop, founder story, or culture take
- Writing scroll-stopping hooks for threads across X/Twitter (and adapting to Threads app)
- Unlocking a new content angle when existing thread topics feel stale

**DO NOT** use this for writing full threads (use `skyyrose-social-twitter-thread`), for full-post captions (use `skyyrose-social-instagram-carousel`), or for video hooks (use `skyyrose-social-tiktok-script`). This skill produces ONLY the opening hook — the first 1-3 lines that earn the read.

---

## Brand Canon (non-negotiable)

- **Every hook must be assignable to exactly one collection register OR to the general brand.** A hook tagged "Black Rose" must carry armor/defiance energy. A hook tagged "Love Hurts" must carry the bloodline/raw-romance register. A hook tagged "Signature" must carry "stay golden / the standard" energy. A hook tagged "Brand" is collection-agnostic. Never blend registers within one hook.
- **Oakland-direct voice.** No hedging, no enthusiasm-performance ("So excited to share!"), no corporate distance. Earned. Specific. Unhurried.
- **Name, not SKU.** If a hook references a product, it's "BLACK Rose Crewneck" not "br-001".
- **No hype-merchant tone.** No "🔥🔥 BIG DROP 🔥🔥", no countdown language in the hook itself.
- **Under 280 characters.** The hook IS the first tweet. No exceptions.
- **The Five only** for any aesthetic or cultural reference: Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels. Never European luxury house names.

Full canon: `../skyyrose-content-engine/brand-guardrails.md`

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|-------------|---------|
| **Topic** | "What is the thread about? Be specific." | No default — must be provided |
| **Collection / register** | "Which collection, or general brand?" | Brand (collection-agnostic) |
| **Thread type** | "Brand story, collection launch, hot take, founder journey, culture commentary, or how-we-made-it?" | Brand story |
| **Key insight or result** | "What is the most surprising, specific, or emotionally resonant element?" | No default — must be provided |
| **Platform** | "X/Twitter or Threads?" | X/Twitter |
| **Number of hooks** | "How many variants? (10 recommended for meaningful A/B testing)" | 10 |

**GATE: Confirm topic, collection register, and key insight before generating hooks. If the register is ambiguous, ask which collection — a Black Rose hook and a Love Hurts hook on the same topic are completely different outputs.**

---

## Phase 2: No Outline Needed

Move directly to generation. Hook writing is generative, not structural.

---

## Phase 3: Write

### Hook Formula Set (SkyyRose-adapted)

Generate one hook per formula. For each: include the text, the formula label, the collection register tag, and a platform-fit note.

```
## Hook Variations

### Formula 1: The Identity Statement [Register: __]
"[A statement of what SkyyRose / the collection IS — identity, not feature]"
SkyyRose example: "Black Rose isn't a product. It's an answer."
Use when: The thread is about brand story or collection deep-dive.

### Formula 2: The Founder Result [Register: Brand or specific]
"[Corey did X / built X with specific, real constraints. Here's what I learned:]"
SkyyRose example: "I built a luxury streetwear brand out of Oakland with no investors, no VC, no hype machine. Here's what that actually looks like:"
Use when: Thread is founder journey or behind-the-business.

### Formula 3: The Contrarian Take [Register: Brand]
"Luxury doesn't come from [expected source]. [It comes from here] Thread:"
SkyyRose example: "Luxury doesn't come from Europe. It never did. Oakland proved it first."
Use when: Culture commentary or fashion-industry hot take.

### Formula 4: The Specific Detail [Register: collection-specific]
"[Exact construction detail or design decision]. Here's why we didn't cut it:"
SkyyRose example: "The embroidery on the BLACK Rose Crewneck took four rounds to get right. A thread on why that mattered:"
Use when: Product deep-dive or "how we made it" thread.

### Formula 5: The Community Call [Register: Brand / Oakland]
"[Oakland / The Town / Bay Area] doesn't get enough credit for [specific thing]. Let me fix that:"
SkyyRose example: "Oakland doesn't get enough credit for what it's building in fashion. Thread:"
Use when: Culture/community thread or Oakland-pride angle.

### Formula 6: The Before / After [Register: Founder / Brand]
"[Time] ago I was [specific state]. Today [specific different state]. Here's the turning point:"
SkyyRose example: "Two years ago SkyyRose was an idea in a notebook. Today it's a collection. Here's the gap between those two sentences:"
Use when: Founder journey or brand origin story.

### Formula 7: The Curiosity Gap [Register: any]
"[Something surprising is true about this collection / brand / product]. Most people don't know it:"
SkyyRose example: "There's a reason every Black Rose piece hits differently at night. It's not the color. Thread:"
Use when: Thread teases a non-obvious insight or design philosophy.

### Formula 8: The Direct Address [Register: collection-specific or Brand]
"If you're [specific person who identifies with the collection], this thread is for you:"
SkyyRose example: "If you grew up in The Town and never saw your aesthetic at retail, this thread is for you:"
Use when: Community-identity thread or drop announcement for a specific audience.

### Formula 9: The Question Hook [Register: any]
"Why do [the people who built / wear / made X] always [specific behavior]?"
SkyyRose example: "Why do the most respected brands in streetwear never explain themselves?"
Use when: Culture/philosophy thread or "the standard" content.

### Formula 10: The Garment Truth [Register: collection-specific]
"[Product name]. [One sentence that is the emotional truth of this garment]. A thread:"
SkyyRose example: "The Love Hurts Bomber. Built for everything the streets charged you to learn. A thread:"
Use when: Single-product drop narrative thread.
```

### Collection Register Tag (mandatory for every hook)

Every hook output must be tagged with one of:

| Tag | When to use |
|-----|-------------|
| `[Black Rose]` | Armor, defiance, "you already stood up," twilight elegance |
| `[Love Hurts]` | Bloodline, raw romance, crimson heat, street passion |
| `[Signature]` | "Stay golden," the standard, West Coast elevation |
| `[Kids Capsule]` | Little royalty, heritage passed down |
| `[Brand]` | General SkyyRose — not collection-specific |
| `[Oakland/Town]` | Bay Area community and culture hooks |

A hook tagged `[Black Rose]` CANNOT contain "bloodline that raised me" (Love Hurts). A hook tagged `[Signature]` CANNOT contain "armor" language (Black Rose). If a draft hook would fit more than one tag, it is not specific enough — rewrite.

### Scoring Each Hook

Rate every hook on:

| Criteria | What It Measures | Score (1-5) |
|----------|-----------------|-------------|
| **Stop power** | Would this pause a scrolling thumb mid-feed? | |
| **Curiosity gap** | Does it create an itch that only the thread can scratch? | |
| **Specificity** | Does it include a concrete detail, number, product name, or place? | |
| **Brand register** | Is it unmistakably SkyyRose / Oakland — not any other brand? | |
| **Platform fit** | Under 280 chars, sounds like a tweet, not a LinkedIn post? | |

Maximum score: 25. Flag any hook under 15 for rewrite before presenting.

---

## Phase 4: Polish

### Top 3 Recommendations

Present the 3 highest-scoring hooks with reasoning:

```
## Top 3 Hooks

1. "[Hook text]" — Register: [tag] — Score: [X/25]
   Why it works: [1-2 sentences on the psychological trigger and why it fits SkyyRose]
   A/B test against: Hook #N (different trigger, same topic)

2. "[Hook text]" — Register: [tag] — Score: [X/25]
   Why it works: [1-2 sentences]

3. "[Hook text]" — Register: [tag] — Score: [X/25]
   Why it works: [1-2 sentences]
```

### A/B Test Suggestion

Always recommend testing 2 hooks that use different psychological triggers on the same topic:
- One **identity/community** hook (stops the right audience)
- One **specific-detail** hook (stops the curious audience)

These two triggers reach different reader motivations and produce meaningfully different data.

### Hook Checklist

```
- [ ] Under 280 characters
- [ ] Collection register clearly assigned — no cross-attribution
- [ ] Contains a specific detail, name, number, or place (not generic)
- [ ] Does not give away the full thread answer (earns the read)
- [ ] Sounds natural spoken aloud — not like a brand announcement
- [ ] No hype-merchant language (🔥, "BIG DROP", countdown)
- [ ] No European luxury name-drops
- [ ] Matches the actual thread content (no misleading hooks)
- [ ] Score ≥ 15/25 before presenting
```

---

## Implementation

```python
from agents.social_media_agent import SocialMediaAgent

agent = SocialMediaAgent()

# Pull the brand-voice seed for a BLACK Rose Crewneck thread
post = agent.generate_post("br-001", "twitter", "product_launch")

print(post.caption)        # X-native brand voice — the tone your hooks must match
print(post.hashtags)       # collection-aware hashtag set
# The hook variants (text + formula + register tag + score) and the top-three
# recommendation are what THIS skill generates from that voice seed.
```

```bash
# Smoke-test the social venture pipeline for BLACK Rose:
python -m skyyrose.elite_studio.ventures.social smoke --sku br-001
```

**Hook scoring sheet config (tracking spreadsheet row):**

```json
{
  "sku": "br-001",
  "product_name": "BLACK Rose Crewneck",
  "collection": "black-rose",
  "thread_type": "product_launch",
  "hook_variants_generated": 10,
  "selected_hook": "Formula 4 — Specific Detail",
  "hook_text": "The embroidery on the BLACK Rose Crewneck took four rounds to get right. A thread on why that mattered:",
  "register_tag": "Black Rose",
  "stop_power": 4,
  "curiosity_gap": 5,
  "specificity": 5,
  "brand_register": 5,
  "platform_fit": 5,
  "total_score": 24,
  "ab_test_against": "Formula 1 — Identity Statement",
  "posted_utc": null,
  "impressions": null,
  "profile_clicks": null,
  "thread_engagements": null
}
```

---

## Example: 10 Hooks for "BLACK Rose Crewneck Drop Thread"

**Topic:** BLACK Rose Crewneck product launch thread
**Collection:** Black Rose | **Thread type:** Product launch + "how we made it"
**Key insight:** Embroidery took four iterations; the piece is built for permanence, not hype

```
1. [Formula 1 — Identity Statement] [Black Rose] Score: 22/25
"Black Rose isn't a product. It's an answer."
→ Earns curiosity without naming the piece; the thread delivers the context.

2. [Formula 4 — Specific Detail] [Black Rose] Score: 24/25
"The embroidery on the BLACK Rose Crewneck took four rounds to get right. A thread on why that mattered:"
→ Concrete, specific, earns trust before the thread even begins.

3. [Formula 7 — Curiosity Gap] [Black Rose] Score: 21/25
"There's a reason we took four months on one embroidered chest script. Most brands would have shipped at round two:"
→ Stakes the permanence-over-speed philosophy without announcing it.

4. [Formula 3 — Contrarian Take] [Brand] Score: 20/25
"Luxury streetwear gets built in Oakland now. Not Paris. Not New York. The Town. Thread:"
→ Broadens context; sets Black Rose inside a larger cultural claim.

5. [Formula 8 — Direct Address] [Black Rose] Score: 22/25
"If you've ever worn something that felt like armor against the wrong room — this thread is for you:"
→ Self-selects the exact Black Rose audience. High stop power on that reader.

6. [Formula 10 — Garment Truth] [Black Rose] Score: 23/25
"The BLACK Rose Crewneck. Built for people who already stood up. A thread on what that means in practice:"
→ Collection register is precise; "already stood up" is Black Rose canon.

7. [Formula 6 — Before/After] [Brand] Score: 18/25
"A year ago the BLACK Rose embroidery was a sketch. Today it's a chest script on 250 garments. Here's what happened in between:"
→ Lower score; "what happened in between" is a softer hook. Usable but not top 3.

8. [Formula 2 — Founder Result] [Brand] Score: 19/25
"I spent four months on an embroidered chest script for a crewneck. Not because it was expected. Because it had to be right:"
→ Strong Corey voice. Earns respect before the thread delivers product detail.

9. [Formula 9 — Question Hook] [Black Rose] Score: 17/25
"Why does a luxury streetwear brand spend four rounds iterating on one piece of embroidery?"
→ Competent but passive. The statement hooks above outperform it.

10. [Formula 5 — Community Call] [Oakland/Town] Score: 16/25
"Oakland doesn't make things for trends. It makes them to last. The BLACK Rose Crewneck is that, in stitch form:"
→ Strong cultural anchor; lower stop power because it front-loads context over curiosity.

---
TOP 3: Hooks #2 (score 24), #6 (score 23), #5 (score 22)
A/B TEST: Hook #2 (specific detail) vs Hook #5 (direct address) — different triggers, same topic.
```

---

## Anti-Patterns

- **Generic hooks that could apply to any brand** — "I want to tell you about our new collection:" could be from Gap or Walmart. SkyyRose hooks are Oakland-specific, collection-specific, or founder-specific.
- **Cross-register contamination** — writing "bloodline" energy into a Black Rose hook, or "armor" language into a Love Hurts hook. Tag forces this discipline: if you can't assign a clean register, rewrite.
- **Hooks that give away the entire thread** — "Here are the 5 facts about the BLACK Rose Crewneck:" leaves nothing to earn. Create the gap.
- **Hype-merchant opening** — "🔥🔥 BIG DROP: The BLACK Rose Crewneck is HERE" is not a SkyyRose hook. It is a notification, not a thread.
- **Too vague to score on specificity** — "I built something I'm proud of:" is 0/5 on specificity. Name the product, the detail, the place, or the decision.
- **Hooks over 280 characters** — they will be truncated. Check character count before scoring.
- **Same formula every time** — if you're always writing "I did X. Here's what happened:" your audience becomes pattern-blind within 3 threads. Vary.
- **European luxury frame** — "Like a French atelier but Oakland" is the wrong DNA. The Five refs only.
- **Audience mismatch** — a Direct Address hook written for the wrong audience (e.g., a Love Hurts hook framed for corporate professionals) fails to self-select the right reader.

---

## Recovery

- **No topic feels interesting enough for a hook:** Find the single most surprising or specific detail in the brief — embroidery iterations, Oakland location detail, a specific material weight — and lead with that. Every product has one specific truth that earns curiosity.
- **All 10 hooks feel the same:** Check formula diversity. If 6 of them are Formula 2 (Founder Result), you're pattern-locked. Force at least one Formula 3 (Contrarian), one Formula 5 (Community Call), and one Formula 10 (Garment Truth).
- **Hooks feel "brand-try-hard":** Read the content-engine's collection voice sections. If a hook sounds like a brand announcement instead of Corey speaking, strip the brand voice and write it as if Corey is talking to a friend in Oakland who already knows the brand.
- **Register is ambiguous — thread crosses two collections:** That thread should be split. One thread per collection register. Ambiguous register = ambiguous hook = poor click-through.
- **A/B test produced no difference in engagement:** Run a third hook variant using a completely different formula (e.g., if you tested Identity + Detail, now test Community Call). The two-variant test is not conclusive if both variants use similar psychological triggers.
