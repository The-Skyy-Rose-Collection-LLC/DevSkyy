# SuperAgent Self-Healing + Learning Audit — 2026-05-03

**Audit type:** read-only inventory feeding a migration plan
**Scope:** every Python class in this repo that names itself `*Agent` or inherits from a `*SuperAgent` base
**Status:** ready to grill — no code changes proposed yet

---

## TL;DR

There are **two architectural concerns** ("self-healing" and "self-learning") implemented in **two separate modules**, mixed into **four parallel inheritance hierarchies**. **No agent in the codebase currently has both.** The migration question is not "audit one mixin and add it to the agents that lack it" — it's "decide whether self-heal and self-learn should be unified, who the canonical base is, and which lineage each agent should converge on."

| Concern | Module | File | Adopters |
|---|---|---|---|
| Self-healing (diagnose/heal/circuit breaker) | `SelfHealingMixin` | `agents/core/base.py:198` | 8 CoreAgents (via `CoreAgent(SelfHealingMixin)` at line 515) |
| Self-learning (prompt optimization + RAG ingestion) | `SelfLearningModule` | `agents/base_super_agent/learning_module.py:27` | 1 base class (`EnhancedSuperAgent`); 13 subclasses inherit transitively |

`agents/CLAUDE.md` says the canonical base is `SuperAgent` from `agents.core.base`. But `agents/core/base.py:744` re-exports that name from `agents/base_legacy.py` — the same module the doc tells you not to import from. **The "correct" import path resolves to the "deprecated" class.** That contradiction has to be resolved before any migration plan ships.

---

## Hierarchy map (verified)

### 1. Self-healing branch — `agents/core/base.py`
```
SelfHealingMixin                        # universal heal/diagnose/circuit breaker
└── CoreAgent                           # abstract; .execute() + sub-agent delegation
    ├── AnalyticsCoreAgent              # agents/core/analytics/agent.py:21
    ├── CommerceCoreAgent               # agents/core/commerce/agent.py:24
    ├── ContentCoreAgent                # agents/core/content/agent.py:21
    ├── CreativeCoreAgent               # agents/core/creative/agent.py:21
    ├── ImageryCoreAgent                # agents/core/imagery/agent.py:21
    ├── MarketingCoreAgent              # agents/core/marketing/agent.py:21
    ├── OperationsCoreAgent             # agents/core/operations/agent.py:21
    └── WebBuilderCoreAgent             # agents/core/web_builder/agent.py:24
```
**Has self-heal:** ✅ (inherited)
**Has self-learn:** ❌ (no `SelfLearningModule` import anywhere in `agents/core/`)

