#!/usr/bin/env python3
"""Product DNA Extraction — Multi-Model Vision Consensus.

Runs GPT-4.1, Claude Opus 4.6, and Gemini 3 Pro on each product's reference
image in parallel, extracts structured specs, resolves via 2/3 consensus.

Output: data/product-dna/{sku}.json per product.

Usage:
    source .venv-imagery/bin/activate
    python scripts/product_dna_extract.py --sku br-001
    python scripts/product_dna_extract.py --all

This is a standalone Phase 1 tool. The full v3 framework (tournament QA,
candidate generation, human review) is being built in a parallel worktree.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("product-dna")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

DNA_DIR = PROJECT_ROOT / "data" / "product-dna"
DNA_DIR.mkdir(parents=True, exist_ok=True)

# ---- Vision models to use ------------------------------------------------

GPT_VISION_MODEL = "gpt-4o"  # OpenAI flagship vision (most reliable)
CLAUDE_VISION_MODEL = "claude-opus-4-6"  # Anthropic flagship (Opus 4.6)
GEMINI_VISION_MODEL = "gemini-3-pro-preview"  # Google Gemini 3 Pro (latest flagship)

# ---- Extraction schema ---------------------------------------------------

EXTRACTION_PROMPT = """You are analyzing a product photo for the SkyyRose luxury fashion brand.
Extract ONLY what you can see with high confidence. NEVER guess or invent details.

Return ONLY valid JSON (no markdown fences) with this exact schema:

{
  "garment_type": "specific garment name (e.g. 'hooded satin bomber jacket', 'crewneck sweatshirt')",
  "base_color": "primary color as hex code (e.g. '#0A0A0A')",
  "base_color_name": "human-readable color name (e.g. 'true black', 'rose gold')",
  "secondary_colors": ["list of other significant colors visible, as hex"],
  "text_content": [
    {"text": "exact text as shown", "location": "where on garment", "color": "#hex", "style": "font description"}
  ],
  "numbers": [
    {"number": "32", "location": "back center", "size_inches": "estimate"}
  ],
  "logos": [
    {"type": "rose-only | SR-monogram | love-hurts-wordmark | etc", "position": "front chest center", "size_inches": 5, "material": "embroidered | silicone patch | sublimated | printed"}
  ],
  "construction": ["4-button placket", "ribbed cuffs", "welt pockets", "attached hood"],
  "fabric": "material description (e.g. 'satin shell with ribbed knit trim', 'heavyweight cotton 320gsm')",
  "patches": ["description of any patches visible"],
  "design_elements": ["stripes, gradients, panels"],
  "stitching_details": "any visible stitching/seam notes",
  "overall_description": "1-2 sentence summary"
}

If a field is not present in the image, use an empty string or empty array.
If unsure, err on the side of leaving a field empty rather than guessing.
"""

# ---- Client factories ----------------------------------------------------


def _load_env_keys():
    """Load API keys from .env.hf or environment."""
    env_path = PROJECT_ROOT / ".env.hf"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_openai_client():
    import openai

    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        log.warning("No OPENAI_API_KEY — skipping GPT-4o vision")
        return None
    return openai.OpenAI(api_key=key)


def get_anthropic_client():
    try:
        import anthropic
    except ImportError:
        log.warning("anthropic package not installed — skipping Claude vision")
        return None
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        log.warning("No ANTHROPIC_API_KEY — skipping Claude vision")
        return None
    return anthropic.Anthropic(api_key=key)


def get_gemini_client():
    from google import genai

    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        log.warning("No GOOGLE_API_KEY — skipping Gemini vision")
        return None
    return genai.Client(api_key=key, http_options={"timeout": 120_000})


# ---- Vision analysis per model ------------------------------------------


def _load_image_b64(image_path: Path) -> tuple[str, str]:
    """Return (base64_data, mime_type)."""
    ext = image_path.suffix.lower()
    mime = (
        "image/jpeg"
        if ext in (".jpg", ".jpeg")
        else "image/webp" if ext == ".webp" else "image/png"
    )
    return base64.b64encode(image_path.read_bytes()).decode("utf-8"), mime


def _parse_json_response(text: str) -> dict:
    """Strip markdown fences and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.warning("JSON parse failed: %s; raw=%s", e, text[:200])
        return {"_parse_error": str(e), "_raw": text[:500]}


