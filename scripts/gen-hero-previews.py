#!/usr/bin/env python3
"""Immersive Hub hero-scene PREVIEW generator (OpenAI + open-model FLUX).

Generates the 4 canonical collection hero backdrops (Signature / Black Rose /
Love Hurts / Kids Capsule) from the Guardian-approved v2 prompts in
``docs/brand/immersive-hero-prompts.md`` so the founder can compare engines
BEFORE committing to Midjourney finals.

Two engines, one image per scene each:
  • openai    — gpt-image-2, images.generate, 1536x1024 high  ("open version")
  • replicate — FLUX1.1 [pro] ultra, native 16:9               (best open model)

Keys are read AT RUNTIME from ``.env.hf`` by python-dotenv — never printed.

Usage
-----
  python scripts/gen-hero-previews.py plan                 # free; prints manifest
  python scripts/gen-hero-previews.py go                   # PAID; both engines
  python scripts/gen-hero-previews.py go --engine openai   # PAID; one engine
  python scripts/gen-hero-previews.py go --engine replicate

Output -> renders/oai/_hero_preview/<slug>-<engine>.png
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import httpx

# ── Runtime key load (interpreter reads .env.hf; values never surface) ───────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env.hf", override=False)
except Exception as exc:  # pragma: no cover - dotenv is a hard dep here
    print(f"FATAL: could not load .env.hf ({exc})", file=sys.stderr)
    sys.exit(2)

OUTPUT_DIR = PROJECT_ROOT / "renders" / "oai" / "_hero_preview"

# ── Per-engine cost estimates (USD/image) — STOP-AND-SHOW floors ─────────────
EST_COST = {
    "openai": 0.30,  # gpt-image-2 high, 1536x1024 generate (no ref-image tokens)
    "replicate": 0.06,  # FLUX1.1 [pro] ultra flat per-image on Replicate
}
HARD_CAP_USD = 10.0  # tiny preview run; abort if estimate somehow exceeds this


@dataclass(frozen=True)
class Scene:
    slug: str
    name: str
    body: str  # scene description, MJ flags stripped
    negative: str  # comma-joined bans (folded into prompt for no-negative models)

    @property
    def openai_prompt(self) -> str:
        return f"{self.body}. Strictly do NOT include: {self.negative}."

    @property
    def flux_prompt(self) -> str:
        return f"{self.body}. Avoid: {self.negative}."


SCENES: list[Scene] = [
    Scene(
        slug="signature",
        name="Signature — 4 AM on the Ledge",
        body=(
            "Oakland rooftop concrete parapet at 4 AM, single metallic rose-gold rose "
            "resting on the ledge lower-left third, long warm shadow across raw aggregate "
            "concrete toward camera, distant Bay Bridge cables glowing amber-gold in warm "
            "predawn haze lower-right third, open gradient sky filling center and upper "
            "two-thirds transitioning from deep gold #D4AF37 at horizon to near-black "
            "#0A0A0A overhead, dust motes and faint fog drift across bridge cables, luxury "
            "streetwear editorial, cinematic anamorphic wide, warm-golden grade throughout, "
            "no model no people, calm empty sky center for an overlaid title, dark vignette "
            "toward all four edges heaviest at top-center, Fear of God x Oaklandish x Kith "
            "editorial mood, photographic, ultra-detailed, 8k"
        ),
        negative=(
            "text, watermark, logo, people, figures, silhouettes, ornate baroque ballroom, "
            "fairytale castle, European luxury interior, chandelier, marble columns, cold "
            "blue tones, blue, navy, silver grade, beach, surfboard, tech-minimalism, "
            "white studio"
        ),
    ),
    Scene(
        slug="black-rose",
        name="Black Rose — Concrete Refusal",
        body=(
            "Rain-slick West Oakland freeway underpass at 2am, monolithic I-880 concrete "
            "support column scarred with decades of graffiti ghosts filling the entire left "
            "third of the frame from floor to top edge, a single black rose with "
            "silver-chrome petal edges growing through a crack at the column base in the "
            "lower-left third, hard silver key light raking at 25 degrees from camera-left "
            "catching only the petal rims and casting a thin liquid-silver reflection stripe "
            "across wet dark asphalt, Port of Oakland container crane silhouettes barely "
            "resolved through cold fog at far right edge, vast dark open negative space in "
            "the upper center and center-right of frame for a title overlay, deep "
            "atmospheric void ceiling, monochrome — black #0A0A0A dominates every surface, "
            "silver #C0C0C0 only on rose petal rims and asphalt reflection, cool moonlight, "
            "zero color cast zero warmth, heavy radial vignette darkest at upper corners, "
            "brutalist streetwear-luxury editorial, cinematic anamorphic, Fear of God x "
            "Oaklandish mood, ultra-detailed, 8k"
        ),
        negative=(
            "text, watermark, logo, people, blue, navy, warm color grading, gold tones, "
            "red tones, baroque ballroom, fairytale castle, warm color interior decor, "
            "ornate architecture, cartoon, stock photo"
        ),
    ),
    Scene(
        slug="love-hurts",
        name="Love Hurts — The Beast at the Threshold",
        body=(
            "Rain-slick East Oakland industrial alley at deep night, wide cinematic "
            "anamorphic shot, raw red-brick wall right third glistening with moisture, "
            "corrugated iron gate left third slightly ajar revealing pure darkness beyond, "
            "a single deep-crimson rose resting snapped on wet black asphalt at lower "
            "center, rose petals luminous and intact against the dark ground, crimson neon "
            "bleed off-screen left casting hard red fill across wet brick and asphalt "
            "reflection pools, color palette blood-crimson #DC143C and deep shadow-crimson "
            "#9B0F2E against near-black #0A0A0A, calm open dark negative space in the "
            "center-vertical third of frame for title overlay, heavy vignette pulling to "
            "near-black at all four corners, no people, no faces, presence felt only "
            "through the open gate, Fear of God cinematic stillness meets Palm Angels "
            "street-luxe detail meets Culture Kings drop-moment tension, Oakland civic "
            "grit, luxury streetwear editorial, photographic, ultra-detailed, 8k"
        ),
        negative=(
            "text, watermark, logo, ornate baroque ballroom, fairytale castle, gilded "
            "interior, chandeliers, Valentine florals, soft-focus romance, pink, purple, "
            "blue, navy, European fashion editorial, cartoon, people, faces"
        ),
    ),
    Scene(
        slug="kids-capsule",
        name="Kids Capsule — The City Is the Throne",
        body=(
            "A child in a dark red-black colorblock luxury hoodie stands at the edge of a "
            "raw concrete rooftop parapet in Oakland at magic-hour dusk, back "
            "three-quarters to camera, facing the city skyline, posture unhurried and "
            "grounded, a neatly folded purple-black colorblock hoodie resting on the "
            "concrete ledge beside them, directional warm rose-gold sunlight from "
            "camera-right catching the child's far shoulder and pooling on the rough "
            "concrete surface, Oakland downtown skyline glowing amber-gold at building "
            "faces, Port of Oakland crane silhouettes far left, Bay Bridge string-light arc "
            "low on the right horizon, sky grading from deep warm gold #D4AF37 at the "
            "horizon through rose-amber #B76E79 haze into deep indigo #1A1228 at the "
            "zenith, entire upper sky as calm empty negative space for an overlaid title, "
            "child occupies lower-left third frame, folded garment anchors lower-right, "
            "concrete parapet as horizontal ground line, natural dark vignette at left and "
            "right edges, cinematic anamorphic 16:9, luxury streetwear editorial, Kith "
            "Kids x Oaklandish x Fear of God photographic mood, ultra-detailed, 8k"
        ),
        negative=(
            "text, watermark, logo, crown, throne chair, throne, tiny crown, cartoon, "
            "pastel, blue, navy, ornate baroque ballroom, fairytale castle, creepy, child "
            "facing camera, staring at camera, soft focus, saccharine, generic stock photo, "
            "European luxury house aesthetic, white background, floral props"
        ),
    ),
]


# ── Engines ──────────────────────────────────────────────────────────────────
def gen_openai(scene: Scene) -> bytes:
    """gpt-image-2 text-to-image, 1536x1024 landscape, high fidelity."""
    from openai import OpenAI

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY absent from .env.hf")
    client = OpenAI(api_key=key, timeout=180.0)
    resp = client.images.generate(
        model="gpt-image-2",
        prompt=scene.openai_prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    b64 = resp.data[0].b64_json
    if not b64:
        raise RuntimeError("openai returned no image data")
    return base64.b64decode(b64)


def gen_replicate(scene: Scene) -> bytes:
    """FLUX1.1 [pro] ultra on Replicate, native 16:9."""
    import replicate

    key = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not key:
        raise RuntimeError("REPLICATE_API_TOKEN absent from .env.hf")
    output = replicate.Client(api_token=key).run(
        "black-forest-labs/flux-1.1-pro-ultra",
        input={
            "prompt": scene.flux_prompt,
            "aspect_ratio": "16:9",
            "output_format": "png",
            "safety_tolerance": 6,
            "raw": False,
        },
    )
    return _read_replicate_output(output)


def _read_replicate_output(output: object) -> bytes:
    """Normalize Replicate's FileOutput | list | url-string into raw bytes."""
    if isinstance(output, list):
        output = output[0]
    if hasattr(output, "read"):  # FileOutput
        data = output.read()
        if not isinstance(data, bytes):
            raise TypeError(f"FileOutput.read() returned {type(data).__name__}, expected bytes")
        return data
    url = str(output)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith("replicate.delivery"):
        raise RuntimeError(f"refusing to fetch untrusted Replicate URL: {url!r}")
    # follow_redirects=False so a CDN redirect cannot bounce the fetch to an
    # unvalidated (internal) host after the allowlist check.
    resp = httpx.get(url, follow_redirects=False, timeout=120.0)
    resp.raise_for_status()
    return resp.content