### 2. Self-learning branch — `agents/base_super_agent/`
```
EnhancedSuperAgent                      # owns SelfLearningModule + ML + Round Table
├── AnalyticsAgent                      # agents/analytics_agent.py:48
├── CollectionContentAgent              # agents/collection_content_agent.py:33
├── CommerceAgent                       # agents/commerce_agent.py:57
├── CreativeAgent                       # agents/creative_agent.py:76
├── MarketingAgent                      # agents/marketing_agent.py:48
├── OperationsAgent                     # agents/operations_agent.py:48
├── SecurityOpsAgent                    # agents/security_ops_agent.py:31
├── SkyyRoseContentAgent                # agents/skyyrose_content_agent.py:271
├── SkyyRoseImageryAgent                # agents/skyyrose_imagery_agent.py:166
├── SupportAgent                        # agents/support_agent.py:48
├── WordPressAssetAgent                 # agents/wordpress_asset_agent.py:72
├── CodingDoctorAgent ⚠️                # agents/coding_doctor_agent.py:990 — has its OWN SelfLearningEngine + SelfHealingEngine, ignores inherited modules
└── (no others)
```
**Has self-heal:** ❌ (no `SelfHealingMixin` in MRO; `EnhancedSuperAgent`'s own base is `BaseDevSkyyAgent`, not `SelfHealingMixin`)
**Has self-learn:** ✅ (inherited; subclasses don't override or extend — they trust the base)

### 3. Legacy branch — `agents/base_legacy.py` (re-exported via `agents.core.base`)
```
SuperAgent  (from base_legacy, ABC)
├── LegacyEnhancedSuperAgent            # agents/enhanced_base.py:392
├── FashnTryOnAgent                     # agents/fashn_agent.py:190
├── TripoAssetAgent                     # agents/tripo_agent.py:238   ← active in 3D round table
├── AniGenAgent                         # agents/anigen_agent.py:126
└── MeshyAgent                          # agents/meshy_agent.py:230
```
**Has self-heal:** ❌
**Has self-learn:** ❌
**`agents/CLAUDE.md` says:** "do not use; will be removed" — but also "Custom agents extend `SuperAgent` from `agents.core.base`", which resolves to this same class. Contradiction.

### 4. SDK branch — `sdk/python/adk/super_agents.py`
```
BaseSuperAgent  (sdk/python/adk/super_agents.py:57)
├── 6 in-file siblings (CommerceAgent, CreativeAgent, MarketingAgent,
│                       SupportAgent, OperationsAgent, AnalyticsAgent)
│                       ← name collision with branch #2
└── Used by 6 elite_studio agents:
    ├── VariantAgent                    # skyyrose/elite_studio/agents/variant_agent.py:23
    ├── TryOnAgent                      # …/tryon_agent.py:23
    ├── ColorCorrectionAgent            # …/color_correction_agent.py:24
    ├── DualVisionGate                  # …/vision_agent.py:84  ← relevant to Option 2 (dual vision schema)
    ├── QualityAgent                    # …/quality_agent.py:79
    ├── GeneratorAgent                  # …/generator_agent.py:34
    └── ThreeDAgent (via CreativeAgent) # …/three_d_agent.py:49
```
**Has self-heal:** ❌
**Has self-learn:** ❌

---

## Coverage matrix

| Hierarchy | Count | Self-heal | Self-learn | Both |
|---|---|---|---|---|
| `CoreAgent` (#1) | 8 | ✅ | ❌ | — |
| `EnhancedSuperAgent` (#2) | 13 | ❌ | ✅ | — |
| Legacy `SuperAgent` (#3) | 5 | ❌ | ❌ | — |
| SDK `BaseSuperAgent` (#4) | 6 elite_studio + 6 in-file | ❌ | ❌ | — |
| **Total** | **38** | **8** | **13** | **0** |

Plus ~30 SDK sub-agents (`SDKSubAgent` lineage) and ~10 ADK wrapper agents — none touch either system. Excluded above because they're worker classes that probably don't need either, but flagged here for the grill: do they?

---

## The CodingDoctorAgent outlier

`agents/coding_doctor_agent.py:990` extends `EnhancedSuperAgent` (so it inherits `SelfLearningModule`) **and** owns its own private `SelfLearningEngine` (line ~390s) + `SelfHealingEngine` (line 386). It calls `self.learning_engine.learn(...)` and never touches `self.learning_module`. Two possible reads:

1. **Domain-specific specialization** — code-fix learning is structurally different from prompt-technique learning (it persists fix recipes per error signature, not (prompt, technique, score) tuples). The agent reasonably owns its own engine.
2. **Drift artifact** — the agent was written before `SelfLearningModule` was promoted to the base, and nobody migrated it.

Reading the file before the migration plan ships will tell us which. (~10 min, single-file read.)

---

## Open architectural questions (these are the grill targets)

### Q1. Are self-healing and self-learning one concern or two?
- **One concern argument:** "Learn from outcomes" is fundamentally what both do. Self-heal records fix attempts in `_heal_journal`; self-learn records (prompt, technique, score). They're both feedback loops over execution outcomes.
- **Two concerns argument:** Self-heal is about *resilience* (does this agent survive a bad day?). Self-learn is about *improvement* (does this agent get better over time?). Different lifecycles, different storage shapes, different consumers. Mixing them couples retry logic to RAG ingestion.

**Decision blocks:** the migration shape. Unifying = one mixin. Keeping separate = two mixins or a `BaseAgent` that composes both.

### Q2. What is the canonical base going forward?
Three candidates, three migration shapes:

| Candidate | Migration cost | What it implies |
|---|---|---|
| `EnhancedSuperAgent` (#2) | Add `SelfHealingMixin` to its bases. Delete `base_legacy.py` re-export. Migrate the 5 legacy agents and 6 SDK elite_studio agents. | The "modular runtime" wins. `agents/core/base.py::SelfHealingMixin` becomes a building block, not a base. |
| `CoreAgent` (#1) | Add `SelfLearningModule` ownership to `CoreAgent.__init__`. Migrate the 13 EnhancedSuperAgent subclasses to subclass CoreAgent instead. | The "8 domain core agents" architecture wins. The 6-SuperAgent model collapses into the 8-CoreAgent model. |
| New `BaseAgent` | Compose `SelfHealingMixin` + `SelfLearningModule` into one new base. Migrate everyone. | Most code churn, cleanest result. Likely a 2-3 week project. |

### Q3. Does `agents/CLAUDE.md` need fixing first?
The doc tells future maintainers (and future Claude sessions) to use `SuperAgent` from `agents.core.base`, which today resolves to the legacy class the same doc says is deprecated. Either:
- The doc is stale and the canonical base is actually something else (e.g., `EnhancedSuperAgent` or `CoreAgent`), or
- `agents/core/base.py:744` should stop re-exporting from `base_legacy` and instead define a fresh `SuperAgent` that composes both mixins.

**This must be answered before code lands** — otherwise the migration encodes the contradiction.

### Q4. Is the SDK lineage (#4) in scope?
The 6 elite_studio agents (`VariantAgent`, `TryOnAgent`, `ColorCorrectionAgent`, `DualVisionGate`, `QualityAgent`, `GeneratorAgent`) extend `BaseSuperAgent` from `sdk/python/adk/super_agents.py` — a parallel SDK hierarchy with no learning, no healing. Either:
- They're "external" SDK consumers and should stay isolated from internal infra, or
- The SDK base should compose the same mixins as the internal base, so SDK consumers get heal/learn for free.

`DualVisionGate` is directly relevant to Option 2 from the queue (the dual vision schema work) — whatever lineage decision lands here will shape how that SPEC.md gets written.

### Q5. Are sub-agents (SDKSubAgent, ClaudeSDKBaseAgent, CoreAgent's `_sub_agents`) in scope?
~30 worker-style agents inherit from sub-agent bases. They probably don't need their own learning — their parent CoreAgent should learn for them. But `SelfHealingMixin.health_check()` already walks sub-agents looking for `SelfHealingMixin` instances (line 430). Sub-agents that aren't healing-aware are invisible to the health check. Either:
- Add `SelfHealingMixin` to `SDKSubAgent` and `ClaudeSDKBaseAgent` (~30 file change), or
- Document that sub-agent health is the parent's responsibility and remove the recursive walk from `health_check()`.

---

## Three migration shapes to choose from

### Option A — "Compose at the base, no per-agent edits" (smallest)
1. Add `SelfHealingMixin` to `EnhancedSuperAgent`'s bases.
2. Add `SelfLearningModule` to `CoreAgent.__init__`.
3. Stop re-exporting `SuperAgent` from `base_legacy` in `agents/core/base.py`. Migrate the 5 legacy agents to `EnhancedSuperAgent`.
4. Update `agents/CLAUDE.md` to name `EnhancedSuperAgent` as canonical (or whatever Q2 lands on).
5. Leave SDK lineage (#4) alone for a follow-up.

**Touches:** 2 base files + 5 legacy agents + 1 doc = ~8 files.
**Risk:** SDK elite_studio agents still lack heal/learn. Two parallel base classes still exist.

### Option B — "Unify on `EnhancedSuperAgent`" (medium)
A + migrate the 6 SDK elite_studio agents to `EnhancedSuperAgent`. Touches ~14 files. SDK in-file siblings stay where they are (they're SDK example code, not production agents).

### Option C — "New `BaseAgent`, migrate everyone" (largest)
New base composing both mixins. Migrate all 38 agents. Touches ~40 files. Cleanest end state, biggest blast radius.

---

## Recommended sequence

Before any code:

1. **Read `agents/coding_doctor_agent.py`** to settle whether its private engines are domain specialization or drift (resolves Q1's edge case).
2. **Settle Q2 + Q3 with the user** — these are decisions, not investigations.
3. **Pick A / B / C.**

Then migrate. Each per-agent edit is small (add one base class, call one new init). The cost is in the decisions, not the diff.

---

## What I did NOT do

- Did not edit any agent file.
- Did not run tests.
- Did not look at `agents/coding_doctor_agent.py` internals (called out as a follow-up read).
- Did not check whether `EnhancedSuperAgent`'s `execute()` actually invokes `SelfLearningModule.record_execution` — assumed yes based on the audit summary, but should be verified before migration.
- Did not investigate the SDK base (`sdk/python/adk/super_agents.py::BaseSuperAgent`) for hidden hooks the SDK might already provide.

These three follow-ups are ~30 min combined and should happen before the migration plan is committed to.
