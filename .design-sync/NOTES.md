# design-sync Notes

## Preview images

All three preview files use `placehold.co` placeholder images. On re-sync, replace with
real product renders from `renders/output/` or CDN URLs for accurate visual verification
in claude.ai/design.

## Font delivery

Fonts do NOT ship via `dist/skyyrose-ds.css` (Vite would base64-inline all 20 woff2 ~580 KB).
They ship via `cfg.extraFonts` → `design-system/skyyrose-storefront/src/fonts/fonts.css`.
The converter copies woff2 files and the @font-face CSS into `ds-bundle/fonts/`.

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

Three script fonts (Yellowtail, Pinyon Script, Kaushan Script) are NOT in `theme.json`
fontFamilies — they're covered by the `CURATED` map in `sync-theme-assets.mjs`. If new
collection script fonts are added to the theme, add them there.
