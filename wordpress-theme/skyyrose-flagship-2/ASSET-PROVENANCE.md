# About Scroll World — Asset Provenance

## Founder portrait

- Runtime path: `assets/sot/branding/about/skyy-rose-founder-portrait.jpg`
- Source: `/Users/theceo/Downloads/about-skyyrose.html`, embedded hero JPEG supplied for this About page.
- Source SHA-256: `b13f7728fe3f554f2669e4969b3512772b240acbd81bb243546fc756b625db3c`
- Pixel verification: portrait of Skyy Rose in a white and rose-gold set with red-rose embroidery; verified by visual inspection on 2026-08-04.
- Page use: founder-story hero, film poster/fallback, and origin chapter.

## The Skyy Rose Collection film

- Original source: `/Users/theceo/Downloads/Corey Foster- The Skyy Rose Collection.mp4`
- Original SHA-256: `9844b95ac9ad252a4e7c495c7af4c1ba666676fb22a3d8fd4831d253c2b56624`
- Source profile: 1920×1080 H.264 video, 70.028292 seconds, with AAC audio.
- Delivery derivative: `dist/about-video-delivery/corey-foster-skyy-rose-collection-muted.mp4` (Git-ignored by the repository’s `dist/` rule).
- Delivery SHA-256: `1e943ee0c522dce17705bc46328ea182283bf01baaa1ab8cac2aa0518fdc5c06`
- Delivery profile: 1920×1080 H.264 video, 70.028 seconds, **video stream only**; verified with `ffprobe` on 2026-08-04.
- Runtime route: selected destination is the **WordPress Media Library**. Upload only the approved muted derivative, then set its URL in **Appearance → Customize → About Film**. The template renders an opt-in, controls-only player; it never autoplays.

## Delivery handoff

The 79 MB original and the 77 MB muted derivative are deliberately excluded from
the installable theme archive. `scripts/package-theme.sh` creates its archive
from `git archive HEAD`, while this repository has no Git LFS policy for theme
video. Upload only the muted derivative to the WordPress Media Library, verify
its final URL has no audio stream, then paste that URL into the About Film
setting before release. Do not upload or deploy the original.

## Rights authorization

Corey Foster, Founder, confirmed on 2026-08-04 that SkyyRose LLC owns or
holds the necessary worldwide rights to host, distribute, and include in
theme/demo delivery both *The Skyy Rose Collection* film and its muted
derivative, and the Pre-Order editorial film and its muted derivative. The
authorization includes WordPress Media Library delivery of the muted About-film
derivative.

## Collection-world gateways

The four linked collection chapters reuse this theme’s verified Scroll World
images. Their narrative and palette references are the active SOT identity files
in `wordpress-theme/skyyrose-flagship/data/collections/`: `signature/identity.json`,
`black-rose/identity.json`, `love-hurts/identity.json`, and
`kids-capsule/identity.json`. The rendered asset paths are respectively
`assets/scroll-world/scene-1-signature.webp`, `scene-2-black-rose.webp`,
`scene-3-love-hurts.webp`, and `scene-4-kids-capsule.webp`; all were already
bundled with Flagship 2 and are reused rather than replaced with unverified art.

## Product 3D viewer dependency

- Runtime library: `assets/js/lib/model-viewer.min.js`
- Package: `@google/model-viewer` 4.1.0, UMD production build.
- License: BSD-3-Clause; copyright Google LLC 2019.
- Hardened bundled SHA-256:
  `575c39153b62d0af5a51ea38d992cbe62aad91f8f414737966bae985786df236`.
- Hardening modification: upstream remote Draco, Basis/KTX2, and Lottie
  fallback URLs were replaced with same-origin theme paths. The runtime also
  sets those paths before the custom element initializes.
- Unsupported decoder fallbacks resolve only to a same-origin `disabled/`
  namespace. Approved models reject Draco, Meshopt, Basis/KTX2, Lottie, and
  external resources, so no decoder or loader request is valid at runtime.
- Supply-chain rule: the library is self-hosted and is enqueued only when the
  committed `assets/sot/3d/approved-models.json` resolver returns a model with
  approved gate, provenance, policy-attestation, and founder-approval fields.
- Integrity rule: a manifest entry must bind the exact SKU to
  `assets/sot/3d/models/<sku>.glb`. PHP verifies the real file SHA-256, GLB v2
  header and declared length, self-contained resources, and prohibited
  compression/texture extensions before generating a browser URL.
- Product models: the manifest is intentionally empty until a real GLB passes
  the repository's five-angle visual gate and signed release controls.
