"""
LlamaIndex Multimodal Integration Demo
=======================================

Demonstrates the multimodal capabilities integrated into DevSkyy agents.

Features:
- Product image analysis
- Brand compliance checking
- Color extraction
- Visual quality analysis

Requirements:
- ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable
- Sample product images
"""

import asyncio
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def demo_multimodal_capabilities():
    """Demonstrate multimodal capabilities"""
    from agents.creative_agent import CreativeAgent
    from agents.multimodal_capabilities import (
        MultimodalProvider,
        get_multimodal_capabilities,
    )

    print("=" * 80)
    print("DevSkyy LlamaIndex Multimodal Integration Demo")
    print("=" * 80)

    # Initialize multimodal capabilities
    print("\n1. Initializing multimodal capabilities...")
    capabilities = get_multimodal_capabilities(provider=MultimodalProvider.ANTHROPIC)
    await capabilities.initialize()
    print("✓ Multimodal capabilities initialized")

    # Demo 1: Product Image Analysis
    print("\n" + "=" * 80)
    print("Demo 1: Product Image Analysis")
    print("=" * 80)

    sample_image = "assets/images/sample-product.jpg"  # Replace with actual path

    if Path(sample_image).exists():
        result = await capabilities.analyze_product_image(
            image_path=sample_image, product_type="clothing", include_technical=True
        )

        print(f"\nProvider: {result.provider.value}")
        print(f"Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"\nProduct Description:\n{result.text_response}")
    else:
        print(f"⚠️  Sample image not found: {sample_image}")
        print("   Skipping product analysis demo")

    # Demo 2: Brand Compliance Check
    print("\n" + "=" * 80)
    print("Demo 2: Brand Compliance Check")
    print("=" * 80)

    if Path(sample_image).exists():
        result = await capabilities.check_brand_compliance(
            image_path=sample_image,
            brand_colors=["#B76E79", "#1A1A1A", "#FFFFFF"],
            brand_style="luxury streetwear",
        )

        print(f"\nProvider: {result.provider.value}")
        print(f"Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"\nCompliance Analysis:\n{result.text_response}")
    else:
        print("   Skipping brand compliance demo")

    # Demo 3: Color Extraction
    print("\n" + "=" * 80)
    print("Demo 3: Color Extraction")
    print("=" * 80)

    if Path(sample_image).exists():
        result = await capabilities.extract_colors(image_path=sample_image)

        print(f"\nProvider: {result.provider.value}")
        print(f"Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"\nColor Analysis:\n{result.text_response}")
    else:
        print("   Skipping color extraction demo")

    # Demo 4: CreativeAgent Integration
    print("\n" + "=" * 80)
    print("Demo 4: CreativeAgent with Multimodal Tools")
    print("=" * 80)

    creative_agent = CreativeAgent()
    await creative_agent.initialize()
    print("✓ CreativeAgent initialized with multimodal tools")

    if Path(sample_image).exists():
        # Use the agent's tool method
        result = await creative_agent.analyze_product_image_tool(
            image_path=sample_image, product_type="clothing", include_technical=True
        )

        if result["success"]:
            print(f"\nProduct Type: {result['product_type']}")
            print(f"Provider: {result['provider']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Processing Time: {result['processing_time_ms']:.2f}ms")
            print(f"\nDescription:\n{result['description']}")
        else:
            print(f"⚠️  Analysis failed: {result.get('error')}")
    else:
        print("   Skipping CreativeAgent demo")

    # Cleanup
    await capabilities.close()
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


async def quick_test():
    """Quick test with sample prompt"""
    from agents.multimodal_capabilities import (
        AnalysisType,
        MultimodalProvider,
        get_multimodal_capabilities,
    )

    print("Quick Test: Multimodal Capabilities")
    print("-" * 40)

    capabilities = get_multimodal_capabilities(provider=MultimodalProvider.ANTHROPIC)
    await capabilities.initialize()

    # Test with a simple analysis
    sample_image = "assets/images/sample-product.jpg"

    if not Path(sample_image).exists():
        print(f"⚠️  Sample image not found: {sample_image}")
        print("Please provide a valid image path to test")
        return

    result = await capabilities.analyze_image(
        image_path=sample_image,
        analysis_type=AnalysisType.VISUAL_REASONING,
        prompt="Describe this image in detail. What do you see?",
    )

    print(f"\nProvider: {result.provider.value}")
    print(f"Analysis Type: {result.analysis_type.value}")
    print(f"Processing Time: {result.processing_time_ms:.2f}ms")
    print(f"\nResponse:\n{result.text_response}")

    await capabilities.close()


if __name__ == "__main__":
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ERROR: No API keys found!")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
        exit(1)

    # Run demos
    print("Select demo:")
    print("1. Full multimodal capabilities demo")
    print("2. Quick test")
    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(demo_multimodal_capabilities())
    elif choice == "2":
        asyncio.run(quick_test())
    else:
        print("Invalid choice")
