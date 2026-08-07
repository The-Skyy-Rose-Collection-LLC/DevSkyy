#!/usr/bin/env bash
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
expected_agents=(
  fashion-theme-lead
  brand-experience-architect
  fashion-design-system-engineer
  fashion-brand-systems-researcher
  fashion-token-foundations-engineer
  fashion-typography-layout-director
  fashion-component-commerce-engineer
  fashion-motion-responsive-engineer
  fashion-accessibility-content-engineer
  fashion-designops-governance-engineer
  fashion-visual-qa-red-team
  woocommerce-theme-engineer
  fashion-frontend-engineer
  catalog-sot-integrator
  accessibility-performance-reviewer
  visual-commerce-qa
  theme-release-engineer
  fashion-commerce-strategist
  fashion-merchandising-conversion-architect
  fashion-product-fit-returns-specialist
  ecommerce-growth-analytics-engineer
  fashion-knowledge-curator
)
expected_references=(
  acceptance-gates
  autonomy-protocol
  tool-budget-and-loading
  design-system-contract
  design-system-pod
  evidence-examples
  high-end-design-standard
  skyyrose-design-canon
  team-contract
  theme-deliverable-contract
  woocommerce-coverage
)

for agent_name in "${expected_agents[@]}"; do
  test -s "${plugin_root}/agents/${agent_name}.md" || {
    printf 'FAIL: missing agent charter: %s\n' "${agent_name}" >&2
    exit 1
  }
done

for reference_name in "${expected_references[@]}"; do
  test -s "${plugin_root}/skills/fashion-theme-team/references/${reference_name}.md" || {
    printf 'FAIL: missing team contract: %s\n' "${reference_name}" >&2
    exit 1
  }
done

test "$(find "${plugin_root}/agents" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')" -eq 22 || {
  printf 'FAIL: expected exactly twenty-two agent charters\n' >&2
  exit 1
}

brain_root="${plugin_root}/skills/fashion-theme-team/brain"
required_brain_files=(
  README.md
  taxonomy.json
  source-registry.json
  knowledge/fashion-commerce-fundamentals.md
  knowledge/merchandising-and-conversion.md
  knowledge/fit-imagery-and-returns.md
  knowledge/theme-engineering.md
  knowledge/do-dont.md
  pages/page-blueprints.md
  pages/page-blueprints.json
  prompts/prompt-stack.md
  prompts/few-shot-patterns.md
  prompts/evaluator-rubric.json
  schemas/handoff-contract.schema.json
  schemas/evidence.schema.json
  schemas/task-packet.schema.json
  examples/preview.html
  examples/contract.json
  examples/evidence.json
  research/fashion-commerce-research-2026-08-06.md
  brand/skyyrose-artifact-system.json
  brand/skyyrose-artifact.css
  brand/fonts/archivo-latin.woff2
  brand/fonts/hanken-grotesk-latin.woff2
  brand/fonts/anton-latin.woff2
  showcase/index.html
  showcase/v2-page-atlas.html
  showcase/brain-reader.html
  showcase/v2-page-plan.html
  showcase/motion-prompt-pack.html
  showcase/interactive-feature-scaffold.html
  showcase/v2-gap-closure.html
  references/animated-prompt-pack-adaptation.md
  references/animated-website-prompt-pack-200.pdf
  research/interactive-commerce-research-2026-08-06.md
  interactive/feature-scaffold.json
  v2/v2-page-and-imagery-plan.md
  v2/v2-page-plan.json
  v2/v2-page-plan.schema.json
  v2/commerce-state-contract.json
  v2/motion-responsive-contract.json
  v2/gap-closure-procedure.json
  v2/team-run-summary.md
  v2/team-run-contract-repair.md
  v2/team-run-design-system.md
  v2/team-run-commerce.md
  v2/team-run-motion.md
  v2/team-run-contract-repair.md
  v2/team-run-commerce-repair.md
  v2/team-run-motion-repair.md
  v2/team-run-release-loop.md
  visuals/skyyrose-brain-overview.png
  visuals/skyyrose-brain-overview-mobile.png
  visuals/skyyrose-v2-page-atlas.png
  visuals/skyyrose-handoff-preview.png
  visuals/skyyrose-brain-reader.png
  visuals/skyyrose-v2-page-plan-reader.png
  visuals/skyyrose-motion-prompt-pack.png
  visuals/skyyrose-interactive-feature-scaffold.png
  visuals/skyyrose-interactive-feature-scaffold-mobile.png
  visuals/skyyrose-v2-gap-closure.png
  visuals/skyyrose-v2-gap-closure-mobile.png
)

