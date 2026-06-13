# SkyyRose Elite

One installable Claude Code plugin that bundles the SkyyRose **marketing & commerce team** — nine skills and seven specialist agent personas, each grounded in verified vendor docs and wired to the SkyyRose Elite Studio runtime and dev-team pipeline.

> Tagline canon: **"Luxury Grows from Concrete."**

## What's inside

**Skills** (`skills/`)
| Skill | Purpose | Grounded in |
|---|---|---|
| `skyyrose-brand-dna` | Brand canon, collections, voice, The Five, guardrails | Internal canon |
| `skyyrose-content-engine` | Social/content branch index + Elite Studio social venture | Internal |
| `skyyrose-product-copy` | PDP / collection / FAQ copy on WooCommerce | WooCommerce REST + schema.org |
| `skyyrose-seo-commerce` | WooCommerce SEO, schema markup, technical SEO | schema.org Product/Offer, WC REST `meta_data` |
| `skyyrose-email-flows` | Klaviyo welcome / cart / post-purchase / drop flows | Klaviyo Flows API |
| `skyyrose-paid-media` | Meta / Google / TikTok campaigns, PMax, retargeting | Meta Ads + Google Ads API |
| `skyyrose-influencer-growth` | Creator program: discovery → outreach → brief → tracking | FTC disclosure, platform programs |
| `skyyrose-photography-brief` | Product + brand shoot briefs, shot lists, art direction | WooCommerce image specs, platform crops |
| `skyyrose-launch-commander` | Drop orchestration T-30 → T+7, propose-roster-and-wait | Composes the above |

**Agents** (`agents/`) — one persona per specialist, embedding its skill(s): `skyyrose-content-engine`, `skyyrose-email-strategist`, `skyyrose-paid-media-buyer`, `skyyrose-seo-commerce`, `skyyrose-influencer-lead`, `skyyrose-photography-director`, `skyyrose-launch-commander`.

**Command** (`commands/`) — `/skyyrose-elite <intent>` routes to the right specialist, or runs a full drop campaign behind a propose-roster-and-wait gate.

## Install (local marketplace)

```bash
# from anywhere
/plugin marketplace add /Users/theceo/DevSkyy/skyyrose-elite
/plugin install skyyrose-elite@skyyrose-elite
```

Then the nine skills load under the plugin namespace and the seven agents register as `subagent_type`s.

## Wiring

See [`WIRING.md`](./WIRING.md) for how each agent maps to the Python runtime SuperAgents (`SkyyRoseContentAgent`, `MarketingAgent`, `SkyyRoseImageryAgent`, `agents/core/orchestrator.py`), the Elite Studio imagery pipelines, and the dev-team workflow marketing lane.

## Guardrails

Paid-media spend, Klaviyo sends, WooCommerce writes, and media uploads are all **STOP-AND-SHOW** — the agents propose and wait for explicit founder approval before any money or production action.
