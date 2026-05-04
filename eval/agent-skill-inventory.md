---
name: Agent & Skill Inventory Audit (with MCP auth status)
specified_by: [v2: §4 (orchestration map), grill Branch 4 (advisor flag)]
phase: 0
test_command: node scripts/measurement/check-agent-inventory.js  # exits 0 when no FOUND_GAP entries remain
pass_threshold: Every V2 §4 referenced agent/skill/MCP has explicit AVAILABLE | SUBSTITUTE_AVAILABLE | GAP_DOCUMENTED status
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Agent & Skill Inventory Audit

Every agent, skill, and MCP server referenced by `docs/SKYYROSE_V2_MASTER_PLAN.md` §4 audited for actual availability. The advisor flagged in Phase 0 grill that several specialist agents may not exist — this audit makes the gap explicit.

**Audit method:**
- Skills: confirmed via the available-skills list at session entry (the authoritative invocability list — surfaced via `Skill` tool)
- Agents: confirmed via available `subagent_type` list (the authoritative `Agent` tool list)
- MCPs: confirmed via deferred-tools list at session entry (the authoritative invocable-tool list once schemas are loaded via `ToolSearch`)

**Audit constraints:**
- No `mcp__*__authenticate` calls were triggered (those are state-change OAuth flows; reserved for Phase 0.5 prerequisite check)
- No skill/agent invocations that would burn tokens; this is read-only inventory only

---

## SkyyRose-specific skills (V2 §4.1)

| Skill | V2 phase entries | Status | Notes |
|-------|------------------|--------|-------|
| **skyyrose-brand-dna** | EVERY phase | **AVAILABLE** | Surfaced via Skill tool (plugin-namespaced; not in `~/.claude/skills/` directly but present in available-skills list). Voice rules, banned phrases, palette, "say The Town not the Bay Area" |
| **skyyrose-launch-commander** | Phase 5.4 | **AVAILABLE** | Drop launch sprint orchestration. Confirmed in `~/.claude/skills/skyyrose-launch-commander/` |
| **skyyrose-product-copy** | Phase 4 + 5.3 | **AVAILABLE** | Per-collection voice. Confirmed `~/.claude/skills/skyyrose-product-copy/` |
| **skyyrose-content-engine** | Phase 5.4 + 6 | **AVAILABLE** | 5 content pillars. Confirmed `~/.claude/skills/skyyrose-content-engine/` |
| **skyyrose-paid-media** | Phase 6.5 | **AVAILABLE** | Meta/TikTok/Google ad creative. Confirmed `~/.claude/skills/skyyrose-paid-media/` |
| **skyyrose-email-flows** | Phase 5.4 + 6 | **AVAILABLE** | Klaviyo flows (Welcome 5, Drop 7, Cart 3, Post-purchase 4, Seasonal). Confirmed `~/.claude/skills/skyyrose-email-flows/` |
| **skyyrose-seo-commerce** | Phase 4 + 5 + 6 | **AVAILABLE** | Keyword matrix, JSON-LD, URL hierarchy. Confirmed `~/.claude/skills/skyyrose-seo-commerce/` |
| **BONUS — skyyrose-influencer-growth** | Not in V2 §4.1 | AVAILABLE | Skill exists but not referenced in V2 plan; useful for Phase 6 if influencer marketing surfaces |
| **BONUS — skyyrose-photography-brief** | Not in V2 §4.1 | AVAILABLE | Skill exists; useful for Phase 4 luxury reference triangulation alongside `image-taste-frontend` |

**Battle-tested vs aspirational verdict (per grill Branch additional question):**

These 7 SkyyRose skills are battle-tested — they're already invocable AND project-grounded (their content was written for this project, per `MEMORY.md` and prior project history). The 2 bonus skills are also battle-tested but not in the V2 plan; they may surface Phase 4-6 work without re-derivation.

---

## Generic design lens skills (V2 §4.2)

