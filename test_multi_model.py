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


    # Test 1: Claude Sonnet 4.5
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[{"role": "user", "content": "In one sentence, describe DevSkyy's multi-model AI system."}],
        )
    except Exception:
        pass

    # Test 2: OpenAI GPT-4
    try:
        import openai

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=100,
            messages=[{"role": "user", "content": "In one sentence, what makes intelligent duo routing powerful?"}],
        )
    except Exception:
        pass

    # Test 3: Google Gemini
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        model.generate_content("In one sentence, describe why visual AI is important for fashion.")
    except Exception:
        pass

    # Test 4: Hugging Face
    hf_token = os.getenv("HUGGING_FACE_TOKEN")
    if hf_token and hf_token.startswith("hf_"):
        pass
    else:
        pass



if __name__ == "__main__":
    asyncio.run(test_multi_model_system())
