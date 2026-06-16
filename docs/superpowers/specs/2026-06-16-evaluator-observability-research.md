# Evaluator + Observability Agents — Research Report
*Generated: 2026-06-16 | Sources: ~55 | Confidence: High (LLM-as-judge, self-correction, observability standards); Medium (some 2026 single-source vendor findings, flagged inline)*

Companion to the design spec `2026-06-16-evaluator-observability-agents-design.md`. This report pressure-tests every design decision against 2024–2026 literature before the spec was locked. Each section ends with the concrete design delta it produced.

---

## Executive Summary

Four research clusters were investigated in parallel: (1) LLM-as-a-judge reliability, (2) iterative self-correction loops, (3) agent-observability metric standards, (4) anomaly detection & alerting. Key outcomes:

- **The evaluator's external-feedback revise loop is architecturally correct** — the well-known "LLMs cannot self-correct" finding (Huang et al. 2023) applies only to *intrinsic* self-correction with no external signal. Our loop is driven by a deterministic fact-gate + a separate judge, which is the validated path (CRITIC, Reflexion, TICK).
- **Two evaluator details were wrong:** a 0–1 continuous score should be a **0–5 integer scale** (maximizes human alignment), and scoring should be **criterion-separated with chain-of-thought**, not one holistic number.
- **Self/family-preference bias is real and unquantified for Claude-judging-Claude copy** — requires concrete mitigations (blind authorship, ground criteria to locked phrases, build a calibration set).
- **The observability metric record should adopt OpenTelemetry GenAI semantic-convention field names** — critically, split `tokens_used` into `input_tokens` + `output_tokens` (output costs 3–5× more) and store a computed `cost_usd`.
- **The 5 detection rules have the right instinct** (statics for retry-storm/dead-agent/loop, rolling baseline for spend/latency), but the design is **missing the single most important rule for agent fleets: a per-conversation cumulative cost accumulator** — the failure mode behind a documented $47K runaway loop that left dashboards green for 11 days.

---

## 1. LLM-as-a-Judge Reliability