| Skill | V2 use | Status |
|-------|--------|--------|
| **image-taste-frontend** | Phase 4 design-ref A | **AVAILABLE** (plugin-namespaced) |
| **aidesigner** (MCP + skill + CLI) | Phase 4 design-ref B | **FULLY PROVISIONED 2026-05-03** — three integration paths live: (1) `aidesigner-frontend` skill at both project (`.claude/skills/`) and user (`~/.claude/skills/`) scopes, installed via `npx -y @aidesigner/agent-skills init` + `init claude --scope user`; (2) `/aidesigner` slash command; (3) npx CLI fallback `npx -y @aidesigner/agent-skills generate` reading `AIDESIGNER_API_KEY` from `.env` (set 2026-05-03, file mode 0o600). MCP OAuth flow initiated; awaiting one-click browser completion to unlock `mcp__aidesigner__*` tool runtime calls. |
| **ui-ux-pro-max** | Phase 4 lookup | **AVAILABLE** (plugin-namespaced) |
| **high-end-visual-design** | Phase 4 build | **AVAILABLE** (plugin-namespaced) |
| **impeccable** | Phase 4 build | **AVAILABLE** (`~/.claude/skills/impeccable/`) |
| **design-taste-frontend** | Phase 4 build | **AVAILABLE** (plugin-namespaced) |
| **gpt-taste** | Phase 4 motion (only on permitted templates) | **AVAILABLE** (plugin-namespaced) |
| **overdrive** | Phase 4 motion (only on permitted templates) | **AVAILABLE** (`~/.claude/skills/overdrive/`) |
| **delight** | Phase 4 polish | **AVAILABLE** (`~/.claude/skills/delight/`) |
| **bolder** | Phase 4 polish | **AVAILABLE** (`~/.claude/skills/bolder/`) |
| **polish** | Phase 7 pre-ship | **AVAILABLE** (`~/.claude/skills/polish/`) |
| **redesign-existing-projects** | Phase 3 | **AVAILABLE** (plugin-namespaced) |

All 12 generic design lens skills are AVAILABLE.

---

## Validation skills (V2 §4.3)

| Skill | V2 use | Status |
|-------|--------|--------|
| **eval-harness** | Phase 0 | **AVAILABLE** |
| **simplify** | Every edit | **AVAILABLE** |
| **verification-loop** | Every edit | **AVAILABLE** |
| **audit** | Phase entry + pre-ship | **AVAILABLE** |
| **critique** | Phase entry + pre-ship | **AVAILABLE** |
| **e2e-testing** | Phase 7 | **AVAILABLE** (`~/.claude/skills/e2e-testing/` referenced) |
| **ship-check wp** | Phase 7 final | **PARTIAL** (`/ship-check` skill is in available-skills as a project command; `ship-check wp` variant needs Phase 7 wiring) |

---

## Specialized agents (V2 §4.4)

