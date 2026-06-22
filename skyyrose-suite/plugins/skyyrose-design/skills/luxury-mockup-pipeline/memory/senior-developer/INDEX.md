# Senior Developer — Memory Index

Discipline-specific facts. Reads before every dispatch alongside `_shared/INDEX.md`.

## Entries

<!-- Append on correction. Example:
- [v2.html parallax compose with scale](parallax-scale-compose.md) — appending scale(1.05) to translate3d keeps zoom + parallax together.
-->

- [scroll-timeline-supports-pattern](scroll-timeline-supports-pattern.md) — `animation-timeline: scroll()` syntax, browser support matrix (Chrome/Edge/FF yes, Safari no), `@supports` guard + rAF fallback gate via `CSS.supports`. Compose scale in keyframes, not separate transform.
- [saas-gate-avif-blocked-vs-code](saas-gate-avif-blocked-vs-code.md) — G2 AVIF FAIL has two causes: code-blocked (missing source tag, fixable now) vs asset-blocked (file doesn't exist on disk, G13 catches fakes). forbidden-midnight AVIF is asset-blocked; deferred avifenc run documented inside.
