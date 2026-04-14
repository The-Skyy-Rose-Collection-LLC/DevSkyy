"""
Character creation agent for SkyyRose Elite Studio.

Builds reference sheet prompts for brand characters, with special support
for the canonical SkyyRose mascot 'Rosie'.

Rosie already exists — reference assets live at:
  - assets/branding/mascot/skyyrose-mascot-reference.png  (primary)
  - skyyrose/assets/images/source-products/brand-assets/skyyrose-avatar-reference.jpeg

The frontend mascot system (/api/mascot, MascotBubble.tsx) is the canonical
generation system. This agent bridges Rosie into the Elite Studio creative pipeline.

"Luxury Grows from Concrete."
"""

from __future__ import annotations

import logging
from pathlib import Path

from .models import CharacterPose, CharacterSheet, CharacterSpec

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Existing mascot asset paths (relative to repo root)
# ---------------------------------------------------------------------------

_MASCOT_REFERENCE_PNG = Path("assets/branding/mascot/skyyrose-mascot-reference.png")
_AVATAR_REFERENCE_JPEG = Path(
    "skyyrose/assets/images/source-products/brand-assets/skyyrose-avatar-reference.jpeg"
)

# Base prompt matching the existing frontend /api/mascot route (route.ts:MASCOT_BASE_PROMPT)
# Kept in sync so Python pipeline produces consistent results with the dashboard.
_MASCOT_BASE_PROMPT = (
    "Pixar/Disney-quality 3D animated young Black girl with voluminous curly/afro dark brown hair, "
    "big expressive brown eyes, warm brown skin, friendly confident smile. "
    "Character must be 100% identical to reference image in face, hair, skin tone, art style, and proportions."
)

# ---------------------------------------------------------------------------
# Canonical Rosie spec
# ---------------------------------------------------------------------------

_ROSIE_SPEC = CharacterSpec(
    name="Rosie",
    style="pixar-chibi",
    body_description=(
        "Young Black girl, approximately 6 years old, Pixar-quality 3D render. "
        "Warm brown skin, bright expressive eyes with long lashes, "
        "soft chubby cheeks with a joyful smile. "
        "Compact, slightly chibi proportions — large head, petite frame. "
        "Confident posture — hands on hips or arms slightly out."
    ),
    face_features=(
        "Round face with warm brown skin. Large bright dark brown eyes, "
        "long eyelashes, small button nose, full lips with a wide smile. "
        "Natural hair in two large afro puffs on either side of head, "
        "secured with rose gold satin ribbons tied in bows. "
        "Single small rose gold rose pin on left afro puff. "
        "Expression: joyful, confident, curious."
    ),
    outfit_base=(
        "Mini BLACK Rose Hoodie (child-sized version of br-004): "
        "near-black (#0A0A0A) french terry hoodie with embroidered silver rose on left chest. "
        "Matching mini black joggers with rose gold stripe detail. "
        "Clean white sneakers with rose gold lace tips. "
        "Small rose gold stud earrings."
    ),
    brand_elements=(
        "Rose gold (#B76E79) accents throughout — ribbons, rose pin, sneaker tips",
        "Embroidered SkyyRose silver rose on left chest of mini hoodie",
        "SkyyRose logo subtly visible on sneaker tongue",
        "'Luxury Grows from Concrete.' ethos embodied in confident pose",
        "Oakland pride — subtle Bay Area references in background details",
    ),
    reference_paths=(
        str(_AVATAR_REFERENCE_JPEG),
        str(_MASCOT_REFERENCE_PNG),
    ),
    embedding_path="",
)

# ---------------------------------------------------------------------------
# Prompt building helpers
# ---------------------------------------------------------------------------

_PIXAR_QUALITY_PREAMBLE = (
    "Pixar-quality 3D CGI render, Disney/Pixar animation style, "
    "subsurface scattering on skin, high detail clothing texture, "
    "professional studio lighting, cinematic quality, 4K render. "
)

_ILLUSTRATION_PREAMBLE = (
    "High-quality character illustration, clean line art, "
    "vibrant colors, professional character design sheet style. "
)