for brain_file in "${required_brain_files[@]}"; do
  test -s "${brain_root}/${brain_file}" || {
    printf 'FAIL: missing Fashion Theme Brain file: %s\n' "${brain_file}" >&2
    exit 1
  }
done

for json_file in \
  "${brain_root}/taxonomy.json" \
  "${brain_root}/source-registry.json" \
  "${brain_root}/pages/page-blueprints.json" \
  "${brain_root}/prompts/evaluator-rubric.json" \
  "${brain_root}/brand/skyyrose-artifact-system.json" \
  "${brain_root}/v2/v2-page-plan.json" \
  "${brain_root}/v2/v2-page-plan.schema.json" \
  "${brain_root}/v2/commerce-state-contract.json" \
  "${brain_root}/v2/motion-responsive-contract.json" \
  "${brain_root}/v2/gap-closure-procedure.json" \
  "${brain_root}/interactive/feature-scaffold.json" \
  "${brain_root}/schemas/handoff-contract.schema.json" \
  "${brain_root}/schemas/evidence.schema.json" \
  "${brain_root}/schemas/task-packet.schema.json"; do
  jq -e . "${json_file}" >/dev/null || {
    printf 'FAIL: invalid brain JSON: %s\n' "${json_file}" >&2
    exit 1
  }
done

jq -e . "${brain_root}/examples/contract.json" >/dev/null
jq -e . "${brain_root}/examples/evidence.json" >/dev/null

jq -e '.pages | length >= 26' "${brain_root}/pages/page-blueprints.json" >/dev/null
jq -e '.status == "planned-not-implemented" and .brand.id == "skyyrose" and (.pages | length) == 28' "${brain_root}/v2/v2-page-plan.json" >/dev/null
jq -e '.status == "scaffolded-not-implemented" and .brand.id == "skyyrose" and .feature_count == 22 and (.features | length) == 22' "${brain_root}/interactive/feature-scaffold.json" >/dev/null
jq -e '.procedure_id == "skyyrose-v2-gap-closure" and .status == "ready-to-run" and .brand.id == "skyyrose" and (.phases | length) == 8 and all(.phases[]; (.owner | length) > 2 and (.depends_on | type) == "array" and (.outputs | length) >= 2 and (.acceptance | length) >= 3 and (.evidence | length) >= 2 and (.stop_if | length) >= 1)' "${brain_root}/v2/gap-closure-procedure.json" >/dev/null
jq -e 'all(.features[]; (.id | length) > 2 and (.targets | length) >= 1 and (.acceptance | length) >= 2 and (.cta | length) > 2)' "${brain_root}/interactive/feature-scaffold.json" >/dev/null
jq -e '(.proof_contract.lifecycle | length) == 4 and (.proof_contract.required_evidence | length) >= 5 and (.proof_contract.ready_when | length) > 20' "${brain_root}/interactive/feature-scaffold.json" >/dev/null
jq -e '.commerce_state_contract == "../v2/commerce-state-contract.json" and (.proof_contract.required_evidence | all(.[]; length > 10)) and (.proof_contract.artifact_contract | has("source") and has("visual") and has("interaction") and has("commerce") and has("release"))' "${brain_root}/interactive/feature-scaffold.json" >/dev/null
jq -e '([.pages[].id] | length) == ([.pages[].id] | unique | length)' "${brain_root}/v2/v2-page-plan.json" >/dev/null
jq -e 'all(.pages[]; (.layout | length) >= 4 and (.features | length) >= 3 and (.imagery | length) >= 20 and (.desktop | length) >= 20 and (.mobile | length) >= 20)' "${brain_root}/v2/v2-page-plan.json" >/dev/null
jq -e '(.cta_by_page | length) == 28 and (.cta_system.primary | length) > 10 and (.motion_reference | length) > 1' "${brain_root}/v2/v2-page-plan.json" >/dev/null

# V2 contract/schema integrity. These checks validate the contract shape and
# fail closed; they do not claim that the planned theme is implemented.
v2_schema="${brain_root}/v2/v2-page-plan.schema.json"
v2_plan="${brain_root}/v2/v2-page-plan.json"
jq -e '
  (.required | type == "array") and
  (.required as $required | all(["status", "brand", "pages", "token_map", "collection_tokens", "imagery_manifest_contract", "state_matrix", "responsive_matrix", "cta_state_matrix", "motion_budget", "rhythm_rules"][]; . as $key | ($required | index($key)) != null)) and
  (.["$defs"].page.required as $required | all(["visual_identity", "provenance", "responsive", "states", "cta_state_matrix", "motion_budget", "rhythm", "acceptance"][]; . as $key | ($required | index($key)) != null))
