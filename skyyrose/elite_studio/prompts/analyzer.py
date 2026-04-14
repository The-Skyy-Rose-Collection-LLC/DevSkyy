"""
Prompt Analyzer — scores incoming prompts and identifies gaps.

Rule-based heuristics (no LLM call) for fast, deterministic analysis.
Detects creative intent, scores quality 0-10, and lists missing context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# SkyyRose brand constants for detection
# ---------------------------------------------------------------------------

_COLLECTIONS = {
    "black rose": "black-rose",
    "blackrose": "black-rose",
    "love hurts": "love-hurts",
    "lovehurts": "love-hurts",
    "signature": "signature",
    "kids capsule": "kids-capsule",
    "kids": "kids-capsule",
    "children": "kids-capsule",
}

_GARMENT_TYPES = frozenset({
    "hoodie", "crewneck", "joggers", "jacket", "sherpa", "jersey", "shorts",
    "shirt", "tee", "t-shirt", "beanie", "sweatpants", "varsity", "fanny",
    "fannie", "set", "tank", "cap", "hat", "dress", "skirt", "pants",
})

_FABRICS = frozenset({
    "sherpa", "french terry", "fleece", "mesh", "satin", "jersey knit",
    "cotton", "polyester", "denim", "silk", "linen", "wool", "cashmere",
    "nylon", "velvet", "corduroy", "chambray", "twill", "canvas",
    "recycled", "organic", "bamboo",
})

_COLORS = frozenset({
    "black", "white", "red", "gold", "rose gold", "silver", "crimson",
    "midnight", "navy", "teal", "mint", "lavender", "orchid", "purple",
    "blue", "green", "orange", "pink", "cream", "charcoal", "burgundy",
})

_SEASONS = frozenset({
    "ss", "fw", "spring", "summer", "fall", "autumn", "winter",
    "resort", "pre-fall", "pre-spring", "holiday", "ss25", "fw25",
    "ss26", "fw26", "ss27", "fw27",
})

_PLATFORMS = frozenset({
    "instagram", "tiktok", "twitter", "x", "facebook", "pinterest",
    "linkedin", "youtube", "threads", "snapchat",
})

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "product-render": ["render", "product image", "product photo", "generate image"],
    "3d-model": ["3d", "three-d", "glb", "gltf", "model", "mesh", "turntable"],
    "social-pack": ["social", "post", "caption", "hashtag", "content pack", "campaign"],
    "product-copy": ["copy", "description", "seo", "meta", "product page", "listing"],
    "design-ideation": ["design", "idea", "concept", "new piece", "new product"],
    "mockup": ["mockup", "mock-up", "flat", "technical drawing", "tech flat"],
    "character-sheet": ["character", "mascot", "avatar", "sprite", "rosie"],
    "scene-composite": ["scene", "composite", "background", "editorial", "lookbook"],
    "virtual-tryon": ["try-on", "tryon", "try on", "virtual fitting", "vton"],
    "collection-plan": ["collection", "line sheet", "assortment", "range plan"],
    "tech-pack": ["tech pack", "spec sheet", "specification", "construction", "measurement"],
    "moodboard": ["mood board", "moodboard", "mood", "inspiration", "vibe", "aesthetic"],
    "colorway-explore": ["colorway", "color variation", "palette", "color explore"],
    "full-product-launch": ["launch", "full product", "end to end", "everything"],
}

# SKU prefix → collection mapping
_SKU_PREFIXES = {
    "br-": "black-rose",
    "lh-": "love-hurts",
    "sg-": "signature",
    "kids-": "kids-capsule",
}


@dataclass(frozen=True)
class PromptAnalysis:
    """Immutable analysis of a raw prompt's quality and gaps."""

    original: str
    score: float
    intent: str
    missing: tuple[str, ...]
    ambiguities: tuple[str, ...]
    enhancement_potential: float


