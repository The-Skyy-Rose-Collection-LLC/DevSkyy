#!/usr/bin/env python3
"""
SkyyRose Content Agent — Google ADK-powered catalog copywriter.

Manages product-content.json: reads products, generates brand-voice copy,
writes it back, and audits quality via multi-turn agentic tool-calling.

Usage:
    python skyyrose_content_agent.py refresh-product br-001
    python skyyrose_content_agent.py refresh-collection black-rose
    python skyyrose_content_agent.py generate-social lh-001 instagram
    python skyyrose_content_agent.py audit
    python skyyrose_content_agent.py audit --field tiktok
    python skyyrose_content_agent.py interactive
"""

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

# Load .env before ADK imports so GEMINI_API_KEY is set.
# Load order: local .env first (project-specific settings), then gemini/.env
# with override=True so the real API keys always win over placeholders.
from dotenv import load_dotenv

_LOCAL_ENV = Path(__file__).parent / ".env"
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=False)

_GEMINI_ENV = Path(__file__).parent.parent / "gemini" / ".env"
if _GEMINI_ENV.exists():
    load_dotenv(_GEMINI_ENV, override=True)  # real keys win over placeholders

# ADK imports (after env is loaded)
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types as genai_types

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

APP_NAME = "skyyrose_content_agent"
MODEL = os.getenv("SKYYROSE_MODEL", "gemini-2.0-flash")
PRODUCT_JSON_PATH = Path(__file__).parent / "assets" / "data" / "product-content.json"

WRITABLE_FIELDS = {"description", "short_description", "seo_meta", "instagram", "tiktok"}
READ_ONLY_FIELDS = {"name", "collection"}

FIELD_MIN_CHARS = {
    "description": 400,
    "short_description": 80,
    "seo_meta": 60,
    "instagram": 100,
    "tiktok": 40,
}

# ---------------------------------------------------------------------------
# Brand guidelines
# ---------------------------------------------------------------------------

BRAND_GUIDELINES = {
    "brand": "SkyyRose",
    "origin": "Bay Area / Oakland, California",
    "taglines": [
        "Where darkness blooms.",
        "Embrace the thorns, cherish the bloom.",
        "Luxury born from the streets.",
    ],
    "collections": {
        "black-rose": {
            "voice": "Gothic luxury. Dark romance. Poetic and ethereal with an edge of defiance.",
            "vocabulary": ["twilight", "shadows", "embroidered", "ethereal", "thorns",
                           "bloom", "darkness", "gothic", "enigmatic", "mystic",
                           "enchanting", "opulent", "defiant", "moonlight", "aura"],
            "hashtags": [
                "#SkyyRose", "#BlackRoseCollection", "#GothicLuxury", "#DarkRomance",
                "#StreetwearFashion", "#BayAreaFashion", "#EmbroideredRose",
                "#LuxuryStreetwear", "#FashionStatement", "#MysteryStyle",
                "#DarkAesthetic", "#WearableArt",
            ],
            "tone": "Poetic, evocative, slightly melancholic but empowering.",
        },
        "love-hurts": {
            "voice": "Raw street intensity. Gritty authenticity rooted in Oakland.",
            "vocabulary": ["streets", "grit", "fire", "passion", "Oakland", "concrete",
                           "raw", "hustle", "grind", "authentic", "real", "blood",
                           "sweat", "resilience", "bay"],
            "hashtags": [
                "#SkyyRose", "#LoveHurts", "#OaklandFashion", "#BayAreaStyle",
                "#StreetwearFashion", "#GritAndGrace", "#RealStyle", "#UrbanLuxury",
                "#Authentic", "#BayArea", "#OaklandProud",
            ],
            "tone": "Direct, intense, emotionally honest. Pride in origin, unapologetic.",
        },
        "signature": {
            "voice": "Elevated editorial. Couture-level prestige for the discerning.",
            "vocabulary": ["opulent", "couture", "prestige", "commanding", "refined",
                           "bespoke", "distinguished", "luxurious", "tailored",
                           "exclusive", "premier", "exceptional", "artisanal"],
            "hashtags": [
                "#SkyyRose", "#SignatureCollection", "#LuxuryFashion", "#Couture",
                "#ElevatedStyle", "#BayAreaLuxury", "#FashionForward",
                "#SignatureStyle", "#ExclusiveFashion", "#Prestige",
            ],
            "tone": "Authoritative, refined, aspirational. Confident without being boastful.",
        },
    },
    "forbidden_words": [
        "cheap", "affordable", "budget", "sale", "discount", "basic",
        "simple", "ordinary", "average", "normal", "regular", "plain",
    ],
    "field_guidelines": {
        "description": (
            "400–800 chars. Rich, immersive narrative. Lead with atmosphere, "
            "then garment details, then call to action. One powerful closing statement."
        ),
        "short_description": (
            "80–160 chars. One punchy sentence capturing the essence. "
            "Must include collection name and key design element."
        ),
        "seo_meta": (
            "60–160 chars. Keyword-rich. Include brand name 'SkyyRose', "
            "product name, and one differentiating phrase. Action CTA at end."
        ),
        "instagram": (
            "100–300 chars + hashtags. Evocative storytelling hook. "
            "2–3 sentences + line break + 10–12 hashtags from collection bank."
        ),
        "tiktok": (
            "40–150 chars. Punchy, trend-aware, energetic. "
            "1–2 sentences max. 3–5 hashtags only. Emoji encouraged."
        ),
    },
}

# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def get_product_catalog() -> dict:
    """Return the full product catalog as a dict keyed by SKU."""
    try:
        data = json.loads(PRODUCT_JSON_PATH.read_text(encoding="utf-8"))
        return {"status": "ok", "catalog": data, "count": len(data)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def get_product(sku: str) -> dict:
    """Return a single product by SKU; error if not found."""
    try:
        data = json.loads(PRODUCT_JSON_PATH.read_text(encoding="utf-8"))
        sku = sku.strip().lower()
        if sku not in data:
            return {
                "status": "error",
                "error": f"SKU '{sku}' not found. Available: {sorted(data.keys())}",
            }
        return {"status": "ok", "sku": sku, "product": data[sku]}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def get_collection_products(collection: str) -> dict:
    """Return all products in a collection (auto-normalizes to lowercase-hyphen)."""
    try:
        # Normalize: "Black Rose" → "black-rose"
        normalized = collection.strip().lower().replace(" ", "-")
        valid = {"black-rose", "love-hurts", "signature"}
        if normalized not in valid:
            return {
                "status": "error",
                "error": f"Unknown collection '{collection}'. Valid: {sorted(valid)}",
            }
        data = json.loads(PRODUCT_JSON_PATH.read_text(encoding="utf-8"))
        filtered = {
            sku: product
            for sku, product in data.items()
            if product.get("collection") == normalized
        }
        return {
            "status": "ok",
            "collection": normalized,
            "products": filtered,
            "count": len(filtered),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def get_brand_guidelines() -> dict:
    """Return the SkyyRose brand guidelines including collection voices, vocabulary, and field constraints."""
    return {"status": "ok", "guidelines": BRAND_GUIDELINES}


def update_product_field(sku: str, field: str, content: str) -> dict:
    """Atomically write one field of a product to product-content.json."""
    sku = sku.strip().lower()
    field = field.strip().lower()

    if field in READ_ONLY_FIELDS:
        return {
            "status": "error",
            "error": f"Field '{field}' is read-only. Writable fields: {sorted(WRITABLE_FIELDS)}",
        }
    if field not in WRITABLE_FIELDS:
        return {
            "status": "error",
            "error": f"Unknown field '{field}'. Writable fields: {sorted(WRITABLE_FIELDS)}",
        }

    try:
        data = json.loads(PRODUCT_JSON_PATH.read_text(encoding="utf-8"))
        if sku not in data:
            return {
                "status": "error",
                "error": f"SKU '{sku}' not found.",
            }

        old_value = data[sku].get(field, "")
        data[sku][field] = content

        # Atomic write: write to .tmp then rename
        tmp_path = PRODUCT_JSON_PATH.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp_path.replace(PRODUCT_JSON_PATH)

        return {
            "status": "ok",
            "sku": sku,
            "field": field,
            "old_length": len(old_value),
            "new_length": len(content),
            "preview": content[:120] + ("..." if len(content) > 120 else ""),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def list_products_needing_refresh(field: str) -> dict:
    """Audit all products for a field; flag those with missing or short content."""
    field = field.strip().lower()
    if field not in WRITABLE_FIELDS:
        return {
            "status": "error",
            "error": f"Unknown field '{field}'. Writable fields: {sorted(WRITABLE_FIELDS)}",
        }

    try:
        data = json.loads(PRODUCT_JSON_PATH.read_text(encoding="utf-8"))
        min_chars = FIELD_MIN_CHARS.get(field, 1)
        needs_refresh = []
        ok_products = []

        for sku, product in sorted(data.items()):
            value = product.get(field, "")
            char_count = len(value)
            entry = {
                "sku": sku,
                "name": product.get("name", ""),
                "collection": product.get("collection", ""),
                "char_count": char_count,
                "min_required": min_chars,
            }
            if char_count < min_chars:
                entry["issue"] = "missing" if char_count == 0 else "too_short"
                needs_refresh.append(entry)
            else:
                ok_products.append(entry)

        return {
            "status": "ok",
            "field": field,
            "min_chars": min_chars,
            "needs_refresh_count": len(needs_refresh),
            "ok_count": len(ok_products),
            "needs_refresh": needs_refresh,
            "ok": ok_products,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


TOOL_FUNCTIONS = [
    get_product_catalog,
    get_product,
    get_collection_products,
    get_brand_guidelines,
    update_product_field,
    list_products_needing_refresh,
]

# ---------------------------------------------------------------------------
# System instruction
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """You are the SkyyRose Content Director — an AI copywriter embedded in the SkyyRose luxury fashion house, headquartered in the Bay Area / Oakland, California.

Your sole mission is to create, refine, and maintain the product copy in the SkyyRose catalog (product-content.json). You have direct tool access to read products, write updated copy, and audit content quality.

## Collections

- **black-rose**: Gothic luxury. Dark romance. Ethereal, poetic, defiant. Vocabulary: twilight, shadows, embroidered, ethereal, thorns, bloom.
- **love-hurts**: Raw street intensity. Gritty Oakland authenticity. Direct and emotionally honest. Vocabulary: streets, grit, fire, passion, Oakland, concrete.
- **signature**: Elevated editorial. Couture prestige. Authoritative and aspirational. Vocabulary: opulent, couture, prestige, commanding, refined, bespoke.

## Tool Protocol

1. **Always call `get_brand_guidelines()` first** in any new session before generating copy.
2. **Always call `get_product(sku)`** before rewriting a product — preserve what works, improve what's weak.
3. **Generate → preview → `update_product_field()` → confirm** for every field change.
4. **Never update `name` or `collection`** — these are read-only identifiers.
5. For batch operations, use `get_collection_products(collection)` rather than loading the full catalog.

## Field Requirements

| Field | Min | Max | Style |
|-------|-----|-----|-------|
| description | 400 | 800 | Rich narrative: atmosphere → garment details → CTA |
| short_description | 80 | 160 | One punchy sentence with collection name + key design element |
| seo_meta | 60 | 160 | Keyword-rich, brand name, differentiating phrase, CTA |
| instagram | 100 | 300 | Hook → 2-3 sentences + line break + 10-12 hashtags |
| tiktok | 40 | 150 | Punchy 1-2 sentences + 3-5 hashtags + emoji |

## Writing Standards

- Never use forbidden words: cheap, affordable, budget, sale, discount, basic, simple, ordinary, average, normal, regular, plain.
- Every piece of copy must feel like it belongs in the luxury fashion world — elevated, intentional, evocative.
- Descriptions should create atmosphere first, then reveal the garment. The reader should feel the piece before they see it.
- Social copy should speak to the wearer's identity and aspiration, not just the product features.
- Oakland and Bay Area roots are a point of pride — not gritty for grit's sake, but authentic luxury born from the streets.

After completing any write operation, always confirm the update with a brief summary of what changed and why the new copy is stronger."""

# ---------------------------------------------------------------------------
# Agent + Runner construction
# ---------------------------------------------------------------------------


def build_agent() -> LlmAgent:
    """Build the SkyyRose Content Director LlmAgent."""
    return LlmAgent(
        name="skyyrose_content_director",
        model=MODEL,
        instruction=SYSTEM_INSTRUCTION,
        tools=[FunctionTool(fn) for fn in TOOL_FUNCTIONS],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=4096,
        ),
    )


def build_runner(agent: LlmAgent, session_svc: InMemorySessionService) -> Runner:
    """Build the ADK Runner."""
    return Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_svc,
    )


def run_turn(
    runner: Runner,
    session_svc: InMemorySessionService,
    message: str,
    session_id: str,
    user_id: str = "cli-user",
) -> str:
    """Send one message and return the final text response."""
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )
    response_text = ""
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            # Agent may end on a tool call with no text part — scan all parts
            if event.content and event.content.parts:
                texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                response_text = "\n".join(texts)
            break
    return response_text


def make_session(session_svc: InMemorySessionService, user_id: str = "cli-user") -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    session_svc.create_session_sync(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    return session_id


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


def cmd_refresh_product(sku: str) -> None:
    """Refresh all writable fields for a single product."""
    print(f"Refreshing product: {sku}")
    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)
    session_id = make_session(session_svc)

    message = (
        f"Please refresh all content fields for product SKU '{sku}'. "
        f"Start by calling get_brand_guidelines() and get_product('{sku}'). "
        f"Then generate improved copy for description, short_description, seo_meta, "
        f"instagram, and tiktok — saving each with update_product_field(). "
        f"Preserve the voice and any content that's already strong."
    )
    response = run_turn(runner, session_svc, message, session_id)
    print(response)


def cmd_refresh_collection(collection: str, delay: float = 8.0) -> None:
    """Refresh all products in a collection one-by-one to avoid rate limits."""
    normalized = collection.strip().lower().replace(" ", "-")
    result = get_collection_products(normalized)
    if result.get("status") == "error":
        print(f"Error: {result['error']}")
        sys.exit(1)

    skus = sorted(result["products"].keys())
    total = len(skus)
    print(f"Refreshing {total} products in '{normalized}' ({delay}s between each)...\n")

    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)

    for i, sku in enumerate(skus, 1):
        print(f"[{i}/{total}] {sku}")
        session_id = make_session(session_svc)
        message = (
            f"Refresh all content fields for product SKU '{sku}'. "
            f"Call get_brand_guidelines() and get_product('{sku}') first. "
            f"Generate improved description, short_description, seo_meta, instagram, and tiktok "
            f"— saving each with update_product_field(). Maintain the {normalized} brand voice."
        )
        response = run_turn(runner, session_svc, message, session_id)
        print(response)
        if i < total:
            print(f"  (waiting {delay}s...)\n")
            time.sleep(delay)

    print(f"\nDone. {total} products refreshed.")