' "${v2_schema}" >/dev/null || {
  printf 'FAIL: V2 page-plan schema is missing required contract fields\n' >&2
  exit 1
}
jq -e '
  .status == "planned-not-implemented" and .brand.id == "skyyrose" and (.pages | length) == 28 and
  (. as $plan | all(["token_map", "collection_tokens", "imagery_manifest_contract", "state_matrix", "responsive_matrix", "cta_state_matrix", "motion_budget", "rhythm_rules"][]; . as $key | ($plan | has($key)))) and
  ([.responsive_matrix.viewports[].id] | sort) == ["1440", "390", "768"] and
  ([.responsive_matrix.required_states[]] | sort) == ["empty", "error", "keyboard", "loading", "reduced_motion", "success", "unavailable"] and
  (all(.pages[]; . as $page | all(["visual_identity", "provenance", "responsive", "states", "cta_state_matrix", "motion_budget", "rhythm", "acceptance"][]; . as $key | ($page | has($key)))))
' "${v2_plan}" >/dev/null || {
  printf 'FAIL: V2 page plan does not satisfy its schema contract\n' >&2
  exit 1
}

# Commerce is the purchase/data boundary. Client projections never authorize
# purchase, and release readiness remains blocked until evidence exists.
jq -e '
  .contract_version == "2.0.0" and .status == "implementation-required" and .brand.id == "skyyrose" and
  (.owner | length) > 3 and (.enums.product_type | length) >= 6 and (.enums.availability_status | length) >= 8 and
  (.entities.product.required | index("id") != null) and (.entities.variation.required | index("id") != null) and
  (.component_contracts | has("product_card") and has("quick_view") and has("pdp_decision_zone") and has("product_grid_query")) and
  (.action_contract.request.required | index("request_id") != null) and (.action_contract.response.required | index("retryable") != null) and
  (.action_contract.server_truth | length) >= 4 and (.acceptance_matrix | length) >= 7 and
  (.release_gate.ready_when | length) >= 4 and (.release_gate.blocked_when | length) >= 5
' "${brain_root}/v2/commerce-state-contract.json" >/dev/null || {
  printf 'FAIL: commerce state contract is incomplete or not fail-closed\n' >&2
  exit 1
}

# Motion/responsive contract: assert all responsive breakpoints, budgets, and
# candidate-bound evidence classes. Missing runtime evidence remains
# UNVERIFIED/BLOCKED and is reported by the release loop, never inferred here.
jq -e '
  .contract_id == "skyyrose-v2-motion-responsive" and .version == "1.0.0" and
  .implementation_status == "planned-not-implemented" and .release_status == "BLOCKED" and
  (.behavior_matrix | length) == 9 and
  (all(.behavior_matrix[]; ([.responsive | keys[]] | sort) == ["1440", "390", "768"] and (.surface_id | length) > 2 and (.purpose | length) > 10)) and
  (.budgets.critical_css_gzip_kb_max <= 35) and (.budgets.route_owned_initial_js_gzip_kb_max <= 80) and
  (.budgets.initial_fonts_woff2_kb_max <= 150) and (.budgets.lcp_p75_ms_max["390"] <= 3000) and
  (.budgets.lcp_p75_ms_max["1440"] <= 2500) and (.budgets.cls_p75_max <= 0.1) and
  (.budgets.inp_p75_ms_max <= 200) and (.budgets.motion_fps_min >= 55) and (.budgets.touch_target_css_px_min >= 44) and
  ((.evidence_artifacts.required | map(.id) | sort) == ["browser-interaction-trace", "commerce-truth-log", "fallback-trace", "independent-review", "performance-trace", "reduced-motion-trace", "responsive-captures", "source-provenance"]) and
  (all(.evidence_artifacts.required[]; has("id") and has("format"))) and
  ([.evidence_artifacts.required[] | select(.id == "source-provenance") | .fields[]] | sort) == ["SKU_refs", "candidate_id", "feature_id", "page_id", "rights_record", "source_ref", "status", "variation_refs"] and
  ([.evidence_artifacts.required[] | select(.id == "responsive-captures") | .required_viewports[]] | sort) == ["1440x900", "390x844", "768x1024"] and
  ([.evidence_artifacts.required[] | select(.id == "browser-interaction-trace") | .must_cover[]] | sort) == ["CTA states", "Escape and focus restore", "cancellation", "drawer focus trap", "keyboard alternatives", "native scroll", "skip link", "touch targets"] and
  ([.evidence_artifacts.required[] | select(.id == "reduced-motion-trace") | .must_assert[]] | sort) == ["equal DOM order and CTA reachability", "no RAF or auto-rotate", "no WebGL initialization", "no autoplay audio", "no parallax"] and
  ([.evidence_artifacts.required[] | select(.id == "fallback-trace") | .must_cover[]] | sort) == ["GPU timeout", "context loss", "decode failure", "offline", "route abort", "unsupported"] and
  ([.evidence_artifacts.required[] | select(.id == "commerce-truth-log") | .fields[]] | sort) == ["CTA event", "SKU", "availability", "error or unavailable recovery", "idempotency", "price", "request state", "variation"] and
  (any(.evidence_artifacts.required[]; .id == "independent-review" and .self_approval_forbidden == true and (.reviewers | length) >= 4))