class PromptAnalyzer:
    """Rule-based prompt quality analyzer. No LLM calls — fast and deterministic."""

    def analyze(self, prompt: str) -> PromptAnalysis:
        """Score a raw prompt 0-10 and identify missing context."""
        lower = prompt.lower().strip()
        points = 0.0
        missing: list[str] = []
        ambiguities: list[str] = []

        # --- Intent detection ---
        intent = self._detect_intent(lower)
        if intent == "unknown":
            ambiguities.append("creative intent unclear — could not determine task type")

        # --- SKU detection (+1) ---
        if self._has_sku(lower):
            points += 1.0
        else:
            missing.append("product SKU (e.g., br-001, sg-005)")

        # --- Collection detection (+1) ---
        if self._has_collection(lower):
            points += 1.0
        else:
            missing.append("collection name (Black Rose, Love Hurts, Signature, Kids Capsule)")

        # --- Garment type (+1) ---
        if self._has_garment_type(lower):
            points += 1.0
        else:
            missing.append("garment type (hoodie, jersey, joggers, etc.)")

        # --- Color mention (+1) ---
        if self._has_color(lower):
            points += 1.0
        else:
            missing.append("color or colorway")

        # --- Fabric/material (+1) ---
        if self._has_fabric(lower):
            points += 1.0
        else:
            missing.append("fabric or material (sherpa, french terry, mesh, etc.)")

        # --- Season/occasion (+1) ---
        if self._has_season(lower):
            points += 1.0
        else:
            missing.append("season or occasion (FW26, holiday, etc.)")

        # --- Target price (+1) ---
        if self._has_price(lower):
            points += 1.0
        else:
            missing.append("target price point")

        # --- Mood/aesthetic (+1) ---
        if self._has_mood(lower):
            points += 1.0
        else:
            missing.append("mood or aesthetic direction")

        # --- Platform (for social intents) (+0.5) ---
        if intent in ("social-pack",):
            if self._has_platform(lower):
                points += 0.5
            else:
                missing.append("target platform (Instagram, TikTok, etc.)")

        # --- Reference images (+0.5) ---
        if self._has_reference(lower):
            points += 0.5

        # --- Dimensions/resolution (+0.5) ---
        if self._has_dimensions(lower):
            points += 0.5

        # Clamp score to 0-10
        score = min(10.0, max(0.0, points))
        max_possible = 10.0
        potential = (max_possible - score) / max_possible if max_possible > 0 else 0.0

        return PromptAnalysis(
            original=prompt,
            score=round(score, 1),
            intent=intent,
            missing=tuple(missing),
            ambiguities=tuple(ambiguities),
            enhancement_potential=round(potential, 2),
        )

    def _detect_intent(self, text: str) -> str:
        """Detect creative intent from keywords. Returns best match."""
        scores: dict[str, int] = {}
        for intent, keywords in _INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                scores[intent] = count

        if not scores:
            return "unknown"
        return max(scores, key=scores.get)

    def _has_sku(self, text: str) -> bool:
        return bool(re.search(r"\b(br|lh|sg|kids)-\d{3}\b", text))

    def _has_collection(self, text: str) -> bool:
        return any(col in text for col in _COLLECTIONS)

    def _has_garment_type(self, text: str) -> bool:
        return any(g in text for g in _GARMENT_TYPES)

    def _has_color(self, text: str) -> bool:
        return any(c in text for c in _COLORS) or bool(re.search(r"#[0-9a-fA-F]{6}", text))

    def _has_fabric(self, text: str) -> bool:
        return any(f in text for f in _FABRICS)

    def _has_season(self, text: str) -> bool:
        return any(s in text for s in _SEASONS)

    def _has_price(self, text: str) -> bool:
        return bool(re.search(r"\$\d+", text)) or "price" in text

    def _has_mood(self, text: str) -> bool:
        mood_words = {
            "edgy", "gothic", "luxury", "elegant", "bold", "minimal", "clean",
            "dark", "romantic", "raw", "emotional", "refined", "understated",
            "street", "urban", "dramatic", "moody", "vibrant", "fresh",
            "pastel", "premium", "exclusive", "fierce", "soft", "cozy",
        }
        return any(m in text for m in mood_words)

    def _has_platform(self, text: str) -> bool:
        return any(p in text for p in _PLATFORMS)

    def _has_reference(self, text: str) -> bool:
        ref_indicators = {"reference", "like", "similar to", "inspired by", "based on", ".jpg", ".png", ".webp"}
        return any(r in text for r in ref_indicators)

    def _has_dimensions(self, text: str) -> bool:
        return bool(re.search(r"\d{3,4}\s*x\s*\d{3,4}", text)) or any(
            d in text for d in ("4k", "2k", "1080", "1024", "2048", "resolution")
        )
