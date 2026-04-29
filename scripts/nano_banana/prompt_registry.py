"""Prompt Registry — versioned prompt templates with A/B testing and scoring.

Each garment type + view has multiple prompt template versions. The registry
tracks which version scores highest per product category. Winners auto-select.

Architecture:
    1. Templates are keyed by (garment_category, view, version)
    2. Vision spec fills template slots at generation time
    3. After QA scoring, results feed back to promote winning templates
    4. Each model (Gemini, GPT, FLUX) can have model-specific overrides

Usage:
    from nano_banana.prompt_registry import PromptRegistry
    registry = PromptRegistry.load()
    prompt = registry.get_prompt(vision_spec, product, view="front", model="gemini-pro")
    registry.record_score(template_id, qa_score)
    registry.save()
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "data" / "prompt-registry.json"


# ── Garment categories for template routing ──────────────────────────────────

GARMENT_CATEGORIES = {
    "hoodie": ["hoodie", "hooded", "pullover hoodie"],
    "jacket": ["jacket", "bomber", "varsity", "sherpa", "windbreaker"],
    "jersey": [
        "jersey",
        "football jersey",
        "basketball jersey",
        "hockey jersey",
        "baseball jersey",
    ],
    "crewneck": ["crewneck", "sweatshirt", "crew neck"],
    "tee": ["tee", "t-shirt", "shirt"],
    "joggers": ["joggers", "sweatpants", "track pants"],
    "shorts": ["shorts", "basketball shorts"],
    "set": ["set", "tracksuit", "matching set"],
    "accessory": ["beanie", "hat", "fanny pack", "bag", "cap"],
}


def _categorize_garment(vision_desc: dict) -> str:
    """Map vision description to a garment category."""
    garment = vision_desc.get("garment_type", "").lower()
    subtype = (vision_desc.get("garment_subtype") or "").lower()
    combined = f"{garment} {subtype}"

    for category, keywords in GARMENT_CATEGORIES.items():
        for kw in keywords:
            if kw in combined:
                return category
    return "generic"


# ── Template slot system ─────────────────────────────────────────────────────


@dataclass
class VisionSpec:
    """Structured spec extracted from vision analysis — the slots for templates."""

    garment_label: str = ""  # "relaxed hooded varsity bomber"
    fabric: str = ""  # "smooth reflective satin body, matte fleece hood"
    color_map: str = ""  # formatted color lines
    graphics_count: int = 0  # number of graphic elements
    graphics_spec: str = ""  # detailed graphic specs with positions/sizes
    construction: str = ""  # panel/seam/closure details
    branding_verified: str = ""  # from LOGO_TREATMENTS
    negative_constraints: str = ""  # what NOT to generate

    @classmethod
    def from_vision(cls, desc: dict, sku: str = "") -> VisionSpec:
        """Build a VisionSpec from raw vision analysis output."""
        from nano_banana.prompts import LOGO_TREATMENTS

        silhouette = desc.get("silhouette", "")
        subtype = desc.get("garment_subtype", "")
        garment = desc.get("garment_type", "")
        garment_label = f"{silhouette} {subtype or garment}".strip()

        # Colors
        color_lines = []
        for c in desc.get("colors", []):
            area = c.get("area", "")
            color = c.get("color", "")
            finish = c.get("finish", "")
            if area and color:
                color_lines.append(
                    f"  {area}: {color} ({finish})" if finish else f"  {area}: {color}"
                )
        color_map = "\n".join(color_lines) if color_lines else "  Solid black (#000000)"

        # Graphics — with strict position/size enforcement
        graphics = desc.get("graphics", [])
        gfx_count = len(graphics)
        gfx_lines = []
        for i, g in enumerate(graphics, 1):
            location = g.get("location", "unknown position")
            content = g.get("content", "graphic element")
            gtype = g.get("type", "unknown")
            size = g.get("size", "")
            style = g.get("style", "")
            gcolors = g.get("colors", [])

            spec = f'  #{i} "{content}"'
            spec += f"\n      WHERE: {location} — LOCKED POSITION, do not move"
            if size:
                spec += f"\n      SIZE: {size} — LOCKED SIZE, do not enlarge or shrink"
            spec += f"\n      TECHNIQUE: {gtype}"
            if style:
                spec += f"\n      FINISH: {style}"
            if gcolors:
                spec += f"\n      COLORS: {', '.join(str(c) for c in gcolors)}"
            gfx_lines.append(spec)

        graphics_spec = "\n".join(gfx_lines) if gfx_lines else "  NONE — this is a plain garment"

        # Construction
        construction = desc.get("construction", {})
        if isinstance(construction, dict):
            const_parts = [f"  {k}: {v}" for k, v in construction.items() if v]
            const_text = "\n".join(const_parts)
        elif isinstance(construction, list):
            const_text = "\n".join(f"  - {c}" for c in construction[:6])
        else:
            const_text = "  Standard construction"

        # Verified branding
        treatment = LOGO_TREATMENTS.get(sku, "")

        # Negative constraints — the anti-hallucination backbone
        negatives = []
        negatives.append(f"This garment has EXACTLY {gfx_count} graphic element(s)")
        if gfx_count == 0:
            negatives.append("NO logos, NO text, NO patches, NO embroidery — completely blank")
        elif gfx_count == 1:
            negatives.append("ONE graphic only — do NOT add a second logo, patch, or mark anywhere")
        else:
            negatives.append(f"Exactly {gfx_count} graphics listed above — do NOT add extras")

        negatives.append("Do NOT change sizes — if spec says 4.5 inches, render 4.5 inches")
        negatives.append("Do NOT move positions — if spec says left chest, it stays left chest")
        negatives.append("Do NOT invent pockets, stripes, panels, or details not in the reference")
        negatives.append("Do NOT add team names, athlete names, sponsor logos, or league marks")

        return cls(
            garment_label=garment_label,
            fabric=desc.get("fabric_appearance", ""),
            color_map=color_map,
            graphics_count=gfx_count,
            graphics_spec=graphics_spec,
            construction=const_text,
            branding_verified=treatment,
            negative_constraints="\n".join(f"  - {n}" for n in negatives),
        )


# ── Prompt Templates ─────────────────────────────────────────────────────────


@dataclass
class PromptTemplate:
    """A versioned prompt template with performance tracking."""

    id: str  # "jersey_front_v2"
    category: str  # garment category
    view: str  # "front" | "back" | "branding"
    version: int = 1
    model_hint: str = ""  # empty = all models, or "gemini-pro" / "gpt-image"
    template: str = ""  # the actual prompt template with {slot} placeholders
    total_runs: int = 0
    total_score: float = 0.0
    best_score: float = 0.0

    @property
    def avg_score(self) -> float:
        return self.total_score / self.total_runs if self.total_runs > 0 else 0.0

    def render(self, spec: VisionSpec, lighting: dict, product_name: str = "") -> str:
        """Fill template slots with vision spec data."""
        return self.template.format(
            name=product_name,
            garment_label=spec.garment_label,
            fabric=spec.fabric,
            color_map=spec.color_map,
            graphics_count=spec.graphics_count,
            graphics_spec=spec.graphics_spec,
            construction=spec.construction,
            branding_verified=spec.branding_verified,
            negative_constraints=spec.negative_constraints,
            bg=lighting.get("bg", "Dark background"),
            light=lighting.get("light", "Professional lighting"),
            mood=lighting.get("mood", "Luxury fashion"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "view": self.view,
            "version": self.version,
            "model_hint": self.model_hint,
            "template": self.template,
            "total_runs": self.total_runs,
            "total_score": self.total_score,
            "best_score": self.best_score,
        }


# ── Built-in templates ───────────────────────────────────────────────────────

BUILTIN_TEMPLATES: list[PromptTemplate] = [
    # ── FRONT VIEW v1: Strict Spec Sheet ──
    PromptTemplate(
        id="front_v1_strict",
        category="*",
        view="front",
        version=1,
        template="""PRODUCT RENDER SPECIFICATION — {name}
