# design-sync Notes

## Preview images

All three preview files use `placehold.co` placeholder images. On re-sync, replace with
real product renders from `renders/output/` or CDN URLs for accurate visual verification
in claude.ai/design.

## Font delivery

Fonts do NOT ship via `dist/skyyrose-ds.css` (Vite would base64-inline woff2 into the CSS).
They ship via `cfg.extraFonts` → `design-system/skyyrose-storefront/src/fonts/fonts.css`.
The converter copies woff2 files and the @font-face CSS into `ds-bundle/fonts/`.

## Canon font set (11 woff2 files, 8 families)

Only fonts referenced by DS components or tokens are included. Provenance:
- `wordpress-theme/skyyrose-flagship/data/collections/<slug>/identity.json` `fonts` key
  blesses: Cinzel (caps), Cormorant Garamond (body), Yellowtail/Pinyon Script/Kaushan Script
  (per-collection scripts — Black Rose=Yellowtail, Love Hurts=Kaushan Script,
  Signature=Pinyon Script, Kids Capsule=Pinyon Script)
- `design-tokens.css` :root blesses: Playfair Display, Bebas Neue, Inter, Cormorant Garamond

Excluded (legacy/retired — in theme.json but referenced by nothing in the DS):
- Barlow, Oswald, Instrument Serif

The `CANON_WOFF2` set in `scripts/sync-theme-assets.mjs` is the enforcement point.
Sync copies only those 11 files and removes any others from `src/fonts/`. `sync:check`
flags any legacy files that remain.

If font family names drift (e.g., theme.json fontFamilies updated), run:
```
npm --prefix design-system/skyyrose-storefront run sync
npm --prefix design-system/skyyrose-storefront run sync:check
```

## Re-sync risks

- `src/fonts/fonts.css` is generated from `theme.json` — never hand-edit it
- `src/tokens/tokens.css` and `src/styles/commercial-polish.css` are verbatim copies from the WP theme
- Any WP theme CSS change requires `npm run sync` in `design-system/skyyrose-storefront/`

## projectId

`.design-sync/config.json` has no `projectId` yet. Task 8 adds it after the project is
created in claude.ai/design. Do not add a placeholder value.

## Collection scripts

Yellowtail, Pinyon Script, and Kaushan Script are NOT in `theme.json` fontFamilies —
they are covered by the `CURATED` map in `sync-theme-assets.mjs` and are included in
`CANON_WOFF2`. If a new collection script font is added, update both maps.