' "${brain_root}/v2/motion-responsive-contract.json" >/dev/null || {
  printf 'FAIL: motion/responsive contract is incomplete or not fail-closed\n' >&2
  exit 1
}

# Candidate proof contract: every feature must have stable identity, fallback,
# CTA, acceptance data, and the required evidence classes. A planning fixture is
# never treated as runtime proof.
jq -e '
  (.proof_contract.lifecycle == ["scaffolded", "built", "verified", "release-ready"]) and
  (. as $root | all(["source-citation or explicit brand/catalog authority", "desktop and mobile rendered capture", "keyboard and screen-reader interaction result", "reduced-motion and fallback result", "performance budget result", "commerce-truth result for product, price, inventory, and CTA state"][]; . as $needle | ($root.proof_contract.required_evidence | index($needle)) != null)) and
  (all(.features[]; (.id | length) > 2 and (.fallback | length) > 3 and (.cta | length) > 3 and (.acceptance | length) >= 2))
' "${brain_root}/interactive/feature-scaffold.json" >/dev/null || {
  printf 'FAIL: candidate proof contract is incomplete\n' >&2
  exit 1
}

# Founder-locked language guard. Run only against executable V2 contracts and
# readers; audit reports may mention rejected language while documenting why it
# is blocked.
for forbidden_pattern in 'count.?down|timer|remaining[[:space:]-]+time' 'cross[- ]?sell|complete[[:space:]-]+the[[:space:]-]+look|related[[:space:]-]+products|wears[[:space:]-]+with'; do
  if rg -ni "${forbidden_pattern}" \
    "${brain_root}/v2/v2-page-plan.json" \
    "${brain_root}/v2/v2-page-and-imagery-plan.md" \
    "${brain_root}/showcase/v2-page-plan.html" \
    "${brain_root}/showcase/v2-page-atlas.html" >/dev/null; then
    printf 'FAIL: forbidden V2 urgency/recommendation language found: %s\n' "${forbidden_pattern}" >&2
    exit 1
  fi
done
test "$(jq -r '.pages[].id' "${brain_root}/pages/page-blueprints.json" | sort)" = "$(jq -r '.pages[].id' "${brain_root}/v2/v2-page-plan.json" | sort)" || {
  printf 'FAIL: V2 plan and page-blueprint inventories differ\n' >&2
  exit 1
}
jq -e '.sources | length >= 15' "${brain_root}/source-registry.json" >/dev/null
jq -e '([.sources[].id] | length) == ([.sources[].id] | unique | length)' "${brain_root}/source-registry.json" >/dev/null
jq -e '([.sources[].url] | length) == ([.sources[].url] | unique | length)' "${brain_root}/source-registry.json" >/dev/null
jq -e 'any(.sources[]; .id == "USER-ANIMATED-PROMPT-PACK-200" and .sha256 == "0bd6f682245bc603e74d6fdcc4341625e7a3c73fdb502e7dcaa7c338da0261f8")' "${brain_root}/source-registry.json" >/dev/null
jq -e 'any(.sources[]; .id == "GOOGLE-AI-SHOPPING-2025")' "${brain_root}/source-registry.json" >/dev/null
jq -e '.routes | length >= 8' "${brain_root}/taxonomy.json" >/dev/null
jq -e '.pass_threshold >= 80 and ([.dimensions[].weight] | add) == 100 and (.hard_fails | length) >= 8' "${brain_root}/prompts/evaluator-rubric.json" >/dev/null