You are receiving a reference tech flat. Reproduce it as a photorealistic 3D product render.

▸ GARMENT: {garment_label}
▸ FABRIC: {fabric}
▸ VIEW: FRONT ONLY — garment facing camera

EXACT COLORS:
{color_map}

GRAPHICS ({graphics_count} total):
{graphics_spec}
{branding_verified}

CONSTRUCTION:
{construction}

STUDIO SETUP:
- No model, no mannequin — garment on invisible form, natural 3D drape
- {bg}
- {light}
- Photorealistic fabric texture — visible weave, thread weight, sheen

WHAT YOU MUST NOT DO:
{negative_constraints}
  - Do NOT show the back of the garment
  - Do NOT add watermarks, price tags, or size labels
  - If ANYTHING is unclear in the reference, LEAVE IT OUT""",
    ),
    # ── FRONT VIEW v2: Narrative + Spec (may work better for Gemini) ──
    PromptTemplate(
        id="front_v2_narrative",
        category="*",
        view="front",
        version=2,
        template="""Study the reference image carefully. This is a {garment_label} called "{name}".

Your job: generate a photorealistic e-commerce product photo showing ONLY the front of this garment.

The garment is {fabric}. It has EXACTLY {graphics_count} graphic element(s):
{graphics_spec}

These graphics are LOCKED — same size, same position, same colors as the reference. Do not move, resize, or duplicate them.