def cmd_generate_social(sku: str, platform: str) -> None:
    """Generate and save social copy for one product on one platform."""
    platform = platform.lower()
    if platform not in {"instagram", "tiktok"}:
        print(f"Error: platform must be 'instagram' or 'tiktok', got '{platform}'")
        sys.exit(1)

    print(f"Generating {platform} copy for {sku}")
    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)
    session_id = make_session(session_svc)

    message = (
        f"Generate {platform} copy for product SKU '{sku}'. "
        f"Call get_brand_guidelines() and get_product('{sku}') first. "
        f"Write platform-native copy that fits the collection's brand voice, "
        f"then save it with update_product_field('{sku}', '{platform}', <content>). "
        f"After saving, reply with the final saved copy in full so I can read it."
    )
    response = run_turn(runner, session_svc, message, session_id)
    print(response)


def cmd_audit(field: str | None = None) -> None:
    """Audit content quality across the catalog."""
    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)
    session_id = make_session(session_svc)

    if field:
        print(f"Auditing field: {field}")
        message = (
            f"READ-ONLY AUDIT — do NOT call update_product_field(). "
            f"Run a quality audit for the '{field}' field across all products. "
            f"Call list_products_needing_refresh('{field}') and present the results "
            f"in a clear summary: how many need work, which SKUs, and why. "
            f"Recommend which to fix first. Do not write any content."
        )
    else:
        print("Running full catalog audit across all writable fields...")
        fields = sorted(WRITABLE_FIELDS)
        message = (
            f"READ-ONLY AUDIT — do NOT call update_product_field(). "
            f"Run a complete quality audit across all writable fields: {fields}. "
            f"Call list_products_needing_refresh() for each field, then present "
            f"a prioritized action plan: which products need the most work, "
            f"which fields are most incomplete, and recommended fix order. "
            f"Report only — do not generate or write any content."
        )
    response = run_turn(runner, session_svc, message, session_id)
    print(response)


