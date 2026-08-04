# SkyyRose Theme Building Machine

This is the operating system for building premium, interactive WooCommerce themes without sacrificing catalog integrity, editor usability, accessibility, marketplace policy, or release safety. Its machine-readable authority is [manifest.json](manifest.json); this document explains how to apply that contract.

The core pair is mandatory: `fashion-theme-architect` is the primary end-to-end builder and `skyyrose-wp-platform` supplies platform doctrine. The remaining lanes are specialists, not competing owners of the same files.

## Authority and truthful status

The machine can recommend, implement, test, and assemble evidence. The user/founder retains final authority over creative, brand, commerce, asset-licensing, release, and material product decisions. A reviewer, agent, passing scan, or completed build cannot approve on the founder's behalf.

Do not report a candidate as “marketplace approved,” “certified,” “accepted,” “guaranteed,” or “deployed.” A candidate can become **eligible for founder evidence review** only when:

1. every gate required by each selected release profile passes;
2. the evidence bundle passes `node scripts/validate-theme-machine.mjs --report <report.json>`;
3. authoritative marketplace requirements were reviewed within the manifest's freshness window and bound by official-page snapshot digests.

That first `evidence-review` phase contains no approvals. After the founder reviews the evidence, a `release-authorized` report must bind all six explicit approvals to the exact manifest digest, full source commit, package digest, profiles, complete evidence root, issue time, and expiry using a configured founder-controlled Ed25519 key. The repository intentionally ships with no founder public key, so release authorization fails closed until the founder configures one. Marketplace submission and production deployment remain separate explicit actions after authorization.

The build and policy trust roots are also intentionally empty. A candidate report cannot pass until a separately controlled CI/build attestor signs commit-to-ZIP reproducibility and safe package inspection. Marketplace profiles additionally require a separately controlled policy collector to sign official-source snapshots and canonical coverage. Candidate-authored provenance or a locally edited review date is never accepted as independent proof.

Anything skipped, missing, stale, placeholder-only, not run, or unverified is `blocked`, not green. `not_applicable` needs a written rationale and founder approval and cannot satisfy a profile-required gate.

## Intake

Every request must name:

- the target `theme_path` and customer-facing surface or outcome;
- the commerce authority;
- the target release profiles (`internal-production`, `wordpress-org`, and/or `themeforest`);
- the distribution and licensing model; and
- the intended WordPress, PHP, WooCommerce, browser, device, editor, locale/RTL, multisite, and relevant plugin compatibility.

For this repository, WooCommerce is authoritative for catalog, cart, tax, shipping, order, refund, and payment state. Stripe is a payment gateway, not a parallel order system.

Before implementation, the primary builder produces a design and delivery note covering the chosen theme, file boundaries, generated assets, SOT dependencies, target profiles, compatibility claims, browser journeys, risk budgets, approval points, and release gates. A substantial scope or material product change pauses for founder direction.

## The 13 lanes

| Lane | Primary | Paired capability | Clear outcome |
| --- | --- | --- | --- |
| 1. End-to-end build | `fashion-theme-architect` | `skyyrose-wp-platform` | A complete theme surface and build report. |
| 2. Platform doctrine | `skyyrose-wp-platform` | `devskyy-patterns`, `coding-standards` | Platform, SOT, distribution, and current marketplace contracts. |
| 3. Luxury direction | `luxury-design-taste` | `design-system`, `frontend-design-direction` | A founder-reviewed high-fashion visual contract. |
| 4. Storefront composition | `wp-frontend` | `frontend-patterns`, `css-responsive`, `motion-ui` | Responsive, progressively enhanced shopping surfaces. |
| 5. Immersive storytelling | `wp-immersive` | `immersive-interactive-architect`, `3d-rigging-pipeline` | Scroll worlds with tested degraded-mode equivalents. |
| 6. Elementor authoring | `wp-elementor` | `frontend-patterns`, `accessibility` | Safe, editable custom widgets. |
| 7. Commerce and checkout | `wp-woocommerce` | `wordpress-woocommerce-automation`, `checkout-optimizer` | Correct WooCommerce-first product and checkout flows. |
| 8. Catalog integrity | `wp-catalog-sync` | `skyyrose-wp-platform` | Product, SKU, verified media, and media provenance alignment. |
| 9. Accessibility | `accessibility` | `frontend-a11y`, `css-a11y` | Automated and manual inclusive-interface evidence. |
| 10. E2E and visual QA | `e2e-runner` | `e2e-testing`, `design-qc` | Browser journeys, compatibility matrix, screenshots, and measurements. |
| 11. Security and privacy | `security-reviewer` | `security-review`, `adversarial-verification` | Severity-ranked security, privacy, and dependency findings. |
| 12. Review and simplify | `code-reviewer` | `wp-code-simplifier`, `coding-standards` | Simpler maintainable code and a reviewed SBOM. |
| 13. Release and recovery | `deploy-and-verify` | `theme-heal-doctor`, `adversarial-planning` | Reproducible candidate, complete handoff, and approval-gated release or recovery. |