### Documented biases (all quantified in sources)
- **Position bias**: order-swap shifts accuracy 10–30pp; worst when candidates are close in quality (the copy-scoring regime). Claude-v1 ~70% first-position preference ([arXiv:2406.07791](https://arxiv.org/abs/2406.07791); [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)).
- **Verbosity bias**: Claude-v1 & GPT-3.5 preferred longer responses >90% of the time even with zero added substance ([Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)).
- **Self/family-preference bias**: GPT-4 recognizes its own good output 94.5% vs 42.5% for identical-quality others (52pp gap). GPT-4o **and Claude 3.5 Sonnet** both show family-bias. Mechanism is **perplexity preference** — a Claude judge rates Claude-style copy higher even without knowing it wrote it ([arXiv:2410.21819](https://arxiv.org/abs/2410.21819); [arXiv:2604.06996](https://arxiv.org/pdf/2604.06996)).
- **Leniency / central tendency**: LLM judges cluster toward the middle/high; LLM-vs-human gaps often ≥0.5 on a 5-pt scale; judges are overconfident ([arXiv:2506.22316](https://arxiv.org/html/2506.22316v1); [Deepchecks](https://deepchecks.com/llm-judge-calibration-automated-issues/)).
- **Prompt-format sensitivity**: phrasing/delimiter/ID changes swing accuracy up to 76pp; polarity inversion ("has errors?" vs "is error-free?") causes near-universal disagreement ([arXiv:2604.23478](https://arxiv.org/html/2604.23478v1)).
- **Beauty/authority bias** (CALM, [arXiv:2410.02736](https://arxiv.org/pdf/2410.02736)): premium-sounding vocabulary inflates scores — a specific luxury-copy hazard.

### Single judge vs panel
- **PoLL** (3 small models) beat GPT-4 on human correlation at 7× lower cost across 6 datasets ([arXiv:2404.18796](https://arxiv.org/html/2404.18796v1)).
- **Counter-finding (2025)**: a 9-judge panel had effective sample size of only 2.18 (24% of nominal) due to correlated errors (mean φ=0.391); **the best single judge matched the full panel** ([arXiv:2605.29800](https://arxiv.org/html/2605.29800), single-source — strong but unreplicated). Net: a good single judge is defensible; panels only help with architectural diversity.

### Scoring format
- **0–5 integer scale maximizes human-LLM alignment** ([arXiv:2601.03444](https://arxiv.org/pdf/2601.03444)). 0–1 float gives false precision; the judge cannot meaningfully distinguish 0.73 from 0.79.
- **Criterion-separated scoring** (score each rubric dimension separately) prevents invisible trade-offs and makes failures debuggable.
- **Chain-of-thought before the score** is the single highest-leverage technique across all sources ([LLM-Rubric arXiv:2501.00274](https://hf.co/papers/2501.00274); [Evidently](https://www.evidentlyai.com/llm-guide/llm-as-a-judge); [Langfuse](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)).
- Pointwise (not pairwise) is right when you need a decision signal rather than a ranking.

### Calibration
- Acceptable agreement: Cohen's κ ≥ 0.70 target (≥0.80 strong; <0.40 inadequate); Pearson r ≥ 0.80. Human-human κ ≈ 0.80 is the ceiling ([arXiv:2510.09738](https://arxiv.org/pdf/2510.09738); [Trust or Escalate arXiv:2407.18370](https://hf.co/papers/2407.18370)).
- Validate against a **100–200 expert-labeled ground-truth set** spanning the score distribution before using the judge as a hard gate; re-validate monthly on 20–30 production samples ([Confident AI/DeepEval](https://www.confident-ai.com/blog/the-ultimate-llm-evaluation-playbook)).
- Expect 10–15% degradation vs genuine domain experts (luxury copywriters) vs generic annotators.

### → Design deltas
1. **Score on a 0–5 integer scale, not 0–1.** Map: 1–2 = auto-reject/revise, 3–4 = pass to human, 5 = fast-track.
2. **Criterion-separated scoring** — brand-voice, clarity, persuasiveness as separate judge evaluations, each with a CoT reasoning trace, not one holistic number.
3. **CoT-before-score** mandatory in the judge prompt.
4. **Self-preference mitigations**: blind the judge to authorship (never state "AI-written"); ground brand-voice criteria to **specific locked phrases / canonical copy examples / named banned patterns**, not abstract adjectives; add explicit anti-verbosity rubric language ("length is not a quality signal").
5. **Borderline handling**: scores within ±1 (on the 5-scale, ±0.5 normalized) of the pass threshold trigger a position-swapped re-check; if still ambiguous, flag for human rather than auto-deciding.
6. **Calibration set is a phase-0 prerequisite**: ~100 expert-labeled drafts; compute κ; if κ < 0.65, the judge ships as a *soft signal* (annotate) only, not a hard gate, until the rubric is fixed.
7. **Cross-link to Observer**: the judge's own score distribution (mean/variance over time) is a metric the Observer should watch for leniency drift.

---

## 2. Iterative Self-Correction / Revise Loops

### Core finding: external vs intrinsic is the whole ballgame
- **Self-Refine** (2023) reported ~20% gains from self-critique ([arXiv:2303.17651](https://arxiv.org/abs/2303.17651)), but **Huang et al. "LLMs Cannot Self-Correct Reasoning Yet"** (ICLR 2024) showed intrinsic self-correction is unreliable and sometimes *degrades* output ([arXiv:2310.01798](https://arxiv.org/abs/2310.01798)).
- The reconciliation (TACL survey; CorrectBench 2025): self-correction **works with reliable external feedback** (tools, verifiers, ground truth) and fails without it ([TACL](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00713/125177/When-Can-LLMs-Actually-Correct-Their-Own-Mistakes); [CorrectBench](https://hf.co/papers/2510.16062); [CRITIC arXiv:2305.11738](https://arxiv.org/abs/2305.11738); [Reflexion arXiv:2303.11366](https://arxiv.org/abs/2303.11366)).
- **Self-Correction Blind Spot** (2025): models fail to fix their *own* errors 64.5% of the time that they'd fix in others' output ([arXiv:2507.02778](https://hf.co/papers/2507.02778)) — irrelevant to us because our critique comes from a separate evaluator.

### Iteration count
- Gains saturate by ~3 loops; most value in revision 1; creative/ideation gains arrive earliest ([Self-Review arXiv:2507.05598](https://arxiv.org/pdf/2507.05598); [Turn-Wise arXiv:2509.06770](https://arxiv.org/abs/2509.06770)).
- **Degradation is real**: vague feedback "plateaus or reverses correctness after the first few turns"; iterative code-gen introduces security defects correctness tests miss ([arXiv:2506.11022](https://arxiv.org/html/2506.11022)); long-horizon agents bloat without semantic gain ([SlopCodeBench arXiv:2603.24755](https://arxiv.org/pdf/2603.24755)).

### Critique specificity
- Targeted critique "reliably shifts the intended quality axis"; vague critique plateaus/reverses ([Turn-Wise](https://arxiv.org/abs/2509.06770)).
- **TICK** decomposed YES/NO checklists improved evaluator-human agreement 46.4%→52.2% and drove +7.8% generation gains ([arXiv:2410.03608](https://arxiv.org/abs/2410.03608)).
- Informative critique (cite passage, name error type, suggest fix) beats summary judgments ([CritiqueLLM arXiv:2311.18702](https://arxiv.org/abs/2311.18702); [DeepCritic arXiv:2505.00662](https://hf.co/papers/2505.00662)).

### Creative/marketing-copy domain risks
- **RLHF reduces creative diversity** — aligned models form low-entropy "attractor states"; explicitly flagged for copywriting ([arXiv:2406.05587](https://arxiv.org/abs/2406.05587)). Each revision pass may flatten voice.
- **Decoupling critic from generator** prevents homogenization ([LLM Review arXiv:2601.08003](https://arxiv.org/abs/2601.08003)) — our separate evaluator is the right topology.
- Self-Refine's strongest result was sentiment reversal (+21.6pp) — a clear binary objective embedded in open text, which maps to catalog fact-correction in copy.

### → Design deltas
1. **Loop architecture validated** — keep it; emphasize in spec that this is *external-feedback* correction, citing the distinction.
2. **Cap 2 is correct**; add **early-exit**: if revision 1 clears the deterministic gate AND scores ≥ threshold, stop (don't spend slot 2).
3. **Critique format spec**: cite the exact failing check + the offending text fragment; structure as YES/NO checklist items; **separate fact-corrections (comply) from style critique (balance)**; no generic praise/encouragement.
4. **SKU-specific grounding**: pull the per-SKU dossier into the critique context so corrections are product-specific (prevents cross-SKU homogenization; aligns with the project's canonical-sources rule).
5. **Named domain risk in spec**: aligned-judge attractor states may flatten revision-2 voice — rubric must include a distinctiveness check, and the system should preserve/compare the revision-1 candidate on creative dimensions.

---

## 3. Agent Observability Metric Standards

### OpenTelemetry GenAI semantic conventions
- Status: **"Development"** (a governance label, not adoption risk) as of semconv v1.40.0 (Apr 2026); in production at Datadog, Langfuse, MLflow, LiteLLM ([OTel GenAI blog](https://opentelemetry.io/blog/2026/genai-observability/); [registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)).
- Canonical fields: `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, **`gen_ai.usage.input_tokens`** + **`gen_ai.usage.output_tokens`** (deprecated: `prompt_tokens`/`completion_tokens`), `gen_ai.usage.cache_read.input_tokens`, `gen_ai.response.finish_reasons`, `error.type`, `gen_ai.conversation.id`. Agent spans add `gen_ai.agent.name/id/version`, `gen_ai.tool.name`, `gen_ai.workflow.name` ([registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/); [agent-spans spec](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/); [cheat sheet](https://techbytes.app/posts/opentelemetry-genai-agent-semconv-cheat-sheet-2026/)).
- Metrics: `gen_ai.client.operation.duration` (s) and `gen_ai.client.token.usage` ({token}) histograms ([gen-ai-metrics](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-metrics.md)).

### What mature platforms track
- **Langfuse**: trace→span→generation; per-generation tokens (input/output/total), `calculatedInput/Output/TotalCost` (USD, from a pricing table at ingest), start/end time, level, statusMessage, tags, metadata; storage Postgres + ClickHouse ([token & cost](https://langfuse.com/docs/observability/features/token-and-cost-tracking); [self-hosting](https://langfuse.com/self-hosting)).
- **Arize Phoenix** (OpenInference), **OpenLLMetry** (Traceloop — drove the OTel spec), **LangSmith** (Run tree, total_cost, feedback_stats) — all converge on the same field vocabulary and all added OTel ingestion in 2025 ([Phoenix](https://arize.com/blog/llm-tracing-and-observability-with-arize-phoenix/); [OpenLLMetry](https://github.com/traceloop/openllmetry); [LangSmith OTel](https://blog.langchain.com/opentelemetry-langsmith/)).

### Cost attribution
- Universal pattern: `cost = input_tokens×price_in + output_tokens×price_out (+ cache_read×price_cache)`. **Output tokens cost 3–5× input** — storing only a combined total makes cost non-reconstructable ([CloudZero](https://www.cloudzero.com/blog/llm-api-pricing-comparison/); [pricing guide](https://pecollective.com/blog/llm-token-pricing-guide/)).
- No OTel attribute for cost; compute at insert from a maintained pricing table, recompute on rate change.

### Trace vs metric vs log
- Traces = the primary signal for *debugging* agent behavior (span hierarchy, tool sequence); metrics (histograms) = the *alerting* primitive; logs = error detail correlated by trace_id. A flat Postgres table serves alerting + cost but **not** debugging (no span hierarchy) ([VictoriaMetrics](https://victoriametrics.com/blog/ai-agents-observability/); [OpenObserve](https://openobserve.ai/blog/opentelemetry-for-llms/)).

### Build vs adopt
- Consensus: **adopt OTel naming + instrumentation, keep Postgres for the flat alerting table, optionally bolt on Langfuse Cloud free tier later.** Don't invent field names; don't stand up self-hosted Langfuse (Postgres+ClickHouse+Redis+S3) just for a flat table ([build-vs-adopt synthesis](https://www.digitalapplied.com/blog/agent-observability-platforms-langsmith-langfuse-arize-2026); [opentelemetry-instrumentation-openai-v2](https://pypi.org/project/opentelemetry-instrumentation-openai-v2)).

### → Design deltas
1. **Adopt OTel GenAI field names** for the metric record (dotted→underscored in Postgres columns, documented mapping).
2. **Split tokens**: extend `AgentExecution` (currently only `tokens_used` + `duration_ms`) with `input_tokens`, `output_tokens`, `cache_read_tokens`, computed `total_tokens`, `cost_usd` (NUMERIC), `finish_reason`, `error_type`, `provider_name`, `request_model`, `trace_id`, `retry_attempt`, `conversation_id`. Alembic migration required.
3. **Compute `cost_usd` at insert** from a maintained pricing table (config-driven; recompute-on-rate-change supported).
4. **Scope honesty**: v1 = flat Postgres table for alerting + cost attribution at the `execute_safe` seam. **OTel span emission (OTLP) for debugging the span hierarchy = phase 2.** Optional Langfuse Cloud = phase 2.

---

## 4. Anomaly Detection & Alerting

### Statics vs statistical
- Static thresholds are correct for **absolute/policy conditions** (step cap, cost ceiling, dead-agent zero, retry-storm count). Rolling baselines (EWMA/z-score) only where variance is inherent (spend, latency); need ≥3× the strongest seasonal cycle of data (7–30 days) ([OpenObserve](https://openobserve.ai/blog/ai-anomaly-detection-guide/); [incident.io](https://incident.io/blog/sre-alerting-best-practices)).

### Alert fatigue / burn-rate
- Teams get ~2,000 alerts/week, ~3% actionable; target ≥30–50% conversion, delete <20% ([incident.io](https://incident.io/blog/sre-alerting-best-practices)).
- **Multi-window multi-burn-rate (MWMBR)** from Google SRE: fire only when both a long and short window exceed threshold; short window = 1/12 long for fast reset ([Google SRE Workbook](https://sre.google/workbook/alerting-on-slos/); [Grafana](https://grafana.com/blog/how-to-implement-multi-window-multi-burn-rate-alerts-with-grafana-cloud/)).
- **Alert on p95** (sufficient sample volume), p99 on dashboards; "p99 > 3× p50 for 15m" as a secondary ratio alert ([loadtester](https://loadtester.org/p95-vs-p99-latency); [Redis](https://redis.io/blog/p95-latency/)).
- Precision gates: >70% for informational, >90% for paging ([EdgeDelta](https://edgedelta.com/company/knowledge-center/anomaly-detection)).

### Retry storms
- Self-reinforcing amplification; signal = monotonically *accelerating* failures to a single dependency vs decaying transients. Retry budget (AIMD) + circuit breaker are complementary ([Azure retry-storm](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/retry-storm/); [retry strategies](https://dev.to/rajeshpandey/mastering-retry-strategies-in-distributed-systems-preventing-retry-storms-and-ensuring-resilience-12lo)).
- **LLM-specific amplification**: each retry appends context — window can grow 4K→128K by the 5th retry, a secondary cost blowout ([TrueFoundry](https://www.truefoundry.com/blog/rate-limiting-ai-agents-preventing-llm-api-exhaustion)).

### LLM-agent-specific failure modes
- **The $47K loop**: two agents ping-ponged LLM calls with no termination; HTTP 200, stable latency, no errors — green dashboard for 11 days, cost grew 144× ([$47K postmortem](https://dev.to/gabrielanhaia/the-agent-that-spent-47k-on-itself-an-autonomous-loop-postmortem-3313)). Minimum defenses: hard step cap (≈10), **per-conversation USD ceiling**, duplicate-input hash (abort on identical tool+args ≥2 in a window — AWS DebounceHook showed 7× call reduction, [AWS](https://dev.to/aws/how-to-prevent-ai-agent-reasoning-loops-from-wasting-tokens-2652)).
- Per-conversation (not per-call) monitoring is essential — per-call cost is stable while session cost compounds ([OpenObserve LLM cost](https://openobserve.ai/blog/llm-cost-monitoring/)). Adversarial tool-chains can drive 658× cost increases past prompt filters ([arXiv:2601.10955](https://arxiv.org/pdf/2601.10955)).
- Multi-agent signals: error compounding, context rot (>15% quality drop), coordination tokens >25%, >1.5× single-agent latency ([Redis multi-agent](https://redis.io/blog/why-multi-agent-llm-systems-fail/)).
- Semantic failures invisible to infra monitoring — detect via repeated identical error messages + token TTL ([n1n.ai](https://explore.n1n.ai/blog/prevent-runaway-ai-agent-costs-token-spirals-2026-05-25), single-source/directional).

### Cold-start / warm-up
- 2–4 weeks min for daily baselines; 30 days for weekly; shadow-mode before paging. **Validated our dormancy approach.** Refinements: emit raw measurements to dashboard during warm-up (visibility, no alerts); apply static floor bounds day-zero; 10-min post-deploy settling window to suppress deploy-noise (Shopify pattern) ([EdgeDelta](https://edgedelta.com/company/knowledge-center/anomaly-detection)).

### → Design deltas
1. **Detection-rule mechanism validated** per rule (statics for retry-storm/dead-agent/loop; rolling EWMA for spend; hybrid static-bound + MWMBR for latency).
2. **Add the missing critical rule: per-conversation cumulative cost accumulator** (group executions by `conversation_id`/correlation_id, sum `cost_usd`, alert at a configurable ceiling). This is the $47K failure mode and the highest-value addition.
3. **Add (v1, achievable at execute_safe seam)**: per-conversation cost ceiling; workflow TTL (alert if a conversation hasn't reached terminal state by T); per-agent tool-failure rate.
4. **Defer to phase 2 (needs tool-loop instrumentation deeper than execute_safe)**: duplicate-tool-call-input hash, context-growth-rate (quadratic) detection. Named explicitly so they aren't silently dropped.
5. **Ship concrete defaults**: retry storm ≥5 fails/60s; spend >3× EWMA(24h) alert, ≥10× = circuit-level recommendation; latency p95 vs static SLO + MWMBR(5m/1h); dead-agent on the 5-min scan; alert on p95, dashboard p99.
6. **Alerting hygiene**: severity tiers (page/ticket/trend), hysteresis (alert once per open condition), every alert carries a specific remediation recommendation (matches "alert+recommend"), 30-day actionability review, warm-up shadow routing until >70% precision.
7. **Cross-link**: monitor the Evaluator's score distribution for leniency drift (from §1).

---

## Methodology

4 parallel research agents, ~30 queries across web + academic sources (WebSearch/WebFetch; Hugging Face paper_search for arXiv). ~55 unique sources, prioritized 2024–2026, academic + official docs + reputable LLMOps vendors. Single-source claims flagged inline (notably: the 9-judge/2-effective-votes paper, the n1n.ai semantic-failure blog, and the precise Claude self-preference magnitude which is extrapolated from GPT-4 data). Sub-questions: judge biases & panel tradeoffs; scoring format & calibration; external-vs-intrinsic self-correction & iteration limits; OTel GenAI semconv & LLMOps metric vocabularies; statics-vs-statistical detection, burn-rate alerting, agent loop/cost failure modes, cold-start.

## Full source index
See inline citations above — grouped by section. Primary authorities: OpenTelemetry GenAI SemConv, Google SRE Workbook, arXiv (Self-Refine, Reflexion, CRITIC, Huang et al., PoLL, TICK), Langfuse/Arize/Traceloop/LangSmith docs, Eugene Yan, incident.io, EdgeDelta, TrueFoundry, Redis, the $47K-loop postmortem.
