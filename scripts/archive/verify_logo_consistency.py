#!/usr/bin/env python3
"""
Logo Consistency Verification Script
=====================================

Uses Gemini Vision API + VisualComparisonEngine to verify that AI-enhanced
product images have logos consistent with the original brand assets.

Per plan requirements:
- Gemini for visual analysis
- HuggingFace/local models for image comparison metrics
- 90% quality threshold from AssetQualityGate
"""

import argparse
import asyncio
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from imagery.visual_comparison import VisualComparisonEngine

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

# Logo files by collection
LOGO_FILES = {
    "signature": [
        Path("frontend/public/assets/logos/signature-rose-rosegold.png"),
        Path("frontend/public/assets/logos/sr-monogram-rosegold.png"),
        Path("wordpress/skyyrose-immersive/assets/images/logos/signature-logo.png"),
    ],
    "black-rose": [
        Path("frontend/public/assets/logos/black-rose-trophy-cosmic.png"),
        Path("wordpress/skyyrose-immersive/assets/images/logos/blackrose-logo.jpg"),
    ],
    "love-hurts": [
        Path("frontend/public/assets/logos/love-hurts-text-logo.png"),
        Path("frontend/public/assets/logos/love-hurts-trophy-red.png"),
        Path("wordpress/skyyrose-immersive/assets/images/logos/lovehurts-logo.jpg"),
    ],
}

# Enhanced images directory
ENHANCED_DIR = Path("assets/ai-enhanced-images")

# Brand colors for verification
BRAND_COLORS = {
    "signature": {
        "primary": "#B76E79",  # Rose Gold
        "secondary": "#D4AF37",  # Gold
        "accent": "#F5F5F0",  # Ivory
    },
    "black-rose": {
        "primary": "#C0C0C0",  # Cosmic Silver
        "secondary": "#0A0A0A",  # Obsidian
        "accent": "#0a0a1a",  # Deep Blue
    },
    "love-hurts": {
        "primary": "#DC143C",  # Crimson Red
        "secondary": "#800080",  # Deep Purple
        "accent": "#FFD700",  # Candlelight Gold
    },
}

LOGO_VERIFICATION_PROMPT = """
Analyze this product image for brand logo and design consistency.

Reference Information:
- Collection: {collection}
- Brand Colors: {colors}
- Expected Logo Style: {logo_style}

Evaluate:
1. Logo Detection: Is there visible branding/logo on the product?
2. Logo Placement: Is it positioned appropriately for the garment type?
3. Color Accuracy: Do the logo colors match the brand palette?
4. Print Quality: Is the logo clear, not distorted or pixelated?
5. Design Integrity: Does the overall design match SkyyRose luxury aesthetic?

Return a JSON response with:
{{
    "logo_detected": true/false,
    "placement_score": 0-100,
    "color_accuracy": 0-100,
    "print_quality": 0-100,
    "design_integrity": 0-100,
    "overall_score": 0-100,
    "issues": ["list of specific issues if any"],
    "recommendation": "pass" or "review" or "reject"
}}
"""

LOGO_STYLES = {
    "signature": "Rose gold rose emblem with elegant script typography, premium minimalist aesthetic",
    "black-rose": "Silver/cosmic trophy or rose emblem, dark sophisticated luxury feel",
    "love-hurts": "Red heart/rose motif with emotional typography, passionate romantic theme",
}