ENGINES = {"openai": gen_openai, "replicate": gen_replicate}


# ── Manifest / orchestration ─────────────────────────────────────────────────
def build_manifest(engines: list[str]) -> str:
    n = len(SCENES)
    lines = [
        "STOP — Confirm before proceeding (PAID hero-scene preview generation):",
        "",
        f"  Scenes      : {n}  (signature, black-rose, love-hurts, kids-capsule)",
        f"  Engines     : {', '.join(engines)}",
        f"  Images      : {n * len(engines)}",
        "",
        "  Engine      Model                            Size        $/img   Subtotal",
        "  " + "-" * 70,
    ]
    total = 0.0
    specs = {
        "openai": ("gpt-image-2 (high)", "1536x1024"),
        "replicate": ("FLUX1.1 [pro] ultra", "16:9 ~2K"),
    }
    for eng in engines:
        model, size = specs[eng]
        sub = n * EST_COST[eng]
        total += sub
        lines.append(f"  {eng:<11} {model:<32} {size:<11} ${EST_COST[eng]:<5.2f}  ${sub:.2f}")
    lines += [
        "  " + "-" * 70,
        f"  EST. TOTAL  : ~${total:.2f}   (FLOOR estimate; OpenAI/Replicate bill actual)",
        f"  Hard cap    : ${HARD_CAP_USD:.2f}" + ("  ⚠ EXCEEDED" if total > HARD_CAP_USD else ""),
        "",
        "  Keys present:",
        f"    OPENAI_API_KEY     {'✓' if os.environ.get('OPENAI_API_KEY') else '✗ MISSING'}",
        f"    REPLICATE_API_TOKEN{'  ✓' if os.environ.get('REPLICATE_API_TOKEN') else '  ✗ MISSING'}",
        "",
        f"  Output      : {OUTPUT_DIR.relative_to(PROJECT_ROOT)}/<slug>-<engine>.png",
        "",
        "Proceed? [y/N]",
    ]
    return "\n".join(lines)


