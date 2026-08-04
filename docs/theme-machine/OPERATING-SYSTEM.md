# SkyyRose Theme Building Machine

This is the operating system for building premium, interactive WooCommerce themes without sacrificing catalog integrity, editor usability, accessibility, or release safety. Its machine-readable authority is [manifest.json](manifest.json).

The core pair is mandatory: `fashion-theme-architect` is the primary end-to-end builder; `skyyrose-wp-platform` is the platform doctrine it follows. The remaining lanes are specialists, not competing owners of the same files.

## Intake

Every request must name the target `theme_path`, the customer-facing surface or outcome, and the commerce authority. For this repository, WooCommerce is authoritative for catalog, cart, tax, shipping, order, and payment state. Stripe is the payment gateway; it is not a parallel order system.

Before implementation, the primary builder produces a short design and delivery note covering the chosen theme, surface boundaries, source files, generated assets, SOT dependencies, browser journeys, and release gates. A substantial scope change pauses for user approval.

## The 13 lanes

| Lane | Primary | Paired capability | Clear outcome |
| --- | --- | --- | --- |
| 1. End-to-end build | `fashion-theme-architect` | `skyyrose-wp-platform` | A complete theme surface and build report. |
| 2. Platform doctrine | `skyyrose-wp-platform` | `devskyy-patterns`, `coding-standards` | The correct SkyyRose constraints and SOT contract. |
| 3. Luxury direction | `luxury-design-taste` | `design-system`, `frontend-design-direction` | A restrained, intentional high-fashion visual contract. |
| 4. Storefront composition | `wp-frontend` | `frontend-patterns`, `css-responsive`, `motion-ui` | Responsive, progressively enhanced shopping surfaces. |
| 5. Immersive storytelling | `wp-immersive` | `immersive-interactive-architect`, `3d-rigging-pipeline` | Interactive scenes with non-WebGL and reduced-motion fallbacks. |
| 6. Elementor authoring | `wp-elementor` | `frontend-patterns`, `accessibility` | Safe, editable custom widgets. |
| 7. Commerce and checkout | `wp-woocommerce` | `wordpress-woocommerce-automation`, `checkout-optimizer` | Correct WooCommerce-first product and checkout flows. |
| 8. Catalog integrity | `wp-catalog-sync` | `skyyrose-wp-platform` | Product, SKU, and verified-media SOT alignment. |
| 9. Accessibility | `accessibility` | `frontend-a11y`, `css-a11y` | Keyboard, semantic, contrast, and motion acceptance evidence. |
| 10. E2E and visual QA | `e2e-runner` | `e2e-testing`, `design-qc` | Browser journey results and screenshots. |
| 11. Security review | `security-reviewer` | `security-review`, `adversarial-verification` | A severity-ranked review of theme and commerce risks. |
| 12. Review and simplify | `code-reviewer` | `wp-code-simplifier`, `coding-standards` | Simpler, maintainable code with independent findings resolved. |
| 13. Release and recovery | `deploy-and-verify` | `theme-heal-doctor`, `adversarial-planning` | Post-approval release proof or an evidence-backed recovery. |

## Execution model

1. The core pair validates scope and asks for approval only when a significant new product, design, payment, deployment, or paid-media decision is required.
2. Luxury direction makes the visual contract concrete before surface build work. Storefront, immersive, Elementor, commerce, and catalog lanes work only within distinct ownership boundaries.
3. Accessibility, E2E/visual QA, security, and independent review all run after integration. Their evidence is a release input, not optional polish.
4. The release lane runs only with explicit production approval. `theme-heal-doctor` is an incident responder, never a substitute for pre-release verification.

Each lane that modifies code receives its own Git worktree and branch. Shared artifacts are handed off by commit, patch, or an explicit reviewed file list; no lane writes another lane's worktree. `fashion-theme-architect` is deliberately non-deploying and non-committing, so its candidate worktree is handed to the integration/release owner for that action.

## Non-negotiable quality gates

- Update source assets first; rebuild and commit corresponding `.min.css` and `.min.js` outputs.
- Use verified SOT catalog and media data only. Do not synthesize product records or trust filenames as image proof.
- Treat a skipped browser, performance, security, or release check as incomplete—not green.
- Keep WooCommerce authoritative and test cart through checkout against a non-production environment.
- Require output escaping, input sanitization, nonces and authorization checks where WordPress actions demand them.
- Test keyboard navigation, focus state, reduced motion, and the non-WebGL fallback for every interactive experience.
- Run the relevant focused checks, then the theme's full verification gate. Independent review and simplification are release prerequisites.

## Using the system

Route an implementation request to `theme-building-machine` with the target theme and desired outcome. It reads the manifest, activates the core pair, assigns only relevant lanes, creates isolated worktrees, and collects gate evidence. It should never activate all thirteen lanes merely for ceremony: a static product-card fix may need lanes 1, 2, 4, 8, 9, 10, and 12, while an immersive launch surface also needs lanes 3, 5, and 11.

The manifest is deliberately explicit so the system can be audited, extended, and validated without relying on chat history.
