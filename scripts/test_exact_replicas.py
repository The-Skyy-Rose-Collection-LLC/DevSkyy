#!/usr/bin/env python3
"""
TEST RUN: Generate 3 EXACT replicas to verify pipeline quality.

This will generate 3 Signature collection products to verify:
- 100% fidelity to source images
- Maximum quality settings work correctly
- Output is ready for Threedium.io

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_exact_3d_replicas import ExactReplicaGenerator


async def main():
    """Test generation with 3 products."""

    print("\n" + "=" * 70)
    print("🧪 TEST RUN: Generating 3 EXACT replicas")
    print("   Collection: SIGNATURE")
    print("   Products: First 3 available")
    print("   Quality: MAXIMUM (4096 textures, 95% fidelity)")
    print("=" * 70 + "\n")

    generator = ExactReplicaGenerator(output_dir="./test_3d_replicas")

    # Generate first 3 Signature products
    await generator.generate_collection(
        collection="signature",
        max_concurrent=1,  # One at a time for testing
        products_limit=3,  # TEST: Only 3 products
    )

    # Save test results
    generator.save_results(output_file="test_generation_results.json")

    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("   Check test_3d_replicas/ folder for generated models")
    print("   Review test_generation_results.json for fidelity scores")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
