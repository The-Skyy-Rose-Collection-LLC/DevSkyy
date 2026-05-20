<claude-mem-context>

</claude-mem-context>

# public/ — Static assets served by the FastAPI app

Static files served directly by `main_enterprise.py` via FastAPI's `StaticFiles` mount. Do not confuse with `wordpress-theme/skyyrose-flagship/assets/` — these are for the Python API server, not WordPress.

## Key files

- `draco/draco_decoder.js` — Draco geometry decoder JavaScript (client-side). Used by Three.js `DRACOLoader` to decompress `.drc` 3D model files in the browser.
- `draco/draco_decoder.wasm` — WebAssembly Draco decoder. Loaded by `draco_decoder.js` — both files must be present and version-matched.
- `draco/draco_encoder.js` — Draco encoder for client-side compression (used in editor tooling, not runtime).
- `draco/draco_wasm_wrapper.js` — WASM bridge between the JS decoder and the WASM binary. Do not edit — it is a build artifact from the Draco npm package.
- `draco/README.md` — Version and update instructions for the Draco binaries.
- `experiences/black-rose.html` — Standalone immersive HTML experience for the Black Rose collection. Self-contained (inline Three.js scene, no server-side rendering).
- `experiences/love-hurts.html` — Standalone immersive HTML for Love Hurts collection.
- `experiences/signature.html` — Standalone immersive HTML for Signature collection.

## Conventions

- Draco files are versioned together — never update one without the others. Check `draco/README.md` for the current version. Match the version used by `wordpress-theme/skyyrose-flagship/assets/js/` Three.js imports.
- Immersive experience HTML files in `experiences/` are self-contained — no external CSS or JS imports that would break if served from a different origin. Test offline before deploying.
- Adding new static assets: mount point is configured in `main_enterprise.py`. New top-level directories under `public/` need a corresponding `StaticFiles` mount added there.
- Experience HTML files correspond to collection templates in `wordpress-theme/skyyrose-flagship/template-immersive-*.php` — keep collection slug naming consistent.

## Don't

- Don't put secrets, API keys, or environment-specific config in `public/` — everything here is world-readable.
- Don't hand-edit Draco WASM/JS files — replace the entire `draco/` directory from a versioned Draco npm release.
- Don't add server-rendered templates here — `public/` is pure static. API routes go in `api/`.

## Related

- `main_enterprise.py` — mounts `public/` as a `StaticFiles` directory
- `wordpress-theme/skyyrose-flagship/template-immersive-*.php` — WP counterparts to the experience HTML files
- `services/ai_3d/` — 3D model generation pipeline that produces `.drc` files consumed by the Draco decoder
