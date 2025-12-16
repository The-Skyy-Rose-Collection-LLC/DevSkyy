#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API connection.

Usage:
    python3 test_openai_connection.py
"""

import os
import sys


def test_openai_connection():
    """Test OpenAI API connection"""

    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY environment variable is not set")
        print("\nTo set it:")
        print('  export OPENAI_API_KEY="your-key-here"')
        print("\nOr add to ~/.zshrc:")
        print("  echo 'export OPENAI_API_KEY=\"your-key-here\"' >> ~/.zshrc")
        print("  source ~/.zshrc")
        return False

    # Mask the key for security
    masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
    print(f"✓ API key found: {masked_key}")

    # Test the connection
    try:
        from openai import OpenAI

        print("\n🔄 Testing OpenAI API connection...")

        client = OpenAI(api_key=api_key)

        # Make a simple test request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello from DevSkyy!' in exactly 5 words."}],
            max_tokens=20,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        tokens = response.usage.total_tokens

        print("\n✅ SUCCESS! OpenAI API is working!")
        print(f"\nResponse: {content}")
        print(f"Tokens used: {tokens}")
        print(f"Model: {response.model}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. API key has been revoked")
        print("  3. Network connection issue")
        print("  4. OpenAI service is down")
        print("\nPlease:")
        print("  1. Verify your API key at: https://platform.openai.com/api-keys")
        print("  2. Check your internet connection")
        print("  3. Try again in a few moments")
        return False


if __name__ == "__main__":
    success = test_openai_connection()
    sys.exit(0 if success else 1)
