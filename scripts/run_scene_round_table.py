#!/usr/bin/env python3
"""
LLM Round Table Scene Generation Competition
=============================================

All 6 LLM providers compete to design immersive Three.js scenes for each
SkyyRose collection. Winner per collection gets implemented.

Providers: OpenAI, Anthropic, Google, Mistral, Cohere, Groq
Scoring: Brand alignment, Visual creativity, Technical feasibility,
         Luxury aesthetics, Interactivity depth, Performance conscious
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env
from dotenv import load_dotenv

load_dotenv()

from llm.base import Message
from llm.creative_judge import CreativeJudge, Verdict
from llm.providers.anthropic import AnthropicClient
from llm.providers.cohere import CohereClient
from llm.providers.google import GoogleClient
from llm.providers.groq import GroqClient
from llm.providers.openai import OpenAIClient
from llm.round_table import LLMProvider, LLMRoundTable

# Brand DNA for each collection
BRAND_DNA = {
    "signature": {
        "theme": "Timeless Essentials",
        "mood": "Golden hour luxury garden, elegant pedestals, floating roses",
        "colors": {
            "primary": "#B76E79",  # Rose Gold
            "secondary": "#D4AF37",  # Gold
            "accent": "#F5F5F0",  # Ivory
        },
        "style": "Classic, versatile, refined luxury",
    },
    "black-rose": {
        "theme": "Limited Edition Exclusivity",
        "mood": "Gothic night garden, moonlit, ethereal mystery",
        "colors": {
            "primary": "#C0C0C0",  # Cosmic Silver
            "secondary": "#0A0A0A",  # Obsidian
            "accent": "#0a0a1a",  # Deep Blue
        },
        "style": "Mysterious, sophisticated, rare",
    },
    "love-hurts": {
        "theme": "Feel Everything",
        "mood": "Enchanted castle ballroom, Beauty & Beast inspiration",
        "colors": {
            "primary": "#DC143C",  # Crimson Red
            "secondary": "#800080",  # Deep Purple
            "accent": "#FFD700",  # Candlelight Gold
        },
        "style": "Passionate, vulnerable, powerful",
    },
}

SCENE_PROMPT_TEMPLATE = """
You are a creative director designing an immersive 3D web experience for SkyyRose's {collection} COLLECTION.

## Brand DNA
- Theme: "{theme}"
- Mood: {mood}
- Colors: Primary {primary}, Secondary {secondary}, Accent {accent}
- Style: {style}

## Design Requirements
Create a detailed Three.js scene specification that includes:

1. **Environment Design**
   - Background (gradient, skybox, or procedural)
   - Atmospheric effects (fog, particles, lighting)
   - Ground/floor treatment

2. **Hero Scene Concept**
   - Main visual focal point
   - How products are showcased
   - Signature element that defines this collection

3. **Lighting Setup**
   - Light types (ambient, directional, point, spot)
   - Color temperatures matching brand palette
   - Shadow settings for luxury feel

4. **Camera Configuration**
   - Initial position and target
   - Orbit controls settings
   - Cinematic movement suggestions

5. **Interactive Elements**
   - Hotspots for products (position, behavior)
   - Hover/click animations
   - Navigation elements

6. **Particle Systems**
   - Type (petals, sparkles, fog wisps)
   - Count, size, movement patterns
   - Colors matching brand

7. **Post-Processing Effects**
   - Bloom settings
   - Color grading
   - Any special effects

8. **Performance Considerations**
   - Mobile optimization notes
   - LOD suggestions
   - Texture size recommendations