Color spec:
{color_map}

Construction:
{construction}

Render the garment floating on an invisible form (no model, no mannequin) with:
- {bg}
- {light}
- Photorealistic fabric texture with natural 3D drape and shadow

CRITICAL NEGATIVE RULES:
{negative_constraints}
  - FRONT VIEW ONLY — do not show the back
  - Match the reference EXACTLY — this is luxury fashion, accuracy is everything""",
    ),
    # ── FRONT VIEW v3: Minimal (for FLUX — shorter prompts work better) ──
    PromptTemplate(
        id="front_v3_minimal",
        category="*",
        view="front",
        version=3,
        model_hint="flux-pro",
        template="""Photorealistic e-commerce product photo of a {garment_label}, front view only.
{fabric} fabric. On invisible ghost mannequin.
{bg}. {light}.
{graphics_count} graphic(s): {graphics_spec}
Colors: {color_map}
No model. No extras. Match reference exactly.""",
    ),
    # ── BACK VIEW v1 ──
    PromptTemplate(
        id="back_v1_strict",
        category="*",
        view="back",
        version=1,
        template="""PRODUCT RENDER SPECIFICATION — {name} (BACK VIEW)
Reproduce the reference as a photorealistic 3D product render — BACK OF GARMENT ONLY.

▸ GARMENT: {garment_label}
▸ FABRIC: {fabric}
▸ VIEW: BACK ONLY — garment facing away from camera

EXACT COLORS:
{color_map}

BACK GRAPHICS ({graphics_count} total):
{graphics_spec}
{branding_verified}

STUDIO SETUP:
- No model, no mannequin — garment on invisible form, back facing camera
- {bg}
- {light}
- Photorealistic fabric texture

WHAT YOU MUST NOT DO:
{negative_constraints}
  - Do NOT show the front of the garment
  - Match the reference EXACTLY""",
    ),
    # ── JERSEY-SPECIFIC v1 (sport jerseys need extra text accuracy) ──
    PromptTemplate(
        id="jersey_front_v1",
        category="jersey",
        view="front",
        version=1,
        template="""AUTHENTIC SPORT JERSEY RENDER — {name}
This is a REAL sport jersey made with authentic athletic materials.
TEXT AND NUMBER ACCURACY IS THE #1 PRIORITY.

▸ GARMENT: {garment_label}
▸ VIEW: FRONT ONLY