def analyze_with_gpt(client, image_path: Path) -> dict:
    b64, mime = _load_image_b64(image_path)
    try:
        response = client.chat.completions.create(
            model=GPT_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            max_tokens=2000,
        )
        text = response.choices[0].message.content
        return _parse_json_response(text)
    except Exception as exc:
        log.error("GPT vision failed: %s", exc)
        return {"_error": str(exc)}


def analyze_with_claude(client, image_path: Path) -> dict:
    b64, mime = _load_image_b64(image_path)
    try:
        response = client.messages.create(
            model=CLAUDE_VISION_MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": mime, "data": b64},
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )
        text = response.content[0].text
        return _parse_json_response(text)
    except Exception as exc:
        log.error("Claude vision failed: %s", exc)
        return {"_error": str(exc)}


def analyze_with_gemini(client, image_path: Path) -> dict:
    from google.genai import types

    try:
        response = client.models.generate_content(
            model=GEMINI_VISION_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=image_path.read_bytes(), mime_type=_load_image_b64(image_path)[1]
                ),
                EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=2000,
            ),
        )
        return json.loads(response.text)
    except Exception as exc:
        log.error("Gemini vision failed: %s", exc)
        return {"_error": str(exc)}


# ---- Consensus voting -----------------------------------------------------


def _normalize(val):
    """Normalize value for comparison (strip whitespace, lowercase strings)."""
    if isinstance(val, str):
        return val.strip().lower()
    if isinstance(val, list):
        return [_normalize(x) for x in val]
    return val


def _values_agree(a, b) -> bool:
    """Check if two extracted values semantically agree."""
    if a is None or b is None:
        return False
    na, nb = _normalize(a), _normalize(b)
    if isinstance(na, str) and isinstance(nb, str):
        # Partial match for strings (one contains the other)
        if not na or not nb:
            return False
        return na == nb or na in nb or nb in na
    if isinstance(na, list) and isinstance(nb, list):
        # Lists agree if their sets overlap significantly
        if not na and not nb:
            return True
        sa = {str(x).lower() for x in na}
        sb = {str(x).lower() for x in nb}
        if not sa or not sb:
            return len(sa) == len(sb)
        overlap = len(sa & sb) / max(len(sa), len(sb))
        return overlap >= 0.5
    return na == nb


def consensus_vote(results: dict[str, dict]) -> tuple[dict, list[dict]]:
    """Resolve 3 model outputs via 2-of-3 majority voting.

    Returns (consensus_dict, disagreement_log).
    """
    # Get all fields present in any result
    all_fields = set()
    valid_results = {
        k: v for k, v in results.items() if "_error" not in v and "_parse_error" not in v
    }
    for r in valid_results.values():
        all_fields.update(r.keys())

    consensus = {}
    disagreements = []

    for field in sorted(all_fields):
        values = {model: r.get(field) for model, r in valid_results.items()}

        # Count agreements
        models = list(values.keys())
        if len(models) < 2:
            consensus[field] = next(iter(values.values())) if values else None
            continue

        # Compare each pair
        agreements = []
        for i, m1 in enumerate(models):
            for m2 in models[i + 1 :]:
                if _values_agree(values[m1], values[m2]):
                    agreements.append((m1, m2))

        if len(agreements) >= 1:
            # At least 2 models agree — take their value
            consensus_models = set()
            for pair in agreements:
                consensus_models.update(pair)
            # Use the first agreeing model's value
            consensus[field] = values[next(iter(consensus_models))]
            if len(consensus_models) < len(models):
                disagreements.append(
                    {
                        "field": field,
                        "agreed_models": list(consensus_models),
                        "disagreeing_models": [m for m in models if m not in consensus_models],
                        "values": values,
                    }
                )
        else:
            # No consensus — record all values, flag for review
            disagreements.append(
                {
                    "field": field,
                    "no_consensus": True,
                    "values": values,
                }
            )
            # Use GPT result as default when no consensus
            consensus[field] = values.get("gpt") or values.get("claude") or values.get("gemini")

    return consensus, disagreements


# ---- Orchestration --------------------------------------------------------