def run(engines: list[str]) -> int:
    total_est = sum(len(SCENES) * EST_COST[e] for e in engines)
    if total_est > HARD_CAP_USD:
        print(f"ABORT: estimate ${total_est:.2f} exceeds hard cap ${HARD_CAP_USD:.2f}")
        return 2
    import openai

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    for scene in SCENES:
        for eng in engines:
            dest = OUTPUT_DIR / f"{scene.slug}-{eng}.png"
            try:
                print(f"[{eng}] {scene.slug} … generating", flush=True)
                data = ENGINES[eng](scene)
                dest.write_bytes(data)
                print(f"[{eng}] {scene.slug} ✓ {dest}  ({len(data) // 1024} KB)", flush=True)
            except openai.AuthenticationError:
                # Never print str(exc) — the OpenAI SDK echoes a partial key in it.
                print(
                    f"[{eng}] {scene.slug} ✗ AuthenticationError: check OPENAI_API_KEY",
                    file=sys.stderr,
                )
                return 1
            except Exception as exc:  # noqa: BLE001 — surface, continue other scenes
                failures += 1
                print(f"[{eng}] {scene.slug} ✗ {type(exc).__name__}: {exc}", file=sys.stderr)
    print(f"\nDone. {len(SCENES) * len(engines) - failures} ok, {failures} failed -> {OUTPUT_DIR}")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Hero-scene preview generator")
    ap.add_argument("mode", choices=["plan", "go"])
    ap.add_argument(
        "--engine",
        action="append",
        choices=["openai", "replicate"],
        help="restrict to one engine (repeatable); default = both",
    )
    args = ap.parse_args()
    engines = args.engine or ["openai", "replicate"]
    if args.mode == "plan":
        print(build_manifest(engines))
        return 0
    return run(engines)


if __name__ == "__main__":
    raise SystemExit(main())
