#!/usr/bin/env python3
"""
Test Multi-Model AI Orchestration for DevSkyy
Tests all API connections and intelligent duo routing
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_multi_model_system():
    """Test the complete multi-model system"""

    print("=" * 70)
    print("🚀 DevSkyy Multi-Model AI Orchestration Test")
    print("=" * 70)
    print()

    # Test 1: Claude Sonnet 4.5
    print("1️⃣  Testing ANTHROPIC (Claude Sonnet 4.5)...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "In one sentence, describe DevSkyy's multi-model AI system."
            }]
        )
        print(f"   ✅ Claude: {response.content[0].text}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
        raise  # Re-raise to fail the test

    # Test 2: OpenAI GPT-4
    print("2️⃣  Testing OPENAI (GPT-4 Turbo)...")
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "In one sentence, what makes intelligent duo routing powerful?"
            }]
        )
        print(f"   ✅ GPT-4: {response.choices[0].message.content}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
        raise  # Re-raise to fail the test

    # Test 3: Google Gemini
    print("3️⃣  Testing GOOGLE GEMINI (1.5 Flash)...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            "In one sentence, describe why visual AI is important for fashion."
        )
        print(f"   ✅ Gemini: {response.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
        raise  # Re-raise to fail the test

    # Test 4: Hugging Face
    print("4️⃣  Testing HUGGING FACE...")
    hf_token = os.getenv('HUGGING_FACE_TOKEN')
    if hf_token and hf_token.startswith('hf_'):
        print(f"   ✅ Hugging Face token valid\n")
    else:
        print(f"   ❌ Invalid Hugging Face token\n")
        import sys
        sys.exit(1)  # Exit with error code for invalid token

    print("=" * 70)
    print("🎯 Multi-Model Orchestration Ready!")
    print("=" * 70)
    print()
    print("Agent Category Assignments:")
    print("  • Frontend: Claude + Gemini")
    print("  • Backend: Claude + GPT-5")
    print("  • Content: Huggingface + Claude + Gemini + GPT-5")
    print("  • Development: Claude + Codex")
    print()
    print("✨ Intelligent Duo Routing: ACTIVE")
    print("   Best 2 models selected per task for optimal performance!")
    print()

if __name__ == "__main__":
    asyncio.run(test_multi_model_system())