def encode_image_to_base64(image_path: Path) -> str:
    """Encode image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(image_path: Path) -> str:
    """Get MIME type from file extension."""
    ext = image_path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/jpeg")


async def analyze_with_gemini(
    image_path: Path,
    collection: str,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Use Gemini Vision API to analyze logo consistency."""
    if not GOOGLE_API_KEY:
        return {"error": "GOOGLE_API_KEY not set", "overall_score": 0}

    try:
        # Encode image
        image_data = encode_image_to_base64(image_path)
        mime_type = get_mime_type(image_path)

        # Build prompt
        prompt = LOGO_VERIFICATION_PROMPT.format(
            collection=collection,
            colors=json.dumps(BRAND_COLORS.get(collection, {})),
            logo_style=LOGO_STYLES.get(collection, "Premium luxury brand aesthetic"),
        )

        # Gemini request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            },
        }

        response = await client.post(
            f"{GEMINI_URL}?key={GOOGLE_API_KEY}",
            json=payload,
            timeout=60.0,
        )

        if response.status_code != 200:
            return {
                "error": f"Gemini API error: {response.status_code}",
                "overall_score": 0,
            }

        result = response.json()

        # Extract text response
        text = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # Parse JSON from response
        try:
            # Find JSON in response
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {
            "error": "Could not parse Gemini response",
            "raw_response": text[:500],
            "overall_score": 50,  # Assume neutral if parsing fails
        }

    except Exception as e:
        return {"error": str(e), "overall_score": 0}


def compare_with_visual_engine(
    enhanced_path: Path,
    logo_paths: list[Path],
    engine: VisualComparisonEngine,
) -> dict[str, Any]:
    """Use VisualComparisonEngine to compare image colors with logo colors."""
    results = []

    for logo_path in logo_paths:
        if not logo_path.exists():
            continue

        try:
            # Compare colors only (logos are small, full SSIM not meaningful)
            comparison = engine.compare_colors_only(
                str(enhanced_path),
                str(logo_path),
            )
            results.append(
                {
                    "logo": logo_path.name,
                    "color_similarity": comparison.get("color_similarity", 0),
                    "histogram_correlation": comparison.get("histogram_correlation", 0),
                }
            )
        except Exception as e:
            results.append(
                {
                    "logo": logo_path.name,
                    "error": str(e),
                }
            )

    if not results:
        return {"error": "No logos to compare"}

    # Average color similarity across all logo comparisons
    valid_scores = [r.get("color_similarity", 0) for r in results if "error" not in r]
    avg_color_similarity = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    return {
        "comparisons": results,
        "avg_color_similarity": avg_color_similarity,
    }