while IFS= read -r pack_path; do
  test -s "${brain_root}/${pack_path}" || {
    printf 'FAIL: taxonomy references missing pack: %s\n' "${pack_path}" >&2
    exit 1
  }
done < <(jq -r '.routes[].packs[]' "${brain_root}/taxonomy.json" | sort -u)

for html_term in '<!doctype html>' 'data-section-id=' 'Desktop' 'Mobile' 'Required states'; do
  rg -i "${html_term}" "${brain_root}/examples/preview.html" >/dev/null || {
    printf 'FAIL: visual handoff fixture missing term: %s\n' "${html_term}" >&2
    exit 1
  }
done

while IFS= read -r section_id; do
  rg -F "data-section-id=\"${section_id}\"" "${brain_root}/examples/preview.html" >/dev/null || {
    printf 'FAIL: contract section is absent from HTML preview: %s\n' "${section_id}" >&2
    exit 1
  }
done < <(jq -r '.routes[].sections[].id' "${brain_root}/examples/contract.json" | sort -u)

while IFS= read -r section_id; do
  jq -e --arg section_id "${section_id}" '[.routes[].sections[].id] | index($section_id) != null' \
    "${brain_root}/examples/contract.json" >/dev/null || {
    printf 'FAIL: HTML section is absent from JSON contract: %s\n' "${section_id}" >&2
    exit 1
  }
done < <(rg -o 'data-section-id="[^"]+"' "${brain_root}/examples/preview.html" | sed -E 's/.*="([^"]+)"/\1/' | sort -u)

for branded_json in \
  "${brain_root}/taxonomy.json" \
  "${brain_root}/source-registry.json" \
  "${brain_root}/pages/page-blueprints.json" \
  "${brain_root}/prompts/evaluator-rubric.json" \
  "${brain_root}/v2/v2-page-plan.json" \
  "${brain_root}/v2/v2-page-plan.schema.json" \
  "${brain_root}/v2/commerce-state-contract.json" \
  "${brain_root}/v2/motion-responsive-contract.json" \
  "${brain_root}/v2/gap-closure-procedure.json" \
  "${brain_root}/interactive/feature-scaffold.json" \
  "${brain_root}/examples/contract.json" \
  "${brain_root}/examples/evidence.json"; do
  rg -i -F 'skyyrose' "${branded_json}" >/dev/null || {
    printf 'FAIL: unbranded JSON artifact: %s\n' "${branded_json}" >&2
    exit 1
  }
done

for branded_html in \
  "${brain_root}/showcase/index.html" \
  "${brain_root}/showcase/v2-page-atlas.html" \
  "${brain_root}/showcase/brain-reader.html" \
  "${brain_root}/showcase/v2-page-plan.html" \
  "${brain_root}/showcase/motion-prompt-pack.html" \
  "${brain_root}/showcase/interactive-feature-scaffold.html" \
  "${brain_root}/showcase/v2-gap-closure.html" \
  "${brain_root}/examples/preview.html"; do
  rg -F 'SkyyRose' "${branded_html}" >/dev/null || {
    printf 'FAIL: unbranded HTML artifact: %s\n' "${branded_html}" >&2
    exit 1
  }
done

test "$(rg -o 'const ctaByIndex' "${brain_root}/showcase/v2-page-plan.html" | wc -l | tr -d ' ')" -eq 1 || {
  printf 'FAIL: V2 HTML reader is missing its per-page CTA matrix\n' >&2
  exit 1
}
test "$(rg -o '\[\"[a-z0-9-]+\",\"[^\"]+\",\"(build_now|pilot|future|reject)\"' "${brain_root}/showcase/interactive-feature-scaffold.html" | wc -l | tr -d ' ')" -eq 22 || {
  printf 'FAIL: interactive feature scaffold must render twenty-two records\n' >&2
  exit 1
}
test "$(rg -o 'data-feature-id=' "${brain_root}/showcase/interactive-feature-scaffold.html" | wc -l | tr -d ' ')" -eq 1 || {
  printf 'FAIL: interactive feature scaffold must render stable feature IDs\n' >&2
  exit 1
}
test "$(shasum -a 256 "${brain_root}/references/animated-website-prompt-pack-200.pdf" | awk '{print $1}')" = "0bd6f682245bc603e74d6fdcc4341625e7a3c73fdb502e7dcaa7c338da0261f8" || {
  printf 'FAIL: saved motion prompt pack checksum changed\n' >&2
  exit 1
}

