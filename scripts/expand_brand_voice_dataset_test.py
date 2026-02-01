"""Test dataset expansion with 15 examples (quick validation)."""

import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are SkyyRose's brand voice - a luxury streetwear brand from Oakland, California.

Brand Guidelines:
- Tone: Sophisticated yet accessible, bold yet elegant
- Style: Poetic, evocative, with street culture authenticity
- Colors: Rose gold (#B76E79), black (#1A1A1A), pastels
- Tagline: "Where Love Meets Luxury"
- Collections: Signature (classic), Black Rose (dark romantic), Love Hurts (edgy)

Always emphasize:
- Premium quality and craftsmanship
- Oakland heritage and authenticity
- Gender-neutral inclusivity
- Limited edition exclusivity
- Emotional connection through fashion

Never use: cheap, discount, basic, generic, mass-produced"""

TEST_PROMPTS = [
    "Write a product description for rose gold joggers.",
    "Describe a Black Rose graphic tee.",
    "Create marketing copy for a Love Hurts bomber jacket.",
    "Write an Instagram caption for a new collection drop.",
    "Create a welcome email for new subscribers.",
    "Respond to a customer asking about sizing.",
    "Write about SkyyRose's Oakland origins.",
    "Describe a Signature collection beanie.",
    "Create a Twitter post announcing a limited restock.",
    "Write a post-purchase thank you email.",
    "Describe a Black Rose windbreaker.",
    "Create copy for Love Hurts track jacket.",
    "Write a social post about community impact.",
    "Respond to an order tracking inquiry.",
    "Describe the brand's design philosophy.",
]


async def generate_response(prompt: str, client: httpx.AsyncClient) -> str:
    """Generate a brand voice response using Claude API."""
    response = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"]


async def main():
    print("Generating 15 test examples...")
    examples = []

    async with httpx.AsyncClient() as client:
        for i, prompt in enumerate(TEST_PROMPTS, 1):
            print(f"[{i}/{len(TEST_PROMPTS)}] {prompt[:50]}...")
            response = await generate_response(prompt, client)
            examples.append(
                {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ]
                }
            )
            await asyncio.sleep(0.5)

    output_path = Path("datasets/skyyrose_brand_voice/train_test.jsonl")
    with open(output_path, "w") as f:
        for example in examples:
            f.write(json.dumps(example) + "\n")

    print(f"\n✓ Generated {len(examples)} examples")
    print(f"✓ Saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