| Agent | V2 phase | Status | Notes |
|-------|----------|--------|-------|
| **wordpress-pro** | 1–7 | **PARTIAL** — referenced as agent name; project has 4 specialized variants in `~/.claude/agents/`: `wp-frontend.md`, `wp-immersive.md`, `wp-security.md`, `wp-woocommerce.md`. Use these as substitutes per scope. |
| **woocommerce-backend-dev** | 5.1, 5.10 | **AVAILABLE** (skill `~/.claude/skills/woocommerce-backend-dev/` AND agent equivalents) |
| **php-pro** | 5.6, 5.7 | **GAP_DOCUMENTED** — no `php-pro` agent in `~/.claude/agents/`. **Substitute:** use Backend Architect (engineering subagent_type) + the wp-* agents for WP-specific PHP. The Backend Architect is a strong substitute for cross-system glue work. |
| **security-reviewer** | 5.1, 5.6, 5.10 | **AVAILABLE** (`~/.claude/agents/security-reviewer.md` + Skill) |
| **websocket-engineer** | 5.4 | **GAP_DOCUMENTED** — no dedicated agent. **Substitute:** Backend Architect + the existing WebSocket experience in claude-mem (cmem observations cover Pusher / drop queue patterns). For Phase 5.4, use Backend Architect with the V2 §3 integration architecture as the spec. |
| **immersive-interactive-architect** | 5.8 | **AVAILABLE** as `subagent_type` per main system prompt. Plus `~/.claude/agents/wp-immersive.md` for project-specific WebXR work. |
| **rag-architect** | 5.7 | **GAP_DOCUMENTED** — no dedicated agent. **Substitute:** Backend Architect + AI Engineer (both available as `subagent_type`) for Pinecone integration. AI Engineer's expertise in embedding pipelines + Backend Architect's API design = sufficient coverage for Phase 5.7. |
| **playwright-expert** | 7 | **GAP_DOCUMENTED** — no dedicated agent. **Substitute:** `e2e-runner` agent (`~/.claude/agents/e2e-runner.md`) is the closest match — handles Playwright + Page Object Model + CI integration per its description. Use it for Phase 7 e2e suite. |
| **vercel:ai-architect** | 5.9 | **GAP_DOCUMENTED** — `vercel:ai-architect` is plugin-namespaced; not visible in current `subagent_type` list. **Substitute:** Backend Architect + AI Engineer + the Vercel MCP server (which IS available). For Phase 5.9 Claude Lab admin tool: design the architecture with Backend Architect, implement with AI Engineer, deploy via Vercel MCP. |
| **vercel:deployment-expert** | Phase 6.5 perf | **GAP_DOCUMENTED** — same plugin-namespace gap. **Substitute:** Vercel MCP server (`mcp__claude_ai_Vercel__*` — deferred tool) for deploy/env/log inspection. DevOps Automator agent for deployment configuration. |
| **vercel:performance-optimizer** | Phase 6.5 | **GAP_DOCUMENTED** — same plugin-namespace gap. **Substitute:** `nextjs-performance` skill (AVAILABLE, project-relevant) + `Performance Benchmarker` agent (visible in `subagent_type` list). |
| **Backend Architect** | 5.6, 5.7, 5.10 | **AVAILABLE** as `subagent_type` |
| **Accessibility Auditor** | 6.3 | **AVAILABLE** as `subagent_type` |
| **Tracking & Measurement Specialist** | 6.6 | **AVAILABLE** as `subagent_type` |
| **Brand Guardian** | 6.8 | **AVAILABLE** as `subagent_type` (plus `~/.claude/agents/design/design-brand-guardian.md`) |
| **Cultural Intelligence Strategist** | 6.9 | **AVAILABLE** as `subagent_type` |
| **Inclusive Visuals Specialist** | 6.9 | **AVAILABLE** as `subagent_type` (plus `~/.claude/agents/design/design-inclusive-visuals-specialist.md`) |

**Net agent gaps to mitigate:**
1. `php-pro` → Backend Architect substitute
2. `websocket-engineer` → Backend Architect substitute
3. `rag-architect` → Backend Architect + AI Engineer substitute
4. `playwright-expert` → `e2e-runner` substitute
5. `vercel:ai-architect`, `vercel:deployment-expert`, `vercel:performance-optimizer` → combination of Backend Architect / AI Engineer / DevOps Automator + Vercel MCP server + `nextjs-performance` skill substitute

All gaps have substitutes; none are fatal to the V2 build. Phase 5 sub-phases that depend on the gapped agents will document the substitute used in their phase plan.

---

## MCP servers (auth status — Task 10)

Read-only inventory; no `_authenticate` calls triggered.

