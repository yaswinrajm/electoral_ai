"""
services/translation_service.py — Google Cloud Translation Service Layer
=========================================================================
Encapsulates all interactions with the Google Cloud Translation API v2.
This service is responsible for:
  - Real-time translation of individual text strings
  - Loading and serving the pre-generated UI translation cache from disk

Design Principle:
    Route handlers call `translate_text_to_language()` or `load_dictionary_cache()`
    and work with plain Python dicts/strings. All Translation SDK details
    are confined to this module.

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import os
import json
from typing import Dict, Optional

from config import settings
from data.electoral_data import BASE_DICTIONARY


# ─── Module-Level State ───────────────────────────────────────────────────────

# Path to the pre-generated translations file (created by generate_translations.py)
TRANSLATIONS_FILE_PATH: str = os.path.join("static", "translations.json")


def load_dictionary_cache() -> Dict[str, Dict[str, str]]:
    """
    Loads the pre-generated UI translation cache from disk into memory.

    The translations file is created by running `generate_translations.py` once.
    At runtime, all language dictionaries are served from this in-memory cache,
    making language switching instant and completely free (no API calls).

    If the translations file is not found (e.g., during development), the cache
    is pre-populated with only English as a safe fallback.

    Returns:
        Dict[str, Dict[str, str]]: A mapping of language code → translation dict.
                                   e.g., {"en": {"title": "Electoral AI..."}, "hi": {...}}

    Example:
        >>> cache = load_dictionary_cache()
        >>> cache["ta"]["vote_btn"]
        'வாக்களிக்கவும்'
    """
    # Start with English as the baseline (avoids any API call for the default lang)
    cache: Dict[str, Dict[str, str]] = {"en": BASE_DICTIONARY}

    if os.path.exists(TRANSLATIONS_FILE_PATH):
        with open(TRANSLATIONS_FILE_PATH, "r", encoding="utf-8") as f:
            loaded: Dict[str, Dict[str, str]] = json.load(f)
            cache.update(loaded)

    return cache


def translate_text_to_language(
    text: str,
    target_language: str,
    translate_client: Optional[object] = None,
) -> str:
    """
    Translates a text string into the specified target language.

    In mock_mode, returns a prefixed mock translation without making any API call.
    In production, delegates to the Google Cloud Translation API v2 via the
    provided client instance.

    Args:
        text (str): The source text to translate. Can be empty string.
        target_language (str): ISO 639-1 language code for the target language
                               (e.g., "hi", "ta", "te").
        translate_client (Optional[object]): An initialized google.cloud.translate_v2.Client.
                                             Must be provided in production mode.

    Returns:
        str: The translated text string.

    Raises:
        ValueError: If translate_client is None in production mode.
        Exception: If the Translation API call fails (e.g., invalid language code).

    Example:
        >>> client = translate.Client()
        >>> result = translate_text_to_language("Vote", "hi", client)
        >>> print(result)  # "वोट"
    """
    # ── Mock Mode Path ──────────────────────────────────────────────────────
    if settings.mock_mode:
        return f"[{target_language.upper()}] {text}"

    # ── Production Path ─────────────────────────────────────────────────────
    if translate_client is None:
        raise ValueError("translate_client must be provided in production mode.")

    result = translate_client.translate(text, target_language=target_language)
    return result["translatedText"]
