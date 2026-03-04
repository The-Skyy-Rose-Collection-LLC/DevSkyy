Execute ALL tasks in ralph-tasks.md IN ORDER. You have 5 task groups:

(1) PRIORITY: Rebuild front-page.php from docs/elite-web-builder-package/homepage/skyyrose-homepage-v2.html — extract CSS/JS/images, convert HTML to WordPress PHP, fix 7 cosmetic issues, wire WooCommerce + AJAX.

(2) IMPROVEMENT 1: Audit inc/enqueue.php and make ALL CSS/JS conditional per-template, generate .min.css/.min.js via terser+csso-cli, bundle engine CSS.

(3) IMPROVEMENT 2: Optimize images — ffmpeg the GIF to WebM/MP4, cwebp scene PNGs to WebP, add loading=lazy everywhere, kill files over 1MB.

(4) IMPROVEMENT 3: Extract design system CSS — create assets/css/system/ with tokens.css, base.css, animations.css, components.css, deduplicate .rv/.grain/.vignette definitions from 53 CSS files.

(5) VERIFICATION: Prove each improvement works — network tab audit, no console errors, immersive pages untouched.

CRITICAL RULES:
- Context7 HARD GATE before ANY code. If Context7 returns stale/missing docs, fall back to WebFetch on developer.wordpress.org or WebSearch. Log every query result in ralph-tasks.md.
- Serena for all file operations.
- Commit after EVERY iteration.
- Read ralph-context.md for the FULL spec — it has the complete page structure, CSS design system, cosmetic fixes, WordPress conversion requirements, all 3 improvement specs with exact shell commands, and the Context7 verification protocol.
- NEVER delete ralph-context.md or ralph-tasks.md.
