"""Prompt simplification for CLIP alignment scoring (advisory utility).

**Empirical finding (2026-05-01):** A/B testing this against 4 real product
shots showed simplification *did not* reliably improve absolute CLIP
alignment scores — mean delta was -0.013 across the sample. CLIP-base's
text encoder is robust to brand noise (unfamiliar tokens contribute
near-zero), and longer prompts often pool more useful semantic context
than aggressively-stripped ones.

**Production guidance:** for the round-table and nano-banana alignment
scorers, prefer the *original* generation prompt (it's what was actually
sent to the generator, and ranking renders against the same original
prompt gives consistent relative ordering — which is what discrimination
actually needs).

**When this module IS useful:**
  - Scoring user-facing search queries against catalog images (queries
    are casual prose, often brand-laden in unhelpful ways).
  - Visual-similarity widgets that need a tightly normalized text query.
  - Any context where you control the prompt that goes into CLIP and want
    to maximize chance it grounds in CLIP's pretraining vocabulary.

**Pipeline:**
  1. Lowercase + light punctuation normalization.
  2. Replace brand-specific landmarks ("Bay Bridge" -> "city bridge").
  3. Strip SKU codes (br-001, sg-014, kids-001-twin).
  4. Strip hex color codes (#B76E79, #0a0a0a).
  5. Strip brand/collection/marketing terms (SkyyRose, Black Rose, luxury).
  6. Collapse whitespace.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

import re

# Tokens we strip outright. Order doesn't matter; matched as case-insensitive
# whole-word patterns. Multi-word brand names (e.g. "Black Rose") are matched
# with the embedded space.
_BRAND_TERMS: tuple[str, ...] = (
    # Master brand
    "skyyrose",
    "skyy rose",
    "skyy-rose",
    # Collection names
    "black rose",
    "love hurts",
    "kids capsule",
    "kids-capsule",
    "signature edition",
    "signature collection",
    # Marketing adjectives that don't ground in CLIP-base
    "exclusive",
    "luxury",
    "premium",
    "high-end",
    "high end",
    "couture",
    "limited edition",
    "limited-edition",
    "bespoke",
    "elevated",
    "curated",
    "iconic",
    "signature",  # noisy as marketing word; keep AFTER specific phrases above
    # Brand-specific iconography CLIP doesn't ground
    "bay bridge",
    "golden gate bridge",
    "golden gate",
    "oakland",
    "san francisco",
    "bay area",
)

# Specific landmarks/phrases mapped to generic visual equivalents.
# Applied BEFORE _BRAND_TERMS strip so the generic substitute survives.
_LANDMARK_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("bay bridge skyline", "city skyline"),
    ("bay bridge", "city bridge"),
    ("golden gate bridge", "suspension bridge"),
    ("golden gate", "suspension bridge"),
)

# SKU code pattern: 2-4 letter prefix, hyphen, alphanumeric tail.
# Matches br-001, sg-014, kids-001, br-001-twin, etc.
_SKU_PATTERN = re.compile(r"\b[a-z]{2,4}-[a-z0-9]+(?:-[a-z0-9]+)?\b", re.IGNORECASE)

# Hex color codes: #RRGGBB or #RGB.
_HEX_PATTERN = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _normalize_whitespace(text: str) -> str:
    """Collapse internal whitespace and strip."""
    return re.sub(r"\s+", " ", text).strip()


def _strip_punctuation_around_words(text: str) -> str:
    """Light cleanup so punctuation around removed brand terms doesn't linger.

    Strips parentheses, quotes, and double-hyphens that often wrap brand names
    in marketing prompts. Preserves apostrophes and intra-word hyphens.
    """
    text = re.sub(r"[\"'`()]", " ", text)
    text = re.sub(r"\s--+\s", " ", text)
    text = re.sub(r"\s*[!?]+\s*", " ", text)
    return text


def simplify_for_clip(prompt: str) -> str:
    """Return a CLIP-friendly version of `prompt`.

    Pipeline:
      1. Lowercase + light punctuation normalization.
      2. Replace brand-specific landmarks with generic visual equivalents.
      3. Strip SKU codes (br-001, sg-014, ...).
      4. Strip hex color codes (#B76E79, #0a0a0a, ...).
      5. Strip brand/collection/marketing terms (whole-word, case-insensitive).
      6. Collapse whitespace.

    Empty/whitespace input returns an empty string.
    """
    if not prompt or not prompt.strip():
        return ""

    text = prompt.lower()
    text = _strip_punctuation_around_words(text)

    # 2. Landmark genericization (must run before brand-strip, else we lose
    #    the substituted generic too).
    for landmark, replacement in _LANDMARK_REPLACEMENTS:
        text = re.sub(re.escape(landmark), replacement, text)

    # 3. SKU codes
    text = _SKU_PATTERN.sub(" ", text)

    # 4. Hex codes
    text = _HEX_PATTERN.sub(" ", text)

    # 5. Brand/marketing terms — match longest first so multi-word phrases
    #    like "kids capsule" beat the single token "kids" if it ever appears.
    sorted_terms = sorted(_BRAND_TERMS, key=len, reverse=True)
    for term in sorted_terms:
        # Word-boundary match, but allow hyphens inside the term itself.
        pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
        text = re.sub(pattern, " ", text)

    return _normalize_whitespace(text)