AUTHENTIC SPORT FABRIC — this is NOT a fashion tee, it is a real athletic jersey:
- FOOTBALL JERSEY: Pro-weight polyester mesh, moisture-wicking, tackle-twill numbers with satin stitch borders, reinforced V-neck with 3-color braid, sleeve stripes with overlock finish, NFL-grade athletic cut
- BASKETBALL JERSEY: Lightweight dazzle mesh polyester, sublimation print, wide shoulder straps, deep armholes, NBA-grade tank cut
- HOCKEY JERSEY: Heavy-weight air-knit polyester, fight strap, hooded pullover construction, reinforced elbow patches, NHL-grade loose fit, teal/black horizontal striping
- BASEBALL JERSEY: Button-front athletic mesh, sublimation print, raglan sleeves, MLB-grade relaxed fit

Use the fabric description that matches this specific jersey type.

EXACT COLORS:
{color_map}

TEXT & NUMBERS — PIXEL-PERFECT ACCURACY:
{graphics_spec}
{branding_verified}

CONSTRUCTION:
{construction}

CRITICAL — TEXT AND NUMBER RULES:
- Every digit must be the EXACT correct number from the reference
- Every letter must be correctly spelled — "BLACK IS BEAUTIFUL" not "BLACK IS BEAUTFUL"
- Font style, weight, outline, and fill colors must match exactly
- Rose graphics inside numbers must be reproduced precisely
- Athletic trim (stripes, braids, piping) must match reference colors and width

STUDIO:
- Ghost mannequin, no person — jersey floating with natural athletic drape
- {bg}
- {light}
- Fabric must show authentic mesh/knit texture — NOT flat matte cotton

FORBIDDEN:
{negative_constraints}
  - Do NOT change any numbers or text from the reference
  - Do NOT add real team names, athlete names, or official league logos (NFL/NBA/MLB/NHL shields)
  - Do NOT smooth out the mesh texture — athletic fabric has visible weave
  - FRONT ONLY""",
    ),
    # ── ACCESSORY v1 ──
    PromptTemplate(
        id="accessory_front_v1",
        category="accessory",
        view="front",
        version=1,
        template="""ACCESSORY PRODUCT PHOTO — {name}
Photorealistic product render of this {garment_label}.

DETAILS:
{graphics_spec}
Colors: {color_map}

PRESENTATION:
- Product only, slightly angled for dimension
- {bg}
- {light}
- Tight framing — the accessory fills the frame

