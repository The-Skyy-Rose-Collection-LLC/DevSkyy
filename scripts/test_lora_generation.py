#!/usr/bin/env python3
"""Test LoRA generation - models wearing SkyyRose products."""

import asyncio
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from imagery.skyyrose_lora_generator import (
    GarmentType,
    SkyyRoseCollection,
    SkyyRoseLoRAGenerator,
)


async def main():
    """Generate test images of models wearing products."""
    print("🎨 SkyyRose LoRA Generator Test")
    print("=" * 50)

    generator = SkyyRoseLoRAGenerator()

    # Test 1: Model wearing SIGNATURE hoodie
    print("\n📸 Generating: Model wearing SIGNATURE hoodie...")
    result1 = await generator.generate(
        prompt="professional fashion model wearing lavender rose hoodie, full body shot, studio lighting, fashion photography",
        collection=SkyyRoseCollection.SIGNATURE,
        garment_type=GarmentType.HOODIE,
        num_outputs=1,
    )

    if result1.success:
        print(f"   ✅ Success! URL: {result1.output_urls[0]}")
        print(f"   ⏱️  Latency: {result1.latency_ms:.0f}ms")
    else:
        print(f"   ❌ Error: {result1.error}")

    # Test 2: Model wearing BLACK_ROSE bomber
    print("\n📸 Generating: Model wearing BLACK_ROSE bomber jacket...")
    result2 = await generator.generate(
        prompt="model wearing black bomber jacket with rose embroidery, urban street style, dramatic lighting",
        collection=SkyyRoseCollection.BLACK_ROSE,
        garment_type=GarmentType.BOMBER,
        num_outputs=1,
    )

    if result2.success:
        print(f"   ✅ Success! URL: {result2.output_urls[0]}")
        print(f"   ⏱️  Latency: {result2.latency_ms:.0f}ms")
    else:
        print(f"   ❌ Error: {result2.error}")

    # Test 3: Model wearing LOVE_HURTS windbreaker
    print("\n📸 Generating: Model wearing LOVE_HURTS windbreaker...")
    result3 = await generator.generate(
        prompt="fashion model in red windbreaker jacket, emotional pose, editorial photography",
        collection=SkyyRoseCollection.LOVE_HURTS,
        garment_type=GarmentType.WINDBREAKER,
        num_outputs=1,
    )

    if result3.success:
        print(f"   ✅ Success! URL: {result3.output_urls[0]}")
        print(f"   ⏱️  Latency: {result3.latency_ms:.0f}ms")
    else:
        print(f"   ❌ Error: {result3.error}")

    # Print stats
    print("\n" + "=" * 50)
    stats = generator.get_stats()
    print("📊 Generation Stats:")
    print(f"   Total: {stats['total_generations']}")
    print(f"   Success Rate: {stats['success_rate'] * 100:.0f}%")
    print(f"   Total Cost: ${stats['total_cost_usd']:.4f}")
    print(f"   Avg Latency: {stats['avg_latency_ms']:.0f}ms")

    # Return URLs for easy access
    urls = []
    for r in [result1, result2, result3]:
        if r.success and r.output_urls:
            urls.extend(r.output_urls)

    print("\n🖼️  All Generated Images:")
    for i, url in enumerate(urls, 1):
        print(f"   {i}. {url}")

    return urls


if __name__ == "__main__":
    asyncio.run(main())