test "$(rg -o '\[\"[a-z0-9-]+\",\"[^\"]+\",\"(core|experience|extension)\"' "${brain_root}/showcase/v2-page-atlas.html" | wc -l | tr -d ' ')" -eq 28 || {
  printf 'FAIL: V2 visual atlas must render twenty-eight page records\n' >&2
  exit 1
}

if rg -n 'gradient-text|background-clip:[[:space:]]*text|backdrop-filter|cursor:[[:space:]]*none' \
  "${brain_root}/brand/skyyrose-artifact.css" \
  "${brain_root}/showcase" \
  "${brain_root}/examples/preview.html" >/dev/null; then
  printf 'FAIL: forbidden generic visual device found in SkyyRose artifact system\n' >&2
  exit 1
fi

research_report="${brain_root}/research/fashion-commerce-research-2026-08-06.md"
host_count="$(rg -o 'https?://[^/ )]+' "${research_report}" | sort -u | wc -l | tr -d ' ')"
inline_count="$(rg -c '\]\(https?://' "${research_report}")"
source_count="$(awk '/^## Sources/,/^## Methodology/' "${research_report}" | rg -c '^[0-9]+\.')"
test "${host_count}" -ge 5 || { printf 'FAIL: research uses fewer than five hosts\n' >&2; exit 1; }
test "${inline_count}" -ge 10 || { printf 'FAIL: research has fewer than ten inline citations\n' >&2; exit 1; }
test "${source_count}" -ge 15 || { printf 'FAIL: research has fewer than fifteen sources\n' >&2; exit 1; }

jq -e '.name == "fashion-theme-team"' "${plugin_root}/.codex-plugin/plugin.json" >/dev/null
jq -e '.hooks.SessionStart | length > 0' "${plugin_root}/hooks/hooks.json" >/dev/null
bash -n "${plugin_root}/hooks/session-start.sh"
bash -n "${plugin_root}/scripts/preflight.sh"
bash -n "${plugin_root}/scripts/report.sh"
bash -n "${plugin_root}/scripts/verify.sh"
python3 -m py_compile \
  "${plugin_root}/runtime/elite_web_builder/run.py" \
  "${plugin_root}/runtime/elite_web_builder/core/verification_loop.py"

test -s "${plugin_root}/runtime/elite_web_builder/INTEGRATION.md" || {
  printf 'FAIL: missing elite runtime integration overlay\n' >&2
  exit 1
}

test -s "${plugin_root}/skills/elite-builder-runtime/SKILL.md" || {
  printf 'FAIL: missing lazy elite runtime skill\n' >&2
  exit 1
}

if test -e "${plugin_root}/runtime/elite_web_builder/.coverage" || \
   test -e "${plugin_root}/runtime/elite_web_builder/output/last_report.json"; then
  printf 'FAIL: stale runtime output was packaged\n' >&2
  exit 1
fi

if rg -n 'DEFAULT_PRD|load_dotenv|PASSED or SKIPPED' \
  "${plugin_root}/runtime/elite_web_builder/run.py" \
  "${plugin_root}/runtime/elite_web_builder/core/verification_loop.py" >/dev/null; then
  printf 'FAIL: unsafe runtime default remains\n' >&2
  exit 1
fi

for required_term in 'PENDING.*READY.*ACTIVE' 'four active' 'candidate ID' 'tool budget' 'SkyyRose' 'garment is the protagonist' 'eyes-on' 'authoritative primary' 'Fashion Theme Brain' 'preview.html' 'contract.json' 'EXPERIMENT'; do
  rg -i "${required_term}" "${plugin_root}/skills/fashion-theme-team" >/dev/null || {
    printf 'FAIL: missing motherbase contract term: %s\n' "${required_term}" >&2
    exit 1
  }
done

marker_pattern='\[TO''DO:|FIX''ME|PLACE''HOLDER'
if rg -n "${marker_pattern}" "${plugin_root}" --glob '*.md' --glob '*.json' --glob '*.yaml' --glob '*.sh' >/dev/null; then
  printf 'FAIL: unresolved placeholder marker found\n' >&2
  exit 1
fi

printf 'PASS: fashion-theme-team motherbase integrity\n'
