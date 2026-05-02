"""
services/ai_service.py — Gemini AI Service Layer
=================================================
Encapsulates all interactions with Google Vertex AI (Gemini 2.5 Flash).
This service is responsible for:
  - Building language-aware system instructions for political neutrality
  - Caching GenerativeModel instances per language for performance
  - Executing prompts with exponential-backoff retry logic on quota errors

Design Principle:
    The route layer (api/routes.py) should NOT know about Gemini internals.
    It calls `ask_ai_with_retry()` and receives a plain string answer.
    All Vertex AI SDK details are confined to this module.

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import time
from typing import Optional

from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold

from config import settings
from data.electoral_data import LANGUAGE_MAP


# ─── Module-Level Constants ───────────────────────────────────────────────────

# Number of times to retry a Gemini request before giving up
MAX_RETRIES: int = 3

# Seconds to wait between retry attempts (on 429 quota errors)
RETRY_DELAY_SECONDS: int = 5

# The Gemini model version to use for all inference
GEMINI_MODEL_ID: str = "gemini-2.5-flash"


# ─── Per-Language Model Cache ─────────────────────────────────────────────────
# Stores one GenerativeModel instance per language code.
# Keyed by ISO 639-1 code, e.g. {"en": GenerativeModel(...), "hi": GenerativeModel(...)}
# Exposed as a public name so route handlers and test fixtures can inject mock models.
GEMINI_MODEL_CACHE: dict = {}


def _build_system_instruction(language_code: str) -> str:
    """
    Constructs the system instruction string for the Gemini model.

    The instruction enforces:
      - Political neutrality (no opinions, no candidate commentary)
      - Indian electoral context only (ECI, NVSP, Form 6, EPIC)
      - Response language enforcement (model must respond in the user's language)

    Args:
        language_code (str): ISO 639-1 code for the target language (e.g., "hi").

    Returns:
        str: The complete system instruction string for GenerativeModel initialization.

    Example:
        >>> _build_system_instruction("hi")
        "You are a politically neutral Electoral AI assistant..."
    """
    lang_name: str = LANGUAGE_MAP.get(language_code, "English")
    return (
        f"You are a politically neutral Electoral AI assistant for the Election Commission of India. "
        f"Your sole purpose is to provide factual, procedural information regarding Indian elections, "
        f"voting mechanics, voter registration (like Form 6, EPIC, NVSP), and schedules. "
        f"Do not express political opinions, biases, or comment on specific candidates or political events. "
        f"YOU MUST RESPOND STRICTLY IN {lang_name.upper()}."
    )


def _build_safety_settings() -> dict:
    """
    Returns the safety settings configuration for the Gemini model.

    Blocks medium and above content across all four harm categories.
    This configuration ensures the AI assistant remains safe and appropriate
    for use by voters of all ages and backgrounds.

    Returns:
        dict: Mapping of HarmCategory enum values to HarmBlockThreshold enum values.
    """
    return {
        HarmCategory.HARM_CATEGORY_HARASSMENT:        HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:       HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }


def get_gemini_model(language_code: str = "en") -> Optional[GenerativeModel]:
    """
    Returns a Gemini GenerativeModel instance configured for the given language.

    Models are cached per language code. The first call for a given language
    creates and caches the instance; all subsequent calls return the cached
    instance immediately (zero initialization overhead).

    Returns None in mock_mode so callers can handle the mock path cleanly.

    Args:
        language_code (str): ISO 639-1 language code for the AI response language.
                             Defaults to "en" (English).

    Returns:
        Optional[GenerativeModel]: Configured Gemini model, or None in mock mode.

    Example:
        >>> model = get_gemini_model("ta")
        >>> response = model.generate_content("What is EPIC?")
    """
    if settings.mock_mode:
        return None

    # Return from cache if already initialized for this language
    if language_code in GEMINI_MODEL_CACHE:
        return GEMINI_MODEL_CACHE[language_code]

    # First-time initialization for this language — create and cache
    model = GenerativeModel(
        GEMINI_MODEL_ID,
        safety_settings=_build_safety_settings(),
        system_instruction=[_build_system_instruction(language_code)],
    )
    GEMINI_MODEL_CACHE[language_code] = model
    return model


def ask_ai_with_retry(question: str, language_code: str = "en") -> str:
    """
    Sends a question to Gemini and returns the AI's answer as a string.

    In mock_mode, returns a static mock response without making any API calls.

    Retry Logic:
        On a 429 (Quota Exceeded) error, waits RETRY_DELAY_SECONDS before
        retrying, up to MAX_RETRIES total attempts. Any other exception is
        immediately re-raised to the caller.

    Args:
        question (str): The voter's question to send to Gemini.
        language_code (str): ISO 639-1 code for the desired response language.
                             Defaults to "en" (English).

    Returns:
        str: The AI-generated answer text.

    Raises:
        Exception: If all retry attempts are exhausted or a non-quota error occurs.

    Example:
        >>> answer = ask_ai_with_retry("How do I register to vote?", "hi")
        >>> print(answer)  # Response in Hindi
    """
    # ── Mock Mode Path ──────────────────────────────────────────────────────
    if settings.mock_mode:
        mock_answer = "This is a mock answer about the election. Mock Mode is currently ON."
        if language_code != "en":
            mock_answer = f"[{language_code.upper()}] {mock_answer}"
        return mock_answer

    # ── Production Path ─────────────────────────────────────────────────────
    model = get_gemini_model(language_code)
    prompt = f"Answer the following question accurately and concisely: {question}"

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            is_quota_error: bool = "429" in str(exc)
            is_last_attempt: bool = attempt >= MAX_RETRIES - 1

            if is_quota_error and not is_last_attempt:
                # Quota exceeded — wait and retry
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            else:
                # Non-quota error or final attempt — propagate to caller
                raise exc

    # This line is unreachable; exists to satisfy static type checkers
    raise RuntimeError("Exhausted all retry attempts without returning or raising.")
