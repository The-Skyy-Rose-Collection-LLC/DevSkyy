---
name: skyyrose-content-engine
description: "Index hub for the SkyyRose social media branch — routes to 27 specialized social skills (content formats, strategy, community, influencer/PR, visual briefs) and the Elite Studio social venture. Use to find the right SkyyRose social skill, or for the at-a-glance brand-voice quick reference."
allowed-tools: Read Write Edit Glob
---

# SkyyRose Content Engine — Social Branch Hub

> The front door to the SkyyRose social media branch of Elite Studio. This is an
> **index** — the depth lives in the specialized `skyyrose-social-*` skills below.
> Start here to find the right skill, confirm brand voice, or reach the venture.

**Non-negotiable canon for the whole branch:** [`brand-guardrails.md`](./brand-guardrails.md)
— read it before producing anything. Every sub-skill references it.

---

## Brand voice — at a glance

- **Tagline (verbatim):** `Luxury Grows from Concrete.`
- **Brand:** SkyyRose — luxury Oakland streetwear. Founder: Corey Foster. Site: skyyrose.co.
- **Voice:** earned, unhurried, Oakland-direct. No hype-merchant tone, no fake urgency, no
  "complete the look" cross-sell. The garment is the protagonist. Reference products by NAME, not SKU.
- **Visual references (the Five, ALWAYS):** Kith · Oaklandish · Culture Kings · Fear of God · Palm Angels.
  NEVER European luxury-house framing.

### Collections (each its own register — never cross-attribute)

| Collection | Register | Accent |
|------------|----------|--------|
| **Black Rose** | Gothic luxury, armor. "You already stood up." "Concrete answering back." | Silver `#C0C0C0` |
| **Love Hurts** | Street passion, "the bloodline that raised me." Crimson heat. | Crimson `#DC143C` |
| **Signature** | West Coast luxury, "the standard." "Stay golden." | Gold `#D4AF37` |
| **Kids Capsule** | Little royalty, heritage passed down. | Rose Gold `#B76E79` |

Global accent Rose Gold `#B76E79` · Background Dark `#0A0A0A`. Full canon in `brand-guardrails.md`.

### Content pillars (depth in `skyyrose-social-social-media-strategy`)

Brand Story (15%) · Product Showcase (30%) · Culture & Community (25%) · Lifestyle (20%) · Exclusivity (10%).

### Posting times (PST)

Instagram 11am–1pm / 7–9pm · TikTok 9am, 12pm, 6pm, 9pm · X throughout day, Oakland energy.

---

## The Engine — Elite Studio social venture

The branch is powered by the deep-wired **social venture** in Elite Studio. Its publisher node
runs the live `SocialMediaAgent` (free, template-based brand-voice posts); graphics
(`CreativeAgent`) and strategy (`MarketingAgent`) are wired but cost-gated.

```bash
python -m skyyrose.elite_studio.ventures.social info     # manifest
python -m skyyrose.elite_studio.ventures.social agents   # bound agents + wiring
python -m skyyrose.elite_studio.ventures.social smoke --sku br-001   # real posts, free
```
```python
from agents.social_media_agent import SocialMediaAgent
agent = SocialMediaAgent()
post = agent.generate_post("br-001", "instagram", "product_launch")
print(post.caption, post.hashtags)   # brand-voice seed every social skill builds on
```

Agent surface (all real): `generate_post(sku, platform, content_type)` ·
`generate_campaign(...)` · `get_analytics()` · `get_collection_context(collection)` ·
`get_platform_config(platform)`. Platforms: instagram, tiktok, twitter, facebook.
Content types: product_launch, collection_drop, behind_scenes, lifestyle, engagement.

---

## Skill directory — route to the right specialist

### Content formats (what you post)
| Skill | Use when |
|-------|----------|
| `skyyrose-social-instagram-carousel` | Swipeable IG carousel (launch, styling, collection story) |
| `skyyrose-social-tiktok-script` | Frame-by-frame TikTok/Reels script |
| `skyyrose-social-short-form-video-plan` | Multi-week short-form video calendar + batch sessions |
| `skyyrose-social-twitter-thread` | X thread (brand story, drop, founder POV) |
| `skyyrose-social-thread-hook-writer` | Hook variants + scoring for any thread/post |
| `skyyrose-social-meme-content-brief` | On-brand meme concepts (engagement register) |

### Strategy & planning (what to do)
| Skill | Use when |
|-------|----------|
| `skyyrose-social-social-media-strategy` | Pillars, channel mix, 90-day roadmap, repurposing flow |
| `skyyrose-social-social-media-calendar` | 30-day calendar, weekly rhythm, monthly arcs |
| `skyyrose-social-social-media-audit` | Score current accounts incl. brand-canon compliance |
| `skyyrose-social-hashtag-strategy` | Branded + collection + niche hashtag sets per platform |
| `skyyrose-social-youtube-strategy` | YouTube channel positioning + Shorts pipeline |
| `skyyrose-social-pinterest-strategy` | Boards, Rich Pins, keyword formula |
| `skyyrose-social-reddit-strategy` | Corey-as-person community participation (90/10 rule) |

### Community & policy (how the audience is run)
| Skill | Use when |
|-------|----------|
| `skyyrose-social-community-launch` | Stand up the Discord/community space |
| `skyyrose-social-community-moderation` | Moderation tiers, AutoMod, escalation |
| `skyyrose-social-platform-community-guidelines` | Public-facing community guidelines doc |
| `skyyrose-social-social-media-policy` | Internal social governance + approval workflow |
| `skyyrose-social-social-listening-plan` | Keyword/hashtag monitoring + intel reporting |
| `skyyrose-social-crisis-comms` | Severity-tiered crisis response runbook |

### Influencer & PR (who amplifies)
| Skill | Use when |
|-------|----------|
| `skyyrose-social-influencer-campaign-brief` | Brief doc for a paid creator campaign |
| `skyyrose-social-influencer-outreach` | DM/email outreach sequence + tracker |
| `skyyrose-social-pr-pitch` | Sub-200-word press pitch + follow-up |
| `skyyrose-social-media-kit` | Press/partner media kit document |
| `skyyrose-social-co-marketing-plan` | Brand-to-brand co-marketing partnership |

### Visual briefs (how it looks)
| Skill | Use when |
|-------|----------|
| `skyyrose-social-brand-photography-brief` | Lifestyle/campaign/founder shoot brief |
| `skyyrose-social-product-photography-brief` | Garment-centric e-commerce shoot brief |
| `skyyrose-social-social-media-graphics` | Per-platform graphic specs + canvas sizes |

---

## How the pieces fit

```
brand-guardrails.md  ← canon every skill obeys
        │
skyyrose-content-engine (this hub)  → routes to ↓
        │
27 skyyrose-social-* skills  ← author the deliverables
        │
Elite Studio social venture  ← SocialMediaAgent produces the brand-voice seed
        │
skyyrose.co / platforms  ← published
```

**Rule:** every platform gets a native adaptation — never cross-post identical content. Each
skill above carries its own Implementation/Artifact spec, real worked example, anti-patterns,
and recovery steps. When in doubt about voice, return to `brand-guardrails.md`.