## Execution model

1. The core pair validates the intake, target profiles, founder approval points, and ownership map.
2. Platform doctrine refreshes the selected marketplace references before making compliance decisions. WordPress.org and ThemeForest are separate profiles; evidence from one never proves the other.
3. Luxury direction creates a concrete contract before surface work. Storefront, immersive, Elementor, commerce, and catalog lanes stay inside distinct file boundaries.
4. Accessibility, performance, E2E/visual QA, security/privacy, SBOM review, and independent review run after integration. Their artifacts are release inputs, not optional polish.
5. Release assembles a clean candidate twice, proves identical archives, validates an approval-free evidence-review report, and asks for founder review. Only afterward may it validate a candidate-bound, expiring founder signature for release handoff. Deployment or marketplace submission remains a separate explicitly approved action.

Each modifying lane receives its own Git worktree and branch. Shared artifacts are handed off by commit, patch, or an explicit reviewed file list; no lane writes another lane's worktree. `fashion-theme-architect` is deliberately non-deploying and non-committing, so its candidate worktree is handed to the integration/release owner.

## Marketplace profiles

Marketplace policies change. The manifest records official sources and a maximum age; the platform lane must refresh them before release review and update the manifest if policy changed. The policy artifact records each canonical URL, retrieval time, page-content SHA-256, covered requirement IDs, tool results, and human reviewer. An editable manifest date alone is not evidence.

### WordPress.org