def cmd_interactive() -> None:
    """Start an interactive multi-turn session."""
    print("SkyyRose Content Agent — Interactive Mode")
    print("Type 'exit' or 'quit' to end the session.\n")

    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)
    session_id = make_session(session_svc)
    user_id = "cli-user"

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Session ended.")
            break

        response = run_turn(runner, session_svc, user_input, session_id, user_id)
        print(f"\nAgent: {response}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SkyyRose Content Agent — Google ADK catalog copywriter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # refresh-product
    p_refresh = subparsers.add_parser("refresh-product", help="Refresh all fields for one product")
    p_refresh.add_argument("sku", help="Product SKU (e.g. br-001)")

    # refresh-collection
    p_collection = subparsers.add_parser(
        "refresh-collection", help="Refresh all products in a collection"
    )
    p_collection.add_argument(
        "collection", help="Collection name (black-rose | love-hurts | signature)"
    )

    # generate-social
    p_social = subparsers.add_parser(
        "generate-social", help="Generate social copy for one product"
    )
    p_social.add_argument("sku", help="Product SKU")
    p_social.add_argument("platform", help="Platform (instagram | tiktok)")

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit content quality")
    p_audit.add_argument(
        "--field",
        default=None,
        help="Audit a specific field only (description | short_description | seo_meta | instagram | tiktok)",
    )

    # interactive
    subparsers.add_parser("interactive", help="Start an interactive multi-turn session")

    args = parser.parse_args()

    # Validate API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("AIza..."):
        print(
            "Error: GEMINI_API_KEY not set or is a placeholder.\n"
            "Set it in skyyrose/.env or export GEMINI_API_KEY=<your-key>",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.command == "refresh-product":
        cmd_refresh_product(args.sku)
    elif args.command == "refresh-collection":
        cmd_refresh_collection(args.collection)
    elif args.command == "generate-social":
        cmd_generate_social(args.sku, args.platform)
    elif args.command == "audit":
        cmd_audit(args.field)
    elif args.command == "interactive":
        cmd_interactive()


if __name__ == "__main__":
    main()
