---
name: stop-and-show
description: STOP-AND-SHOW protocol — paid / production / irreversible actions require founder y/yes before execution
tags: [safety, protocol, money]
applies_to: [ux-architect, ui-designer, brand-guardian, frontend-developer, senior-developer]
last_verified: 2026-05-25
---

# STOP-AND-SHOW

Before any of these actions, agent MUST stop, print exact details, wait for founder "y" / "yes":

**Money:** FASHN API, Gemini paid generation, GPT-Image, FLUX, paid OpenAI/Anthropic/Google calls
**Production:** deploy-theme.sh, SFTP to skyyrose.co, WooCommerce REST write, WordPress media upload, cache flush
**File ops with real data:** sourcing files for paid API, uploading to WC/WP, deleting/overwriting outside `/tmp/` or `renders/output/`
**Compute-heavy:** rembg, cwebp/avifenc batch runs, large image transforms — even if free, founder approves the queue

**Confirm format:**
```
STOP — Confirm before proceeding:
Action : <name>
Target : <exact path>
Cost   : <$X.XX or compute units>
Proceed? [y/N]
```

**Why:** founder bills get burned by autonomous mistakes. Every confirmation costs zero dollars; wrong autonomy costs real money.

**How to apply:** agents propose actions only. The orchestrator (this skill) surfaces them to founder. No agent executes a STOP-AND-SHOW action without explicit go-ahead.

**Project source:** `/Users/theceo/DevSkyy/CLAUDE.md` section "STOP AND SHOW"