async def verify_collection(
    collection: str,
    dry_run: bool = False,
    limit: int = 0,
) -> dict[str, Any]:
    """Verify all images in a collection."""
    collection_dir = ENHANCED_DIR / collection
    if not collection_dir.exists():
        return {"error": f"Collection directory not found: {collection_dir}"}

    logo_paths = [p for p in LOGO_FILES.get(collection, []) if p.exists()]
    if not logo_paths:
        print(f"  Warning: No logo files found for {collection}")

    # Get all main images
    images = list(collection_dir.glob("*/*_main.jpg")) + list(collection_dir.glob("*/*_main.png"))
    if limit > 0:
        images = images[:limit]

    print(f"\n  Found {len(images)} images to verify")

    results = []
    passed = 0
    review = 0
    failed = 0

    # Initialize comparison engine
    try:
        engine = VisualComparisonEngine()
    except Exception as e:
        print(f"  Warning: Could not initialize VisualComparisonEngine: {e}")
        engine = None

    async with httpx.AsyncClient() as client:
        for i, image_path in enumerate(images):
            if dry_run:
                print(f"  [{i + 1}/{len(images)}] Would verify: {image_path.name}")
                continue

            # Gemini analysis
            gemini_result = await analyze_with_gemini(image_path, collection, client)

            # Visual comparison (if engine available)
            visual_result = {}
            if engine and logo_paths:
                visual_result = compare_with_visual_engine(image_path, logo_paths, engine)

            # Combine scores
            gemini_score = gemini_result.get("overall_score", 50)
            visual_score = visual_result.get("avg_color_similarity", 50) * 100

            # Weighted final score (Gemini 70%, Visual 30%)
            final_score = (gemini_score * 0.7) + (visual_score * 0.3)

            recommendation = gemini_result.get("recommendation", "review")
            if final_score >= 80:
                recommendation = "pass"
                passed += 1
            elif final_score >= 60:
                recommendation = "review"
                review += 1
            else:
                recommendation = "reject"
                failed += 1

            result = {
                "image": str(image_path),
                "gemini_score": gemini_score,
                "visual_score": visual_score,
                "final_score": round(final_score, 1),
                "recommendation": recommendation,
                "issues": gemini_result.get("issues", []),
            }
            results.append(result)

            status_icon = (
                "✓" if recommendation == "pass" else ("⚠" if recommendation == "review" else "✗")
            )
            print(
                f"  [{i + 1}/{len(images)}] {status_icon} {image_path.parent.name[:30]} - Score: {final_score:.1f}"
            )

            # Rate limiting
            await asyncio.sleep(0.5)

    return {
        "collection": collection,
        "total": len(images),
        "passed": passed,
        "review": review,
        "failed": failed,
        "pass_rate": f"{(passed / len(images) * 100):.1f}%" if images else "N/A",
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(description="Verify logo consistency in AI-enhanced images")
    parser.add_argument("--dry-run", action="store_true", help="List files without processing")
    parser.add_argument(
        "--collection", choices=["signature", "black-rose", "love-hurts", "all"], default="all"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Limit images per collection (0 = all)"
    )
    parser.add_argument("--output", type=str, default="", help="Output JSON file for results")
    args = parser.parse_args()

    print("=" * 60)
    print("Logo Consistency Verification")
    print("=" * 60)
    print(f"Using Gemini Model: {GEMINI_MODEL}")
    print(f"API Key: {'✓ Set' if GOOGLE_API_KEY else '✗ Missing'}")

    if not GOOGLE_API_KEY:
        print("\nERROR: GOOGLE_API_KEY environment variable not set")
        print("Set it with: export GOOGLE_API_KEY=your_key")
        return

    collections = (
        ["signature", "black-rose", "love-hurts"] if args.collection == "all" else [args.collection]
    )

    all_results = {}
    total_passed = 0
    total_review = 0
    total_failed = 0
    total_images = 0

    for collection in collections:
        print(f"\n{'=' * 60}")
        print(f"Verifying: {collection.upper()}")
        print("=" * 60)

        result = await verify_collection(
            collection,
            dry_run=args.dry_run,
            limit=args.limit,
        )

        all_results[collection] = result
        total_passed += result.get("passed", 0)
        total_review += result.get("review", 0)
        total_failed += result.get("failed", 0)
        total_images += result.get("total", 0)

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total Images: {total_images}")
    print(
        f"Passed (≥80): {total_passed} ({total_passed / total_images * 100:.1f}%)"
        if total_images
        else ""
    )
    print(
        f"Review (60-79): {total_review} ({total_review / total_images * 100:.1f}%)"
        if total_images
        else ""
    )
    print(
        f"Failed (<60): {total_failed} ({total_failed / total_images * 100:.1f}%)"
        if total_images
        else ""
    )

    # Save results
    if args.output and not args.dry_run:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "summary": {
                        "total": total_images,
                        "passed": total_passed,
                        "review": total_review,
                        "failed": total_failed,
                    },
                    "collections": all_results,
                },
                f,
                indent=2,
            )
        print(f"\nResults saved to: {output_path}")

    # Flag issues
    flagged = []
    for coll, result in all_results.items():
        for item in result.get("results", []):
            if item.get("recommendation") in ("review", "reject"):
                flagged.append(
                    {
                        "collection": coll,
                        "image": item.get("image"),
                        "score": item.get("final_score"),
                        "issues": item.get("issues"),
                    }
                )

    if flagged:
        print(f"\n⚠ Flagged Items ({len(flagged)}):")
        for item in flagged[:10]:
            print(
                f"  - {Path(item['image']).parent.name}: {item['score']} - {item['issues'][:2] if item['issues'] else 'No specific issues'}"
            )
        if len(flagged) > 10:
            print(f"  ... and {len(flagged) - 10} more")


if __name__ == "__main__":
    asyncio.run(main())
