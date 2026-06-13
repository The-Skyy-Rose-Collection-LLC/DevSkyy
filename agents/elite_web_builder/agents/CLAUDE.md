# agents/elite_web_builder/agents/ — Elite Web Builder specialist agents

14 specialist agents (13 + base) that the `Director` assigns stories to. Each file exports a single `*_SPEC = AgentSpec(...)` constant — no class instantiation. The Director imports all specs and assigns each story to the appropriate role via `ModelRouter`.

## Key files

- `base.py` — `AgentRole(Enum)` with 14 values: DIRECTOR, DESIGN_SYSTEM, FRONTEND_DEV, BACKEND_DEV, ACCESSIBILITY, PERFORMANCE, SEO_CONTENT, QA, IMAGERY, SOCIAL_MEDIA, THEME_BUILDER, ECOMMERCE_PHOTOGRAPHY, GARMENT_3D, COMPETITOR_SCOUT. Also defines `AgentSpec(role, name, system_prompt, capabilities)` and `AgentCapability(name, description, tags)`.
- `frontend_dev.py` — `FRONTEND_DEV_SPEC`: semantic HTML5, responsive CSS (Grid/Flexbox/Container Queries), WordPress block patterns, GSAP animations, React/Vue components. Model: `claude-sonnet-4-6`. CSS must use design system custom properties — never hardcoded values. All assets via `wp_enqueue_script/style`.
- `backend_dev.py` — `BACKEND_DEV_SPEC`: PHP templates, REST APIs, database queries (via `$wpdb->prepare()`), server config.
- `design_system.py` — `DESIGN_SYSTEM_SPEC`: design token generation, color palettes, typography scales, spacing grids.
- `accessibility.py` — `ACCESSIBILITY_SPEC`: WCAG 2.2 AA audits, ARIA, keyboard navigation, contrast validation.
- `performance.py` — `PERFORMANCE_SPEC`: Lighthouse audits, lazy loading, caching strategy, bundle optimization.
- `seo_content.py` — `SEO_CONTENT_SPEC`: meta tags, schema.org, og tags, heading hierarchy, keyword integration.
- `qa.py` — `QA_SPEC`: cross-browser regression, screenshot diff, functional test generation.
- `imagery.py` — `IMAGERY_SPEC`: image asset briefs, alt text, responsive srcset recommendations. Routes to `agents/core/imagery/` for actual generation.
- `social_media.py` — `SOCIAL_MEDIA_SPEC`: OG/Twitter card assets, social-optimized crop specs.
- `theme_builder.py` — `THEME_BUILDER_SPEC`: `theme.json`, block editor config, template hierarchy.
- `ecommerce_photography.py` — `ECOMMERCE_PHOTOGRAPHY_SPEC`: product shot art direction, ghost-mannequin briefs.
- `garment_3d.py` — `GARMENT_3D_SPEC`: 3D model briefs for Tripo/Meshy, texture mapping guidance.
- `competitor_scout.py` — `COMPETITOR_SCOUT_SPEC`: competitive analysis, positioning, SWOT.

## Conventions

- Every file exports exactly one `*_SPEC = AgentSpec(...)` constant — do not define classes or functions here.
- The `AgentRole` value in `base.py` must match the `role` field in each `AgentSpec` — adding a new specialist requires a new `AgentRole` entry AND a new spec file.
- Agents produce structured outputs (code, config, analysis) — they do NOT make LLM calls themselves. API calls go through `core/provider_adapters.py` + `ModelRouter`.
- `frontend_dev.py` enforces two hard rules in its system prompt: (1) CSS uses `var(--*)` only, never hardcoded hex; (2) no `@import` in CSS (use enqueue dependencies). Both are maintained in the system prompt verbatim.

## Don't

- Don't add LLM API call code to specialist agent files — all calls go through `core/provider_adapters.py`.
- Don't add new roles to `AgentRole` without adding a corresponding spec file and registering the spec in `director.py`.
- Don't route FASHN or Tripo API calls through `imagery.py` directly — `imagery.py` writes briefs; actual generation routes through `agents/core/imagery/`.

## Related

- `agents/elite_web_builder/director.py` — imports all `*_SPEC` objects and assigns stories
- `agents/elite_web_builder/core/model_router.py` — selects provider per `AgentRole`
- `agents/elite_web_builder/core/provider_adapters.py` — executes the actual LLM call
- `agents/elite_web_builder/core/verification_loop.py` — validates agent outputs before story is marked complete
