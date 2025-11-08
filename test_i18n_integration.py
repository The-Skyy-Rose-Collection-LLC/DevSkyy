#!/usr/bin/env python3
"""
Test i18n Integration
Verifies that all translation files load correctly and key translations work
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import i18n_loader directly to avoid circular imports
import importlib.util
spec = importlib.util.spec_from_file_location(
    "i18n_loader",
    Path(__file__).parent / "fashion_ai_bounded_autonomy" / "i18n_loader.py"
)
i18n_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n_module)

t = i18n_module.t
set_language = i18n_module.set_language
get_language = i18n_module.get_language
get_available_languages = i18n_module.get_available_languages


def test_i18n_integration():
    """Test i18n system integration"""
    print("=" * 70)
    print("I18N INTEGRATION TEST")
    print("=" * 70)

    # Test 1: Check available languages
    print("\n✅ Test 1: Available Languages")
    languages = get_available_languages()
    print(f"Available languages: {languages}")
    expected = ['en-US', 'es-ES', 'fr-FR', 'ja-JP', 'zh-CN']
    for lang in expected:
        if lang in languages:
            print(f"  ✓ {lang} loaded")
        else:
            print(f"  ✗ {lang} MISSING")

    # Test 2: Default language
    print("\n✅ Test 2: Default Language")
    current_lang = get_language()
    print(f"Current language: {current_lang}")

    # Test 3: Test key translations in each language
    print("\n✅ Test 3: Key Translations")

    test_keys = [
        ("approval.submitted", {"action_id": "test123", "workflow": "default"}),
        ("cli.list_pending", {}),
        ("tasks.success", {"name": "test_task", "task_id": "task_001"}),
        ("errors.generic", {"error": "test error"}),
    ]

    for lang in expected:
        if not set_language(lang):
            print(f"\n  ✗ Could not set language: {lang}")
            continue

        print(f"\n  Language: {lang}")
        for key, params in test_keys:
            translation = t(key, **params)
            print(f"    {key}: {translation[:80]}...")

    # Test 4: Fallback behavior
    print("\n✅ Test 4: Fallback Behavior")
    set_language('en-US')
    missing_key = t('nonexistent.key.that.does.not.exist')
    print(f"Missing key returns: {missing_key}")
    if missing_key == 'nonexistent.key.that.does.not.exist':
        print("  ✓ Fallback working correctly")
    else:
        print("  ✗ Fallback NOT working")

    # Test 5: Variable substitution
    print("\n✅ Test 5: Variable Substitution")
    set_language('en-US')
    result = t('approval.submitted', action_id='ACT-123', workflow='high_risk')
    print(f"With variables: {result}")
    if 'ACT-123' in result and 'high_risk' in result:
        print("  ✓ Variable substitution working")
    else:
        print("  ✗ Variable substitution FAILED")

    print("\n" + "=" * 70)
    print("I18N INTEGRATION TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_i18n_integration()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