## Output Format
Return a complete JSON specification:
```json
{{
  "collection": "{collection}",
  "scene_name": "your creative name",
  "environment": {{
    "background": {{}},
    "fog": {{}},
    "ground": {{}}
  }},
  "lighting": [
    {{"type": "ambient", "color": "#...", "intensity": 0.5}},
    ...
  ],
  "camera": {{
    "position": [x, y, z],
    "target": [x, y, z],
    "fov": 60,
    "controls": {{}}
  }},
  "hero_element": {{
    "type": "...",
    "geometry": {{}},
    "material": {{}},
    "animation": {{}}
  }},
  "product_displays": [
    {{"position": [x, y, z], "rotation": [x, y, z], "scale": 1}}
  ],
  "particles": {{
    "type": "...",
    "count": 100,
    "size": 0.1,
    "colors": ["#..."],
    "movement": {{}}
  }},
  "postprocessing": {{
    "bloom": {{}},
    "colorGrading": {{}}
  }},
  "interactions": [
    {{"trigger": "hover", "target": "...", "action": "..."}}
  ],
  "performance": {{
    "mobile_notes": "...",
    "recommended_quality": "..."
  }}
}}
```

Be creative, luxurious, and technically precise. This will be directly implemented in Three.js.
"""

SCORING_WEIGHTS = {
    "brand_alignment": 0.25,
    "visual_creativity": 0.20,
    "technical_feasibility": 0.20,
    "luxury_aesthetics": 0.15,
    "interactivity_depth": 0.10,
    "performance_conscious": 0.10,
}


async def elite_judge_responses(
    prompt: str,
    responses: list[tuple[str, str]],  # [(provider, response), ...]
    collection: str,
) -> list[dict[str, Any]]:
    """
    Use the Elite CreativeJudge to score all responses.

    Three-pillar evaluation:
    1. PROMPT_QUALITY (20%) - Was the agent set up to succeed?
    2. EXECUTION_QUALITY (35%) - Did they deliver what was asked?
    3. BRAND_DNA (45%) - Will customers recognize SkyyRose?

    Hardened for production reliability.
    """
    print("\n  🏛️ Elite Judge Evaluation (3-Pillar LLM-as-Judge)")

    if not responses:
        print("  ⚠️ No responses to judge")
        return []

    # Validate responses format
    valid_responses = []
    for item in responses:
        if isinstance(item, tuple) and len(item) == 2:
            provider, content = item
            if provider and content:
                valid_responses.append((str(provider), str(content)))

    if not valid_responses:
        print("  ⚠️ No valid responses after filtering")
        return []

    print(f"  📝 Judging {len(valid_responses)} valid responses")

    try:
        judge = CreativeJudge(
            judge_provider="anthropic",  # Claude as judge
            judge_model="claude-sonnet-4-20250514",
        )
        await judge.initialize()

        results = await judge.compare(
            prompt=prompt,
            responses=valid_responses,
            task_type="three_js_scene_design",
            collection=collection,
        )
    except Exception as e:
        print(f"  ❌ Judge initialization/comparison failed: {e}")
        import traceback

        traceback.print_exc()
        return []

    if not results:
        print("  ⚠️ Judge returned no results")
        return []

    if not isinstance(results, list):
        print(f"  ⚠️ Judge returned unexpected type: {type(results)}")
        return []

    print(f"\n  📊 Elite Judging Results ({len(results)} evaluations):")
    scored = []

    for rank, item in enumerate(results, 1):
        try:
            # Defensive unpacking
            if not isinstance(item, tuple) or len(item) != 2:
                print(f"    ⚠️ Skipping malformed result at rank {rank}: {type(item)}")
                continue

            provider, verdict = item

            # Validate verdict object
            if verdict is None:
                print(f"    ⚠️ Skipping null verdict for {provider}")
                continue

            # Safe attribute access
            verdict_score = getattr(verdict, "total_score", 0.0) or 0.0
            verdict_enum = getattr(verdict, "verdict", Verdict.FAIL)
            verdict_pillars = getattr(verdict, "pillars", []) or []
            verdict_summary = getattr(verdict, "summary", "") or ""
            verdict_recommendations = getattr(verdict, "recommendations", []) or []

            verdict_emoji = {
                Verdict.ELITE: "🏆",
                Verdict.EXCELLENT: "⭐",
                Verdict.GOOD: "✅",
                Verdict.NEEDS_WORK: "⚠️",
                Verdict.FAIL: "❌",
            }.get(verdict_enum, "❓")

            verdict_value = (
                verdict_enum.value if hasattr(verdict_enum, "value") else str(verdict_enum)
            )

            print(
                f"    {rank}. {provider}: {verdict_score:.1f}/100 {verdict_emoji} {verdict_value}"
            )

            # Show pillar breakdown - with guards
            if isinstance(verdict_pillars, list):
                for pillar in verdict_pillars:
                    pillar_name = getattr(pillar, "pillar", "unknown")
                    pillar_score = getattr(pillar, "pillar_score", 0.0) or 0.0
                    print(f"       └─ {pillar_name}: {pillar_score:.1f}")

            # Build scored entry with all guards
            pillars_dict = {}
            if isinstance(verdict_pillars, list):
                for p in verdict_pillars:
                    p_name = getattr(p, "pillar", "unknown")
                    p_score = getattr(p, "pillar_score", 0.0) or 0.0
                    pillars_dict[p_name] = p_score

            scored.append(
                {
                    "rank": rank,
                    "provider": str(provider),
                    "total_score": float(verdict_score),
                    "verdict": verdict_value,
                    "pillars": pillars_dict,
                    "summary": str(verdict_summary) if verdict_summary else "",
                    "recommendations": (
                        list(verdict_recommendations) if verdict_recommendations else []
                    ),
                }
            )

        except Exception as item_error:
            print(f"    ❌ Error processing result {rank}: {item_error}")
            import traceback

            traceback.print_exc()
            continue

    print(f"  ✅ Successfully scored {len(scored)} responses")
    return scored


async def run_collection_competition(
    round_table: LLMRoundTable,
    collection: str,
    use_elite_judge: bool = True,
) -> dict[str, Any]:
    """
    Run Round Table competition for a single collection.

    Args:
        round_table: The LLM Round Table instance
        collection: Collection name (signature, black-rose, love-hurts)
        use_elite_judge: If True, use 3-pillar LLM-as-judge scoring
    """
    brand = BRAND_DNA[collection]

    prompt = SCENE_PROMPT_TEMPLATE.format(
        collection=collection.upper().replace("-", " "),
        theme=brand["theme"],
        mood=brand["mood"],
        primary=brand["colors"]["primary"],
        secondary=brand["colors"]["secondary"],
        accent=brand["colors"]["accent"],
        style=brand["style"],
    )

    print(f"\n{'=' * 60}")
    print(f"COMPETITION: {collection.upper()}")
    print(f"{'=' * 60}")
    print("Prompting all LLMs in parallel...")

    try:
        result = await round_table.compete(
            prompt=prompt,
            task_id=f"scene_design_{collection}",
            context={
                "category": "creative_design",
                "collection": collection,
                "brand_dna": brand,
            },
            persist=True,  # Save to Neon PostgreSQL
        )

        print(f"\n  ⏱️ Generation completed in {result.total_duration_ms:.0f}ms")
        print(f"  📝 Received {len(result.entries)} responses")

        # Collect responses for elite judging
        responses = []
        for entry in result.entries:
            if entry.response and entry.response.content:
                responses.append((entry.provider.value, entry.response.content))

        if use_elite_judge and responses:
            # Use Elite 3-Pillar Judge
            try:
                elite_results = await elite_judge_responses(
                    prompt=prompt,
                    responses=responses,
                    collection=collection,
                )
            except Exception as judge_error:
                print(f"  ⚠️ Elite judging failed: {judge_error}")
                import traceback

                traceback.print_exc()
                elite_results = []

            # Find winner from elite judging - with defensive guards
            if not elite_results or not isinstance(elite_results, list):
                print("  ⚠️ No elite results - falling back to heuristic")
                elite_results = []

            winner = elite_results[0] if elite_results else None

            if winner is None:
                # Fallback to heuristic scoring if elite judging failed
                print("  ⚠️ Elite judging returned no winner - using heuristic")
                return {
                    "collection": collection,
                    "scoring_method": "heuristic_fallback",
                    "winner": {
                        "provider": result.winner.provider.value,
                        "score": result.winner.total_score,
                        "response": result.winner.response.content,
                    },
                    "rankings": [
                        {
                            "rank": e.rank,
                            "provider": e.provider.value,
                            "score": e.total_score,
                        }
                        for e in result.entries
                    ],
                    "duration_ms": result.total_duration_ms,
                    "error_note": "Elite judging failed, using heuristic fallback",
                }

            # Safe access with guards
            winner_provider = (
                winner.get("provider", "unknown") if isinstance(winner, dict) else "unknown"
            )
            winner_score = winner.get("total_score", 0.0) if isinstance(winner, dict) else 0.0
            winner_verdict = (
                winner.get("verdict", "UNKNOWN") if isinstance(winner, dict) else "UNKNOWN"
            )

            print(
                f"\n  🏆 ELITE WINNER: {winner_provider} ({winner_score:.1f}/100) - {winner_verdict}"
            )

            # Safe summary extraction
            summary = winner.get("summary", "") if isinstance(winner, dict) else ""
            if isinstance(summary, dict):
                summary = str(summary.get("recommendation", summary))
            summary = str(summary)[:100] if summary else ""
            print(f"     Summary: {summary}...")

            # Find the response content for the winner - safe access
            winner_response = next((r for p, r in responses if p == winner_provider), None)

            return {
                "collection": collection,
                "scoring_method": "elite_3_pillar_judge",
                "winner": {
                    "provider": winner_provider,
                    "score": winner_score,
                    "verdict": winner_verdict,
                    "pillars": winner.get("pillars", {}) if isinstance(winner, dict) else {},
                    "summary": winner.get("summary", "") if isinstance(winner, dict) else "",
                    "recommendations": (
                        winner.get("recommendations", []) if isinstance(winner, dict) else []
                    ),
                    "response": winner_response,
                },
                "rankings": elite_results,
                "duration_ms": result.total_duration_ms,
                "heuristic_rankings": [
                    {
                        "rank": e.rank,
                        "provider": e.provider.value,
                        "heuristic_score": e.total_score,
                    }
                    for e in result.entries
                ],
            }
        else:
            # Fallback to heuristic scoring
            print(f"\n  Results for {collection} (heuristic scoring):")
            print(f"  Winner: {result.winner.provider.value}")
            print(f"  Score: {result.winner.total_score:.2f}")

            return {
                "collection": collection,
                "scoring_method": "heuristic",
                "winner": {
                    "provider": result.winner.provider.value,
                    "score": result.winner.total_score,
                    "response": result.winner.response.content,
                },
                "rankings": [
                    {
                        "rank": e.rank,
                        "provider": e.provider.value,
                        "score": e.total_score,
                    }
                    for e in result.entries
                ],
                "duration_ms": result.total_duration_ms,
            }

    except Exception as e:
        import traceback

        print(f"  ERROR: {e}")
        traceback.print_exc()
        return {
            "collection": collection,
            "error": str(e),
        }


async def main():
    print("=" * 60)
    print("LLM ROUND TABLE: Scene Generation Competition")
    print("=" * 60)
    print(f"Collections: {list(BRAND_DNA.keys())}")
    print(f"Scoring weights: {SCORING_WEIGHTS}")

    # Check API keys
    api_keys = {
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "Anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "Google": bool(os.getenv("GOOGLE_API_KEY")),
        "Mistral": bool(os.getenv("MISTRAL_API_KEY")),
        "Cohere": bool(os.getenv("COHERE_API_KEY")),
        "Groq": bool(os.getenv("GROQ_API_KEY")),
    }
    print(f"\nAPI Keys: {sum(api_keys.values())}/6 available")
    for name, available in api_keys.items():
        print(f"  {'✓' if available else '✗'} {name}")

    available_count = sum(api_keys.values())
    if available_count < 2:
        print("\nERROR: Need at least 2 API keys for competition")
        return

    # Initialize Round Table
    print("\nInitializing Round Table...")
    round_table = LLMRoundTable()
    await round_table.initialize()

    # Initialize LLM clients
    clients = {}
    if api_keys["OpenAI"]:
        clients[LLMProvider.GPT4] = OpenAIClient()
    if api_keys["Anthropic"]:
        clients[LLMProvider.CLAUDE] = AnthropicClient()
    if api_keys["Google"]:
        clients[LLMProvider.GEMINI] = GoogleClient()
    # SKIP Mistral - API key invalid (2026-01-14)
    # if api_keys["Mistral"]:
    #     clients[LLMProvider.MISTRAL] = MistralClient()
    if api_keys["Cohere"]:
        clients[LLMProvider.COHERE] = CohereClient()
    if api_keys["Groq"]:
        clients[LLMProvider.LLAMA] = GroqClient()

    # Register providers with generator functions
    async def create_generator(client):
        async def generator(prompt: str, context: dict | None = None, **kwargs):
            # Accept but ignore tools/tool_choice kwargs (not needed for scene generation)
            messages = [Message.user(prompt)]
            return await client.complete(messages=messages, max_tokens=4096)

        return generator

    for provider, client in clients.items():
        gen = await create_generator(client)
        round_table.register_provider(provider, gen)

    print(f"Registered {len(clients)} providers: {[p.value for p in clients]}")

    results = {}

    # Run competition for each collection with ELITE JUDGING
    print("\n" + "=" * 60)
    print("🏛️ ELITE 3-PILLAR JUDGING ENABLED")
    print("=" * 60)
    print("Pillars: PROMPT (20%) | EXECUTION (35%) | BRAND DNA (45%)")
    print("=" * 60)

    for collection in BRAND_DNA:
        result = await run_collection_competition(
            round_table,
            collection,
            use_elite_judge=True,  # Enable elite judging
        )
        results[collection] = result

    # Save results
    output_path = Path("assets/ai-enhanced-images/ROUND_TABLE_ELITE_RESULTS.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "scoring_method": "elite_3_pillar_judge",
                "pillar_weights": {
                    "PROMPT_QUALITY": 0.20,
                    "EXECUTION_QUALITY": 0.35,
                    "BRAND_DNA": 0.45,
                },
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n{'=' * 60}")
    print("🏆 ELITE COMPETITION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Results saved to: {output_path}")

    # Summary with verdicts
    print("\n🏆 ELITE WINNERS:")
    print("-" * 50)
    for collection, result in results.items():
        if "error" not in result:
            winner = result["winner"]
            score = winner.get("score", 0)
            verdict = winner.get("verdict", "N/A")
            provider = winner.get("provider", "unknown")

            # Emoji for verdict
            verdict_emoji = {
                "ELITE": "🏆",
                "EXCELLENT": "⭐",
                "GOOD": "✅",
                "NEEDS_WORK": "⚠️",
                "FAIL": "❌",
            }.get(verdict, "❓")

            print(f"  {collection.upper()}")
            print(f"    Winner: {provider}")
            print(f"    Score: {score:.1f}/100 {verdict_emoji} {verdict}")

            # Show pillar breakdown if available
            pillars = winner.get("pillars", {})
            if pillars:
                print("    Pillars:")
                for pillar, pillar_score in pillars.items():
                    print(f"      └─ {pillar}: {pillar_score:.1f}")
            print()
        else:
            print(f"  {collection.upper()}: ERROR - {result['error']}\n")

    await round_table.close()


if __name__ == "__main__":
    asyncio.run(main())
