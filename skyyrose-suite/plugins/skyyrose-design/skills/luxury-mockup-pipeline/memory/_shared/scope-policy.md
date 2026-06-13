---
name: scope-policy
description: Full-site scope + primary_focus_surfaces discipline for every agent dispatch
tags: [pipeline-protocol, scope]
applies_to: [ux-architect, ui-designer, brand-guardian, frontend-developer, senior-developer]
last_verified: 2026-05-25
---

# Scope Policy

Every agent's JSON brief enumerates the FULL site (header→body→every page/component/widget/layout→footer). `primary_focus_surfaces` declares which surface the current sprint targets. Both are mandatory.

**Why:** narrow scoping created silo blind spots — Brand Guardian missed canon drift on PDP because its scope was set to home-only. Founder caught it 2026-05-25.

**How to apply:** 
- Every JSON brief has full-scope coverage (every header field true, every footer field true, every enum array populated)
- Agent reads the full site context before producing deliverable
- Deliverable focuses on `primary_focus_surfaces` BUT includes a `Cross-surface implications` section noting ripples
- Even diagnostic agents (UX / UI / Brand / Frontend) audit the full site, focus deliverable on target

**Repo source:** `prompts/<agent>.json` field `scope._scope_policy` + `scope.scope_note`
