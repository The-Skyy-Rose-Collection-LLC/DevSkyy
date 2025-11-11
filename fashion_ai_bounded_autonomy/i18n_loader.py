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
        Create a TranslationLoader configured with a default language and load available translations.
        
        Parameters:
            default_language (str): Language code to use when a translation is missing in the current language (e.g., "en-US"). Defaults to "en-US".
        """
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.i18n_dir = Path(__file__).parent / "i18n"

        # Load all available translations
        self._load_translations()

    def _load_translations(self) -> None:
        """
        Load JSON translation files from the module's i18n directory into the translations mapping.
        
        If the i18n directory does not exist the function logs a warning and returns without modifying translations.
        For each `*.json` file found, the file stem is used as the language code (e.g., `en-US` from `en-US.json`), the file is read using UTF-8, and the parsed JSON is stored under `self.translations[lang_code]`. Successful loads are logged at info level; failures for individual files are logged as errors and do not stop processing other files.
        """
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
        Change the loader's current language to a loaded language code.
        
        Parameters:
            language_code (str): Language code to select (e.g., "es-ES", "fr-FR").
        
        Returns:
            bool: `True` if the language was set successfully, `False` otherwise.
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
        """
        Return the list of language codes for which translations have been loaded.
        
        Returns:
            list[str]: Language code strings currently available (keys of the translations mapping).
        """
        return list(self.translations.keys())

    def translate(self, key: str, **kwargs) -> str:
        """
        Retrieve a translated string for a dot-notated key using the current language with fallback to the default language.
        
        If the key is not found in the current language, the default language is consulted. If the key cannot be found in either, the key itself is returned. When `kwargs` are provided, the found translation is formatted with those variables; if a required variable is missing during formatting, the unformatted translation is returned.
        
        Parameters:
            key (str): Dot-notated translation key (e.g., "approval.submitted").
            **kwargs: Values to substitute into the translation string via `str.format`.
        
        Returns:
            str: The translated and formatted string if found, otherwise the original `key`.
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
        Retrieve a nested string value from a dictionary using a dot-separated key.
        
        If the key path exists and resolves to a string, returns that string. If any segment is missing, an intermediate value is not a mapping, or the final value is not a string, returns None.
        
        Parameters:
            data: Dictionary to search.
            key: Dot-separated path (e.g., "approval.submitted").
        
        Returns:
            The string value found at the path, or None if not found or not a string.
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
    """
    Return the list of loaded language codes available for translations.
    
    Returns:
        list[str]: Available language codes (e.g., "en-US", "es-ES").
    """
    return _loader.get_available_languages()


def t(key: str, **kwargs) -> str:
    """
    Translate a dot-notated key into the currently selected language.
    
    If the key is missing in the current language, the default language is used as a fallback; if still not found, the key itself is returned. Provided keyword arguments are used to format the resulting translation string.
    
    Parameters:
        key (str): Translation key using dot notation (e.g., "errors.not_found").
        **kwargs: Values to substitute into the translation string via Python formatting.
    
    Returns:
        str: The translated and formatted string, or the original key if no translation is available.
    """
    return _loader.translate(key, **kwargs)


def init_i18n_from_env() -> None:
    """
    Initialize the module language from environment variables.
    
    Reads the LANGUAGE or LANG environment variable, extracts the language code before any dot (for example, "es-ES" from "es-ES.UTF-8"), and attempts to set that language; logs whether initialization succeeded or failed.
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