The candidate policy audit must cover the current [required review rules](https://make.wordpress.org/themes/handbook/review/required/) and [release process](https://developer.wordpress.org/themes/releasing-your-theme/). At minimum it retains Theme Check output, required file/header checks, GPL-compatible licensing for code and assets, source files for minified assets, internationalization, theme-territory analysis, privacy/remote-resource behavior, and WordPress Theme Unit Test evidence.

WordPress.org forbids several behaviors that a commercial marketplace may allow. The profile must prove that theme onboarding does not provide prohibited demo imports, tracking/affiliate behavior, silent plugin installation, or external calls. Plugin functionality must be removed or placed in a separately compliant plugin; it cannot be waived by documentation.

### ThemeForest

The candidate audit starts at Envato's current [WordPress requirements hub](https://help.author.envato.com/hc/en-us/articles/360000472383-WordPress-Theme-Requirements-Start-here) and covers all linked parts, not only the sampled sources stored in the manifest. It retains Envato Theme Check output with zero `REQUIRED` notices, WordPress Theme Unit Test results, out-of-box behavior before plugin activation, public documentation, update compatibility, data privacy, security, plugin boundaries, Gutenberg, asset redistribution rights, and any advertised demo-import evidence.

The founder chooses the ThemeForest licensing option and approves the complete code/asset ledger. A preview-only asset still needs appropriate commercial rights, and a bundled asset needs redistribution rights.

## Per-collection narrative worlds

Every collection must feel like its own authored world. Before implementation, luxury direction produces a founder-approved contract that links the collection identity SOT to its world/scene, visual register, motion grammar, approved imagery allowlist, story beats, commerce bridge, mobile/reduced-motion/no-JavaScript/non-WebGL equivalents, and visual-drift references. An accent-color, font, texture, or background swap on a shared composition is not a new world.

QA compares each rendered surface and fallback to its own contract and checks for cross-collection leakage of assets, product imagery, copy, motifs, interaction language, and scene composition. Shared brand primitives must be named explicitly; everything else is collection-scoped.

- **Black Rose — beauty and depth:** Reveal black as material, silhouette, reflection, and contrast through the Black Rose. Silver is supporting light only. Reject generic goth, grief/mourning, and black-as-absence or emptiness cliches.
- **Love Hurts — the Beast's perspective:** Use the Beauty-and-the-Beast archetype only as thematic inspiration for an original story of isolation, devotion, transformation, and earned tenderness. Do not use Disney names, characters or likenesses, exact plot beats, imagery or recognizable motifs, music or sound-alikes, quotes or paraphrases, marks, or trade dress. Setting, characters, scenes, copy, assets, sound, and commerce transitions must be original. Material similarity risks require qualified human legal/IP review and founder approval; an agent cannot grant clearance.
- **Kids Capsule — heir to the throne:** Express the future inheriting the world through playful sovereignty, protection, and possibility. Design the visual register, copy, pacing, controls, and commerce bridge for children and caregivers. Do not ship a miniature adult or dark-gothic reskin, adult-coded sensuality, manipulative pressure, cross-collection leakage, child profiling, behavioral advertising, or personal-data collection without documented lawful age-appropriate caregiver consent and founder approval.
- **Signature — Flagship house standard:** Make Signature the clearest expression of the house through Oakland confidence, craft, and forward motion. Preserve its city-tour world and gold visual register. It establishes visual and system standards without becoming a neutral default template or a collage of Black Rose, Love Hurts, or Kids Capsule worlds.

## Evidence gates

The manifest defines the canonical criteria, owners, and required artifacts. These are the operational expectations behind them:

- **Licensing and attribution:** Inventory code, fonts, images, icons, video, audio, 3D, scripts, libraries, demo content, and preview assets. Record source, author, exact version, license, attribution, modifications, and redistribution rights. Exclude anything unverifiable.
- **Legal/IP clearance:** Inventory names, narrative, copy, characters, imagery, motifs, music, video, 3D, metadata, and trade dress. Remediate source-confusion and derivative-work risk, retain original-work or license provenance, and obtain qualified human review for material risks plus founder approval.
- **Collection narrative worlds:** Retain one approved contract per collection and visual-drift/leakage evidence for desktop, mobile, and degraded modes. Shared geometry with superficial restyling fails.
- **Privacy:** Map remote calls, local storage, cookies, telemetry, purchase verification, fonts/embeds, personal data, consent, retention, and opt-out. No required consent means no transmission.
- **Accessibility:** Combine automated scanning with manual keyboard, focus, reflow/zoom, contrast, screen-reader smoke, errors, reduced-motion, and commerce tests. A marketplace `accessibility-ready` label requires its own current checklist.
- **Performance:** Declare budgets before measuring. Retain cold/warm mobile and desktop runs for normal storefront and immersive surfaces; tool failures are blockers.
- **Security:** Retain secret, malware, dependency, static-analysis, and WordPress-specific review. Validate/sanitize input, escape output/translations, authorize and nonce state changes, and use WordPress database APIs.
- **Updates and child themes:** Document versioning, migrations, rollback, backup, support window, hooks/template deprecation, update verification, and customization preservation. Test clean install, upgrade, rollback, and child-theme activation.
- **Demo and onboarding:** Test a clean-site journey with prerequisites, required/optional plugins, timeouts, retries, reset, support, and non-destructive consent. Imports must not smuggle production/customer or non-redistributable data.
- **SBOM and dependencies:** Produce CycloneDX JSON for production and build components, including bundled libraries, fonts, and binaries. Record versions, licenses, hashes, origin, vulnerabilities, and lockfile state.
- **Reproducible package:** From one clean commit and locked toolchain, run one documented command twice. The installable ZIP and its SHA-256 must match byte for byte. Inspect archive root and exclusions, and ensure version metadata agrees.
- **Compatibility:** Record exact platform/client versions, date, environment, status, and evidence. Advertised compatibility is a subset of passing rows, never a guess or broad range inferred from one version.
- **Handoff:** Provide the archive, checksums, SBOM, licenses, source/build instructions, public/customer docs, demo material, test reports, compatibility, changelog, rollback, known issues, and support/escalation ownership.

### Website video delivery

The video artifact begins with a complete inventory; an explicit empty inventory passes when the candidate has no delivery video. Website-delivery video derivatives must have audio tracks removed from the media container, not merely muted with player attributes or zero-volume encoding. Preserve source masters outside the repository. For every delivered video, the handoff must record the source and derivative SHA-256, transformation command/toolchain, licensing link, and an `ffprobe` result showing zero audio streams. A file with any audio stream is blocked from packaging even if that stream is silent.

### Scroll-world fallback acceptance

The interaction artifact starts with a complete scroll-world/immersive inventory; an explicit empty inventory passes when the candidate has no such surface. An inventoried immersive surface is incomplete until all of these modes are eyes-on and interaction-tested:

- JavaScript unavailable;
- `prefers-reduced-motion: reduce`;
- WebGL unavailable and WebGL context loss after startup;
- low-memory/low-power behavior and failed asset loading;
- keyboard, touch, mouse, and narrow viewports.

The fallback must preserve essential story information in document order, keyboard focus, navigation, product links, prices, variants, and add-to-cart. It must not trap scrolling, hide commerce behind canvas, or require animation to complete a task. Users must be able to pause or bypass motion, and a failed enhancement must recover to a stable static surface. Retain fallback screenshots and interaction traces.

## Candidate report and handoff

The report passed to the validator contains:

- the exact manifest SHA-256 and schema version, report phase, candidate path/version/full commit, selected profiles, and generation time;
- one record for every required gate, with `pass`, `fail`, `blocked`, or `not_applicable`, notes, artifact IDs, and one evidence-backed result for every numbered manifest criterion;
- a relative path and SHA-256 for every artifact; paths must stay inside the report bundle;
- in `release-authorized` phase only, explicit founder decisions by domain and a candidate-bound, expiring Ed25519 signature; `evidence-review` must contain no approvals.

The validator checks the machine contract by default. With `--report`, it also binds the exact manifest/source commit/theme path/version/package digest; inspects ZIP structure and theme headers; semantically checks policy snapshots, CycloneDX, video probe inventory, two-build provenance, checksums, and compatibility data; checks criterion freshness and artifact containment/hashes; and verifies a configured founder signature for release authorization. The evidence bundle is size-bounded and artifacts are streamed from opened file descriptors.

Automation still cannot judge the truth of screenshots, legal conclusions, scan quality, or human observations. A passing evidence-review report is structurally and semantically valid for founder inspection, not proof of marketplace acceptance. Real founder sign-off requires the external founder-controlled key that is deliberately not configured by this repository.

### Semantically validated artifact shapes

These fields are mandatory in addition to each artifact's path and report-level SHA-256:

| Artifact | Required semantic shape |
| --- | --- |
| `marketplace-policy-audit` | Ed25519 envelope signed by a configured independent policy collector. Its schema-1 payload has complete canonical profile coverage, human reviewer, zero required Theme Check notices, and, for every canonical reference, exact URL, retrieval time, revision/ETag, captured page text, and matching text SHA-256. |
| `video-delivery-audit` | JSON schema version 1, fresh `generated_at`, `inventory_complete: true`, and `videos`. The validator inventories video extensions in the ZIP, requires an exact audit match, hashes each safely extracted derivative, runs `ffprobe` itself, and requires zero audio streams. It also verifies the external source master exists and matches its hash. `videos: []` passes only when the ZIP contains no video. |
| `scroll-fallback-report` | JSON schema version 1, fresh `generated_at`, `inventory_complete: true`, and `surfaces`. Each surface covers the canonical nine degraded/input modes, story and commerce preservation, no scroll trap, and evidence IDs. `surfaces: []` is the explicit non-immersive case. |
| `sbom` | CycloneDX JSON with spec/version, fresh metadata timestamp, metadata component, and components array. |
| `build-provenance` | Ed25519 envelope signed by a configured independent CI/build attestor. Its schema-1 payload binds manifest, full commit/tree, theme version, and package digest; clean repository, toolchain, exactly two clean identical builds, ZIP-to-source equality, and safe-package inspection claims. Candidate-authored JSON cannot substitute. |
| `candidate-package` | ZIP with one root matching the theme directory, safe unique/collision-free entries, no symlinks or encryption, bounded entries/expansion/ratios, no development exclusions, required theme files, and matching Version/Theme Name/Text Domain. Safe inspection also requires the trusted build attestation. |
| `package-checksums` | Standard SHA-256 lines including the exact candidate ZIP filename and digest. |
| `compatibility-matrix` | JSON schema version 1 with exact values for all ten axes, timestamped pass/unsupported rows, evidence IDs, passing minimum/latest/maximum-advertised coverage, and advertised IDs limited to passing rows. |
| `founder-approval-record` | JSON schema version 1 containing `payload`, `key_id`, and base64 Ed25519 `signature`. The signed canonical payload binds manifest digest, commit, package digest, profiles, the canonical evidence root, issued/expiry times (maximum 30 days), and approvals identical to the report. Object keys are recursively sorted, array order is preserved, UTF-8 is used, and insignificant whitespace is removed before signing. |

The validator also requires a fresh report and criterion timestamps, unique artifact paths and content digests, a clean source repository at the exact full commit, and artifacts contained in the report bundle. It copies verified bytes from the original no-follow descriptor into a private read-only staging directory and performs every semantic check against that immutable snapshot. Git, Python 3, `unzip`, and `ffprobe` must be available alongside Node.js.

Run `node scripts/validate-theme-machine.mjs --self-test` to exercise immutable snapshotting, symlink escape rejection, empty-trust-root failure, and evidence-root mutation detection before trusting the validator in a release environment.

## Non-negotiable release rules

- Update source assets first; rebuild and commit corresponding `.min.css` and `.min.js` outputs.
- Use verified catalog/media SOT data only. Never synthesize product records or trust filenames as provenance.
- Strip audio streams from website-delivery video derivatives, retain masters outside the repo, and attach `ffprobe` plus source-to-derivative provenance evidence.
- Keep WooCommerce authoritative and test cart through checkout against a non-production environment.
- Never weaken, skip, quarantine, or bypass a check to make a candidate green.
- Never place secrets, customer data, credentials, or unapproved production URLs in the archive or handoff.
- Never submit, publish, deploy, buy media, or make a final creative, brand, commerce, licensing, release, or material product decision without explicit founder approval.

Route implementation to `theme-building-machine` with the complete intake. It activates the core pair, assigns only relevant implementation lanes, and collects every gate required by the selected release profiles. All profile gates remain mandatory even when the implementation itself does not need every lane.