_REALISTIC_PREAMBLE = (
    "Photorealistic character render, professional photography style, "
    "natural lighting, high detail. "
)

_STYLE_PREAMBLES = {
    "pixar-chibi": _PIXAR_QUALITY_PREAMBLE,
    "illustration": _ILLUSTRATION_PREAMBLE,
    "realistic": _REALISTIC_PREAMBLE,
}


def _preamble(style: str) -> str:
    return _STYLE_PREAMBLES.get(style, _PIXAR_QUALITY_PREAMBLE)


def _base_character_block(spec: CharacterSpec) -> str:
    """Build the shared character identity block used across all prompts."""
    elements = ", ".join(spec.brand_elements[:3]) if spec.brand_elements else ""
    return (
        f"Character: {spec.name}. "
        f"{spec.body_description} "
        f"Face: {spec.face_features} "
        f"Outfit: {spec.outfit_base} "
        f"Brand elements: {elements}. "
        "SkyyRose luxury streetwear brand. 'Luxury Grows from Concrete.' Oakland, CA."
    )


class CharacterCreationAgent:
    """Generates character reference sheets and pose prompts for SkyyRose characters.

    Produces structured generation prompts suitable for FLUX, Midjourney,
    DALL-E, or any AI image generation system.
    """

    def create_sheet(self, spec: CharacterSpec) -> CharacterSheet:
        """Build a complete reference sheet prompt set for a character."""
        try:
            preamble = _preamble(spec.style)
            base = _base_character_block(spec)

            front_view = (
                f"{preamble}"
                f"{base} "
                "View: straight-on front view, full body visible, "
                "neutral stance with slight smile, arms relaxed at sides. "
                "Clean white or light gray studio background. "
                "Reference sheet quality — all design elements clearly visible."
            )

            side_view = (
                f"{preamble}"
                f"{base} "
                "View: 90-degree side profile, full body visible. "
                "Same outfit and expression as front view. "
                "Clean white studio background. "
                "Character reference sheet quality."
            )

            back_view = (
                f"{preamble}"
                f"{base} "
                "View: back view, full body visible. "
                "Show back of outfit including any back branding. "
                "Afro puffs visible from behind. "
                "Clean white studio background. "
                "Reference sheet quality."
            )

            expression_grid = (
                f"{preamble}"
                f"Character: {spec.name}. {spec.face_features} "
                "Expression reference sheet: 2x3 grid of 6 expressions on clean white background. "
                "Row 1: (1) joyful grin, (2) determined confidence, (3) surprised delight. "
                "Row 2: (4) thinking pose with finger on chin, (5) waving hello, (6) proud arms-crossed. "
                "Same character face, hair, and style in all 6 panels. "
                "Label each expression panel clearly. Reference sheet quality."
            )

            sprite_description = (
                f"2D flat-design web sprite for {spec.name}. "
                f"Simplified {spec.style} art style suitable for web animation. "
                f"{spec.face_features[:100]} "
                f"Outfit: {spec.outfit_base[:100]} "
                "Transparent PNG background. Clean vector-like edges. "
                "Suitable for CSS sprite animation on dark backgrounds."
            )

            return CharacterSheet(
                success=True,
                spec=spec,
                front_view_prompt=front_view,
                side_view_prompt=side_view,
                back_view_prompt=back_view,
                expression_grid_prompt=expression_grid,
                sprite_description=sprite_description,
            )

        except Exception as exc:
            logger.exception("create_sheet failed for %s: %s", spec.name, exc)
            return CharacterSheet(
                success=False,
                spec=spec,
                front_view_prompt="",
                side_view_prompt="",
                back_view_prompt="",
                expression_grid_prompt="",
                sprite_description="",
                error=str(exc),
            )

    def generate_pose(
        self,
        spec: CharacterSpec,
        pose: str,
        product_sku: str = "",
    ) -> CharacterPose:
        """Generate a prompt for a character in a specific pose, optionally wearing a product."""
        try:
            preamble = _preamble(spec.style)
            base = _base_character_block(spec)

            product_clause = ""
            if product_sku:
                product_clause = (
                    f"The character is wearing SkyyRose product SKU {product_sku}. "
                    "Product details must be accurately rendered — fabric texture, "
                    "color, and branding visible. "
                )

            pose_descriptors = {
                "walk": "walking forward with confident stride, one foot in front of the other",
                "run": "running joyfully, arms and legs in motion",
                "wave": "waving hello with big smile, arm raised",
                "point": "pointing finger forward/outward toward camera",
                "celebrate": "arms raised in celebration, jumping or triumphant pose",
                "think": "finger on chin, looking upward thoughtfully",
                "idle": "relaxed standing pose, slight S-curve, small smile",
                "sit": "sitting cross-legged on floor, hands in lap",
                "jump": "mid-jump, arms out, expression of pure joy",
            }

            pose_desc = pose_descriptors.get(pose.lower(), pose)

            generation_prompt = (
                f"{preamble}"
                f"{base} "
                f"{product_clause}"
                f"Pose: {pose_desc}. "
                "Dynamic, expressive pose with SkyyRose brand energy. "
                "Clean background suitable for compositing. "
                "'Luxury Grows from Concrete.' brand spirit."
            )

            return CharacterPose(
                success=True,
                character_name=spec.name,
                pose=pose,
                product_sku=product_sku,
                generation_prompt=generation_prompt,
            )

        except Exception as exc:
            logger.exception("generate_pose failed: %s", exc)
            return CharacterPose(
                success=False,
                character_name=spec.name,
                pose=pose,
                product_sku=product_sku,
                generation_prompt="",
                error=str(exc),
            )

    def create_skyyrose_rosie(self) -> CharacterSheet:
        """Return the canonical SkyyRose mascot 'Rosie' character sheet.

        Uses existing reference assets — Rosie already exists. Prompts are
        kept in sync with the frontend /api/mascot route (MASCOT_BASE_PROMPT).
        """
        try:
            base = _MASCOT_BASE_PROMPT

            ref_note = ""
            if _MASCOT_REFERENCE_PNG.exists():
                ref_note = f"Reference image: {_MASCOT_REFERENCE_PNG}. "
            elif _AVATAR_REFERENCE_JPEG.exists():
                ref_note = f"Reference image: {_AVATAR_REFERENCE_JPEG}. "

            front_view = (
                f"{base} {ref_note}"
                "Full body, standing confidently with hands on hips, studio lighting. "
                "SkyyRose brand energy, 'Luxury Grows from Concrete.' Oakland, CA."
            )
            side_view = (
                f"{base} {ref_note}"
                "Full body, 90-degree side profile, same outfit and expression. "
                "Clean white studio background. Character reference sheet quality."
            )
            back_view = (
                f"{base} {ref_note}"
                "Full body, back view. Afro puffs visible from behind. "
                "SkyyRose branding on back of outfit. Reference sheet quality."
            )
            expression_grid = (
                f"{base} {ref_note}"
                "Expression reference sheet: 2x3 grid of 6 expressions. "
                "Row 1: joyful grin, determined confidence, surprised delight. "
                "Row 2: thinking (finger on chin), waving hello, proud arms-crossed. "
                "Same character in all 6 panels. Label each expression clearly."
            )
            sprite_description = (
                "2D flat-design web sprite for Rosie (SkyyRose mascot). "
                "Simplified art style for CSS animation on dark backgrounds. "
                f"{ref_note}"
                "Transparent PNG, vector-like edges, rose gold #B76E79 accents."
            )

            return CharacterSheet(
                success=True,
                spec=_ROSIE_SPEC,
                front_view_prompt=front_view,
                side_view_prompt=side_view,
                back_view_prompt=back_view,
                expression_grid_prompt=expression_grid,
                sprite_description=sprite_description,
            )
        except Exception as exc:
            logger.exception("create_skyyrose_rosie failed: %s", exc)
            return CharacterSheet(
                success=False,
                spec=_ROSIE_SPEC,
                front_view_prompt="",
                side_view_prompt="",
                back_view_prompt="",
                expression_grid_prompt="",
                sprite_description="",
                error=str(exc),
            )