| MCP | V2 §4 / grill role | Status | Notes |
|-----|---------------------|--------|-------|
| **Context7** (`mcp__claude_ai_Context7__*`) | verify-impl Step 2 primary source | **AVAILABLE — auth-on-use** | Tools `resolve-library-id` + `query-docs` confirmed in deferred list. First call triggers auth; free per `eval/cost-cap-policy.md`. |
| **Vercel** (`mcp__claude_ai_Vercel__*`) | Phase 0.5/5/7 deploy ops | **AVAILABLE — auth-on-use** | 18+ tools confirmed in deferred list. CLAUDE.md confirms `.vercel/project.json` linked, so first MCP call should succeed without re-auth. |
| **WordPress.com** (`mcp__claude_ai_WordPress_com__*`) | Phase 1 page reassignments + Phase 0 design tokens | **AVAILABLE — auth-on-use** | 5 tools confirmed (wpcom-mcp-account, wpcom-mcp-content-authoring, wpcom-mcp-site, wpcom-mcp-site-editor-context, wpcom-mcp-user-sites). Plus separate `mcp__wpcom-mcp__authenticate`/`complete_authentication` flow. |
| **Klaviyo** (`mcp__claude_ai_Klaviyo__*`) | Phase 5.4 flow inspection + Phase 0.5 baseline pull | **AVAILABLE — auth-on-use** | 30+ tools confirmed in deferred list (campaigns, flows, lists, profiles, metrics, events, templates). |
| **Stripe** (`mcp__stripe__*`) | Phase 0.5 prereq check + Phase 5.10 | **AVAILABLE — explicit auth** | Has separate `mcp__stripe__authenticate` and `mcp__stripe__complete_authentication`. Phase 0.5.a prereq check will trigger first auth. |
| **GitHub** (`mcp__github__*`) | Phase 7 PR creation | **AVAILABLE — explicit auth** | Has `mcp__github__authenticate`/`complete_authentication`. First auth triggers Phase 7 entry; until then, gh CLI fallback works. |
| **Sentry** (`mcp__claude_ai_Sentry__*` + `mcp__sentry__*`) | Phase 6.5 perf + Phase 7 post-deploy | **AVAILABLE — both flavors** | `mcp__claude_ai_Sentry__*` has 22 tools (analyze_issue_with_seer, search_events, search_issues, etc.). `mcp__sentry__authenticate` is the alternate auth path. |
| **Hugging Face** (`mcp__claude_ai_Hugging_Face__*`) | Phase 5.7 (custom embeddings) + Phase 5.6 (alt AR) | **AVAILABLE — pre-authenticated as `damBruh`** per main system prompt instructions |
| **Apify** (`mcp__apify__*`) | Phase 4 luxury ref scraping + Phase 6.7 SEO | **AVAILABLE — auth-on-use** | 60+ scraper tools confirmed. Defer first call to Phase 4. |
| **claude-in-chrome** (`mcp__claude-in-chrome__*`) | Phase 0 §3 critique + Phase 6 audits | **AVAILABLE — needs ToolSearch load** | Per system reminder, must `ToolSearch` to load schemas before invoking. Already in use by §3 critique subagent (running). |
| **aidesigner** (`mcp__aidesigner__*`) | Phase 4 design-ref B | **AUTH FLOW INITIATED 2026-05-03** | `mcp__aidesigner__authenticate` called — OAuth URL emitted, awaits one-click browser completion. Once done, full `mcp__aidesigner__*` toolkit unlocks. Until then: skill (`aidesigner-frontend`) and npx CLI (`AIDESIGNER_API_KEY` in `.env`) both work as alternates. Per `eval/cost-cap-policy.md`: every aidesigner generation call = STOP-AND-SHOW (>$1 tier) regardless of which path invokes it. |
| **graphify** | Phase 0 deliverable J | **AVAILABLE — skill-installed** | Skill at `~/.claude/skills/graphify/`. Triggers via `/graphify`. MCP server mode via `--mcp` flag during invocation. |

**MCPs explicitly NOT integrated in Phase 0** (per grill Branch 4 user answer "C" with no Figma/Notion/Drive additions):

| MCP | Why skipped | Re-evaluate when |
|-----|-------------|------------------|
| Figma (`mcp__claude_ai_Figma__*`) | User did not confirm SkyyRose Figma designs exist | If Figma designs added later, ingest as `eval/luxury-references.md` foundation |
| Notion (`mcp__notion__*`) | User did not confirm brand/roadmap docs in Notion | If Notion docs surface |
| Google Drive (`mcp__claude_ai_Google_Drive__*`) | User did not confirm brand assets in Drive | If asset library surfaces |
| Linear (`mcp__linear__*`) | No evidence of issue tracking on this project | If Linear adopted |
| Stitch (`mcp__stitch__*`) | Phase 4 design supplement only | When Phase 4 design phase begins |
| Three.js 3D Viewer (`mcp__claude_ai_Three_js_3D_Viewer__*`) | Handy for Phase 5.2/5.8 but not load-bearing | When Phase 5.2 begins |
| Computer-use (`mcp__computer-use__*`) | Native desktop apps; not needed for V2 build | If a native-app workflow surfaces |
| Sequential Thinking (`mcp__sequential-thinking__sequentialthinking`) | **RESOLVED 2026-05-03** — was disabled by rename in `~/.claude/settings.json`. Re-enabled by creating proper `mcpServers` block. Surfaces in deferred-tools list on next session restart. | None — tool available next session. |

---

## Sequential Thinking — RESOLVED 2026-05-03

**Root cause discovered:** the MCP server was configured but parked under the key `_disabled_mcpServers__rename_to_mcpServers_to_reenable` in `~/.claude/settings.json` — Claude Code only loads servers under the literal key `mcpServers`. The rule file at `.claude/rules/sequential-thinking.md` was correct; the config was just keyed wrong.

**Fix applied:**