def extract_dna(sku: str, image_path: Path, clients: dict) -> dict:
    """Run all 3 vision models in parallel, return consensus DNA."""
    log.info("Analyzing %s with 3 vision models...", sku)

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        if clients.get("openai"):
            futures["gpt"] = pool.submit(analyze_with_gpt, clients["openai"], image_path)
        if clients.get("anthropic"):
            futures["claude"] = pool.submit(analyze_with_claude, clients["anthropic"], image_path)
        if clients.get("gemini"):
            futures["gemini"] = pool.submit(analyze_with_gemini, clients["gemini"], image_path)

        for model, fut in futures.items():
            try:
                results[model] = fut.result(timeout=90)
                log.info("  %s done", model)
            except Exception as exc:
                log.error("  %s failed: %s", model, exc)
                results[model] = {"_error": str(exc)}

    consensus, disagreements = consensus_vote(results)

    return {
        "sku": sku,
        "reference_image": str(image_path.relative_to(PROJECT_ROOT)),
        "analyzed_at": datetime.now().isoformat(),
        "models_used": list(results.keys()),
        "consensus": consensus,
        "disagreements": disagreements,
        "raw_results": results,
    }


def save_dna(dna: dict, sku: str) -> Path:
    out_path = DNA_DIR / f"{sku}.json"
    out_path.write_text(json.dumps(dna, indent=2, default=str) + "\n")
    log.info("Saved DNA → %s", out_path.relative_to(PROJECT_ROOT))
    return out_path


def print_summary(dna: dict):
    """Print a readable summary of extracted DNA."""
    c = dna.get("consensus", {})
    print(f"\n{'=' * 60}")
    print(f"DNA for {dna['sku']} — {len(dna.get('models_used', []))} models")
    print(f"{'=' * 60}")
    print(f"Garment:    {c.get('garment_type', 'N/A')}")
    print(f"Base color: {c.get('base_color', 'N/A')} ({c.get('base_color_name', '')})")
    if c.get("text_content"):
        print(f"Text:       {c['text_content']}")
    if c.get("numbers"):
        print(f"Numbers:    {c['numbers']}")
    if c.get("logos"):
        print(f"Logos:      {c['logos']}")
    print(f"Fabric:     {c.get('fabric', 'N/A')}")
    if dna.get("disagreements"):
        print(f"\n⚠️  {len(dna['disagreements'])} field(s) had disagreement — flagged for review")


# ---- CLI ------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Extract product DNA via vision consensus")
    parser.add_argument("--sku", type=str, default=None, help="Single SKU to analyze")
    parser.add_argument("--all", action="store_true", help="Analyze all SKUs with reference images")
    parser.add_argument("--dry-run", action="store_true", help="List what would be analyzed")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print summary after each")
    args = parser.parse_args()

    _load_env_keys()

    # Load references
    from nano_banana.catalog import load_references

    refs = load_references()

    # Filter SKUs
    if args.sku:
        skus = [args.sku] if args.sku in refs else []
    else:
        skus = [sku for sku, entry in refs.items() if entry.get("reference_image")]

    if not skus:
        log.error("No SKUs to analyze")
        return 1

    if args.dry_run:
        print(f"Would analyze {len(skus)} SKUs:")
        for sku in skus:
            ref = refs[sku].get("reference_image", "N/A")
            print(f"  {sku}: {ref}")
        return 0

    # Initialize clients
    clients = {
        "openai": get_openai_client(),
        "anthropic": get_anthropic_client(),
        "gemini": get_gemini_client(),
    }
    active = [k for k, v in clients.items() if v]
    log.info("Active vision models: %s", active)

    if len(active) < 2:
        log.error("Need at least 2 vision models for consensus — only have %d", len(active))
        return 1

    # Process each SKU
    for sku in skus:
        ref_path = PROJECT_ROOT / refs[sku]["reference_image"]
        if not ref_path.exists():
            log.warning("Reference image missing: %s", ref_path)
            continue

        dna = extract_dna(sku, ref_path, clients)
        save_dna(dna, sku)
        if args.verbose:
            print_summary(dna)

    log.info("DONE — processed %d SKUs", len(skus))
    return 0


if __name__ == "__main__":
    sys.exit(main())
