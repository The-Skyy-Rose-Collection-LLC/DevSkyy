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
- Runtime route: set the approved CDN or WordPress Media delivery URL in **Appearance → Customize → About Film**. The template renders an opt-in, controls-only player; it never autoplays.

## Delivery handoff

The 79 MB original and the 77 MB muted derivative are deliberately excluded from
the installable theme archive. `scripts/package-theme.sh` creates its archive
from `git archive HEAD`, while this repository has no Git LFS policy for theme
video. Upload only the muted derivative to the approved media/CDN delivery
location, verify its final URL has no audio stream, then paste that URL into the
About Film setting before release. Do not upload or deploy the original.

## Collection-world gateways

The four linked collection chapters reuse this theme’s verified Scroll World
images. Their narrative and palette references are the active SOT identity files
in `wordpress-theme/skyyrose-flagship/data/collections/`: `signature/identity.json`,
`black-rose/identity.json`, `love-hurts/identity.json`, and
`kids-capsule/identity.json`. The rendered asset paths are respectively
`assets/scroll-world/scene-1-signature.webp`, `scene-2-black-rose.webp`,
`scene-3-love-hurts.webp`, and `scene-4-kids-capsule.webp`; all were already
bundled with Flagship 2 and are reused rather than replaced with unverified art.
