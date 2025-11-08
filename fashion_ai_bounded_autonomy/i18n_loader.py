"""
i18n (Internationalization) Translation Loader

Provides multi-language support for the bounded autonomy system.
Supports: en-US, es-ES, fr-FR, ja-JP, zh-CN

Usage:
    from fashion_ai_bounded_autonomy.i18n_loader import t, set_language

    set_language('es-ES')  # Switch to Spanish
    print(t('approval.submitted'))  # Returns Spanish translation
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TranslationLoader:
    """
    Manages translation loading and retrieval for multi-language support.

    Supports fallback to English if translation key not found.
    """

    def __init__(self, default_language: str = "en-US"):
        """
        Initialize translation loader.

        Args:
            default_language: Default language code (e.g., 'en-US')
        """
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.i18n_dir = Path(__file__).parent / "i18n"

        # Load all available translations
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all translation files from i18n directory."""
        if not self.i18n_dir.exists():
            logger.warning(f"i18n directory not found: {self.i18n_dir}")
            return

        for lang_file in self.i18n_dir.glob("*.json"):
            lang_code = lang_file.stem  # e.g., 'en-US' from 'en-US.json'
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"✅ Loaded translations for {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load translations for {lang_code}: {e}")

    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.

        Args:
            language_code: Language code (e.g., 'es-ES', 'fr-FR')

        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code not in self.translations:
            logger.warning(f"Language {language_code} not available. Available: {list(self.translations.keys())}")
            return False

        self.current_language = language_code
        logger.info(f"🌍 Language set to {language_code}")
        return True

    def get_language(self) -> str:
        """Get the current language code."""
        return self.current_language

    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return list(self.translations.keys())

    def translate(self, key: str, **kwargs) -> str:
        """
        Get translation for a key in the current language.

        Args:
            key: Translation key in dot notation (e.g., 'approval.submitted')
            **kwargs: Variables to substitute in the translation string

        Returns:
            Translated string, or key if translation not found

        Example:
            t('approval.timeout', hours=24)
            # Returns: "Approval request will expire in 24 hours"
        """
        # Try current language
        translation = self._get_nested_value(self.translations.get(self.current_language, {}), key)

        # Fallback to default language if not found
        if translation is None and self.current_language != self.default_language:
            translation = self._get_nested_value(self.translations.get(self.default_language, {}), key)
            if translation is not None:
                logger.debug(f"Using fallback translation for key: {key}")

        # If still not found, return the key itself
        if translation is None:
            logger.warning(f"Translation not found: {key}")
            return key

        # Substitute variables if provided
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing variable in translation {key}: {e}")
                return translation

        return translation

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """
        Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            key: Dot-separated key (e.g., 'approval.submitted')

        Returns:
            Value if found, None otherwise
        """
        keys = key.split('.')
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current if isinstance(current, str) else None


# Global translation loader instance
_loader = TranslationLoader()


def set_language(language_code: str) -> bool:
    """
    Set the current language globally.

    Args:
        language_code: Language code (e.g., 'es-ES', 'fr-FR')

    Returns:
        True if successful, False otherwise
    """
    return _loader.set_language(language_code)


def get_language() -> str:
    """Get the current language code."""
    return _loader.get_language()


def get_available_languages() -> list[str]:
    """Get list of available language codes."""
    return _loader.get_available_languages()


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.

    Shorthand for translate function.

    Args:
        key: Translation key in dot notation
        **kwargs: Variables to substitute

    Returns:
        Translated string
    """
    return _loader.translate(key, **kwargs)


def init_i18n_from_env() -> None:
    """
    Initialize i18n from environment variable.

    Reads LANGUAGE or LANG environment variable and sets it.
    Examples: LANGUAGE=es-ES, LANG=fr-FR
    """
    env_lang = os.getenv('LANGUAGE') or os.getenv('LANG')

    if env_lang:
        # Extract language code (e.g., 'es-ES' from 'es-ES.UTF-8')
        lang_code = env_lang.split('.')[0]

        # Try to set the language
        if set_language(lang_code):
            logger.info(f"🌍 Initialized i18n from environment: {lang_code}")
        else:
            logger.warning(f"Could not set language from environment: {lang_code}")


# Auto-initialize from environment on import
init_i18n_from_env()


logger.info(f"✅ i18n loader initialized (default: {_loader.default_language}, current: {_loader.current_language})")