RULES:
{negative_constraints}
  - Match the reference EXACTLY""",
    ),
]


# ── Registry ─────────────────────────────────────────────────────────────────


class PromptRegistry:
    """Manages prompt templates with A/B testing and scoring feedback."""

    def __init__(self, templates: list[PromptTemplate] | None = None):
        self.templates: list[PromptTemplate] = templates or list(BUILTIN_TEMPLATES)

    def get_prompt(
        self,
        vision_desc: dict,
        product: dict,
        view: str = "front",
        model: str = "",
    ) -> tuple[str, str]:
        """Select the best prompt template and render it.

        Returns (rendered_prompt, template_id).
        """
        from nano_banana.prompts import COLLECTION_LIGHTING

        sku = product.get("sku", "")
        name = product.get("name", "garment")
        collection = product.get("collection", "black-rose")
        lighting = COLLECTION_LIGHTING.get(collection, COLLECTION_LIGHTING["black-rose"])

        spec = VisionSpec.from_vision(vision_desc, sku)
        category = _categorize_garment(vision_desc)

        # Find matching templates
        candidates = []
        for tpl in self.templates:
            # Match view
            if tpl.view != view:
                continue
            # Match category (specific > wildcard)
            if tpl.category != "*" and tpl.category != category:
                continue
            # Match model hint
            if tpl.model_hint and tpl.model_hint != model:
                continue
            candidates.append(tpl)

        if not candidates:
            # Fallback to any template for this view
            candidates = [t for t in self.templates if t.view == view and t.category == "*"]

        if not candidates:
            log.warning("No template found for %s/%s/%s — using raw spec", category, view, model)
            return spec.graphics_spec, "fallback"

        # Pick winner: category-specific > highest avg score > latest version
        candidates.sort(
            key=lambda t: (
                t.category != "*",  # prefer specific category
                t.avg_score,  # then highest score
                t.version,  # then latest version
            ),
            reverse=True,
        )

        winner = candidates[0]
        rendered = winner.render(spec, lighting, name)

        log.info(
            "PROMPT: template=%s (cat=%s, v%d, avg=%.1f, runs=%d)",
            winner.id,
            winner.category,
            winner.version,
            winner.avg_score,
            winner.total_runs,
        )

        return rendered, winner.id

    def record_score(self, template_id: str, score: float) -> None:
        """Record a QA score for a template — feeds the A/B testing loop."""
        for tpl in self.templates:
            if tpl.id == template_id:
                tpl.total_runs += 1
                tpl.total_score += score
                if score > tpl.best_score:
                    tpl.best_score = score
                log.info(
                    "SCORE: %s → %.1f (avg=%.1f over %d runs)",
                    template_id,
                    score,
                    tpl.avg_score,
                    tpl.total_runs,
                )
                return
        log.warning("Template %s not found in registry", template_id)

    def get_stats(self) -> list[dict]:
        """Get performance stats for all templates."""
        return [
            {
                "id": t.id,
                "category": t.category,
                "view": t.view,
                "version": t.version,
                "model_hint": t.model_hint,
                "runs": t.total_runs,
                "avg_score": round(t.avg_score, 1),
                "best_score": round(t.best_score, 1),
            }
            for t in sorted(self.templates, key=lambda x: x.avg_score, reverse=True)
        ]

    def save(self, path: Path | None = None) -> None:
        """Save registry state (scores, run counts) to JSON."""
        path = path or REGISTRY_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"templates": [t.to_dict() for t in self.templates]}
        path.write_text(json.dumps(data, indent=2))
        log.info("Registry saved to %s (%d templates)", path, len(self.templates))

    @classmethod
    def load(cls, path: Path | None = None) -> PromptRegistry:
        """Load registry from JSON, merging with builtins."""
        path = path or REGISTRY_PATH
        if not path.exists():
            log.info("No registry file — using builtins (%d templates)", len(BUILTIN_TEMPLATES))
            return cls()

        data = json.loads(path.read_text())
        saved = data.get("templates", [])

        # Merge: keep builtin templates but restore scores from saved
        templates = list(BUILTIN_TEMPLATES)
        saved_map = {t["id"]: t for t in saved}

        for tpl in templates:
            if tpl.id in saved_map:
                s = saved_map[tpl.id]
                tpl.total_runs = s.get("total_runs", 0)
                tpl.total_score = s.get("total_score", 0.0)
                tpl.best_score = s.get("best_score", 0.0)

        # Add any custom (non-builtin) templates from saved
        builtin_ids = {t.id for t in BUILTIN_TEMPLATES}
        for s in saved:
            if s["id"] not in builtin_ids:
                templates.append(
                    PromptTemplate(
                        id=s["id"],
                        category=s.get("category", "*"),
                        view=s.get("view", "front"),
                        version=s.get("version", 1),
                        model_hint=s.get("model_hint", ""),
                        template=s.get("template", ""),
                        total_runs=s.get("total_runs", 0),
                        total_score=s.get("total_score", 0.0),
                        best_score=s.get("best_score", 0.0),
                    )
                )

        log.info(
            "Registry loaded: %d templates (%d with scores)",
            len(templates),
            sum(1 for t in templates if t.total_runs > 0),
        )
        return cls(templates)

    def add_template(self, template: PromptTemplate) -> None:
        """Add a custom template to the registry."""
        self.templates.append(template)
        log.info("Added template: %s", template.id)
