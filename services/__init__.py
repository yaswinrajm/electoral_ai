"""
services/__init__.py
=====================
Makes the services/ directory a Python package.
Exports public service interfaces for use by the API route layer.

Example:
    from services.ai_service import get_gemini_model
    from services.translation_service import translate_text_to_language
    from services.tts_service import synthesize_speech

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from services.ai_service import get_gemini_model, ask_ai_with_retry
from services.translation_service import translate_text_to_language, load_dictionary_cache
from services.tts_service import synthesize_speech

__all__ = [
    "get_gemini_model",
    "ask_ai_with_retry",
    "translate_text_to_language",
    "load_dictionary_cache",
    "synthesize_speech",
]