1. Created top-level `mcpServers` block in `~/.claude/settings.json` containing only `sequential-thinking` (pure npx, no infra dependencies)
2. Renamed remaining disabled block to `_disabled_mcpServers__claude_context_needs_milvus` to document *why* `claude-context` stays disabled (requires Milvus on `127.0.0.1:19530` which isn't running; Ollama on `11434` IS running so the embedding side would work, but the vector store wouldn't)
3. Tool surfaces on next session restart — current session must finish first

**Why claude-context stays disabled:** enabling it without Milvus running would error on every session start. To enable later: install Milvus locally (`docker run -p 19530:19530 milvusdb/milvus`) then move `claude-context` from the disabled block into `mcpServers`.

---

## Plugin/MCP skills (V2 §4.5)

| Plugin/MCP | V2 use | Status |
|------------|--------|--------|
| `pinecone:quickstart` | Phase 5.7 entry | **PARTIAL** — `pinecone` is not in deferred MCP list (only `mcp__plugin_pinecone__*` referenced via V2 plan). **Substitute:** Phase 5.7 uses Pinecone REST API directly via Vercel route, skipping the MCP layer. The Vercel route can call Pinecone with a service key. |
| `mcp__plugin_pinecone__upsert-records` | Phase 5.7 | **GAP_DOCUMENTED** — same as above. Substitute via direct Pinecone REST call from Vercel route. |
| `mcp__plugin_pinecone__search-records` | Phase 5.7 | Same |
| `mcp__claude_ai_Klaviyo__*` | Phase 5.4 | **AVAILABLE** (per MCP table above) |
| `vercel:vercel-sandbox` | Phase 5.6, 5.7 | **GAP_DOCUMENTED** — `vercel-sandbox` not in deferred tools as separate item. **Substitute:** Vercel preview deployments (`vercel deploy --prebuilt --target=preview`) for testing FASHN/Pinecone proxies before WP wires them. |
| `mcp__stripe__authenticate` | Phase 5.10 | **AVAILABLE** (per MCP table above) |
| `commit-commands:commit-push-pr` | After every milestone | **GAP_DOCUMENTED** — `commit-commands` plugin not visible. **Substitute:** Use `gh pr create` via GitHub MCP (Phase 7) and standard `git commit` per CLAUDE.md `git-workflow.md` rules. |

---

## Net inventory verdict

**Skills:** 100% AVAILABLE for V2 §4.1, §4.2, §4.3 (19 of 19 referenced).

**Agents:** 8 of 12 V2 §4.4 specialized agents AVAILABLE; 4 GAP_DOCUMENTED with explicit substitutes (php-pro → Backend Architect; websocket-engineer → Backend Architect; rag-architect → Backend Architect + AI Engineer; playwright-expert → e2e-runner; vercel:* trio → Backend Architect/AI Engineer/DevOps Automator + nextjs-performance + Vercel MCP).

**MCPs:** All V2-required MCPs AVAILABLE (12 servers, all in deferred-tools list). Plus 1 explicit gap (Sequential Thinking — documentation/reality mismatch logged for later resolution). Plus 4 plugin-namespaced gaps (vercel:*, pinecone:*, vercel-sandbox, commit-commands) with substitutes.

**Phase 5 sub-phase impact:** Phase 5.4 (drop queue), 5.6 (FASHN), 5.7 (Pinecone), 5.8 (WebXR), 5.9 (Claude Lab), 5.10 (Stripe) all need to use substitute agents per the gap table. Each Phase 5 sub-phase plan must document the substitute chosen in its plan file.

**Phase 0 verdict:** No blocker. Phase 0 advances. Gap-mitigation strategies are documented; phase-by-phase substitution is explicit.

---

## Test command

```bash
node scripts/measurement/check-agent-inventory.js
```

Reads this file. Exits 0 if every row has `AVAILABLE | SUBSTITUTE_AVAILABLE | GAP_DOCUMENTED` (current state). Exits 1 only if a row is `FOUND_GAP` (no substitute documented) — which the current audit has zero of.

---

## Phase entry checklist

- Phase 0 (this file) establishes the audit
- Phase 0.5 prerequisite check verifies MCP auth where state-change auth is needed (Stripe, GitHub, Sentry, Vercel)
- Each Phase 5 sub-phase plan that uses a substitute names the substitute in the plan
- Phase 7 ship-check re-runs this audit; any new gaps surfaced during build → addressed before deploy
