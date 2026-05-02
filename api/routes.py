"""
api/routes.py — API Route Handlers (Thin Controller Layer)
===========================================================
Defines all REST API endpoints exposed by the Electoral AI backend.
This module acts as a thin controller — it handles HTTP concerns only
(request parsing, response formatting, error wrapping) and delegates
all business logic to the services/ layer.

Endpoint Summary:
    GET  /api/health          — Liveness probe for Cloud Run health checks
    GET  /api/dictionary      — Serve pre-cached UI translation dictionary
    POST /api/translate       — Translate a text string to a target language
    POST /api/tts             — Convert text to Base64-encoded MP3 audio
    POST /api/ask             — Submit a voter question to Gemini AI

Architecture:
    routes.py (HTTP layer)
        → services/ai_service.py          (Gemini inference + retry)
        → services/translation_service.py (Google Translation API)
        → services/tts_service.py         (Google TTS API)
        → data/electoral_data.py          (static constants)
        → config.py                       (environment settings)

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import os
from typing import Dict, Optional

import vertexai
from fastapi import APIRouter, HTTPException
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from pydantic import BaseModel

from config import settings
from data.electoral_data import BASE_DICTIONARY
from services.ai_service import ask_ai_with_retry, GEMINI_MODEL_CACHE  # cache exposed for test injection
from services.translation_service import load_dictionary_cache, translate_text_to_language
from services.tts_service import synthesize_speech


# ─── Router Instance ──────────────────────────────────────────────────────────
router = APIRouter()


# ─── Global Client Singletons ─────────────────────────────────────────────────
# Initialized once at startup; reused for every request to avoid per-call latency.
TRANSLATE_CLIENT: Optional[translate.Client] = None
TTS_CLIENT: Optional[texttospeech.TextToSpeechClient] = None



def init_clients() -> None:
    """
    Initializes all Google Cloud SDK clients at application startup.

    Called once when this module is first imported. Initializing clients here
    avoids the overhead of creating new connections on every HTTP request.

    Implementation Note:
        MOCK_MODE is read directly from ``os.environ`` (not from the Settings
        object) so that ``pytest-env`` can override the variable before this
        module is imported during test collection. If MOCK_MODE is truthy,
        this function is a no-op and no credentials are required.

    Returns:
        None
    """
    global TRANSLATE_CLIENT, TTS_CLIENT

    mock_mode: bool = os.environ.get("MOCK_MODE", "false").lower() in ("true", "1", "yes")
    if mock_mode:
        return  # Skip all API initialization in test/mock mode

    # Ensure the service account key path is set as an env var for Google SDK auth.
    # This is needed when running locally where the .env value is loaded by Pydantic
    # but not automatically exported to the OS environment.
    if settings.google_application_credentials and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

    if TRANSLATE_CLIENT is None:
        TRANSLATE_CLIENT = translate.Client()

    if TTS_CLIENT is None:
        TTS_CLIENT = texttospeech.TextToSpeechClient()

    vertexai.init(
        project=settings.gcp_project_id,
        location=settings.gcp_region,
    )


# Run at module import time
init_clients()


# ─── In-Memory Translation Cache ──────────────────────────────────────────────
# Loaded from static/translations.json at startup; all 10 languages in memory.
DICTIONARY_CACHE: Dict[str, Dict[str, str]] = load_dictionary_cache()


# ─── Request / Response Models ────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    """
    Request body schema for POST /api/translate.

    Attributes:
        text (str): The source text to translate.
        target_language (str): ISO 639-1 language code for the target language
                               (e.g., "hi" for Hindi, "ta" for Tamil).
    """

    text: str
    target_language: str


class TTSRequest(BaseModel):
    """
    Request body schema for POST /api/tts.

    Attributes:
        text (str): The text string to synthesize into speech.
        language (str): ISO 639-1 language code used for voice selection
                        (e.g., "hi" → hi-IN voice, "ta" → ta-IN voice).
    """

    text: str
    language: str


class AskRequest(BaseModel):
    """
    Request body schema for POST /api/ask.

    Attributes:
        question (str): The voter's natural-language question in any supported language.
        target_language (str): ISO 639-1 language code for the AI response.
                               Defaults to "en" (English).
    """

    question: str
    target_language: str = "en"


# ─── API Endpoints ────────────────────────────────────────────────────────────

@router.get("/health", summary="Health Check", tags=["Infrastructure"])
async def health_check() -> Dict[str, object]:
    """
    Returns the operational status of the backend service.

    Used by Google Cloud Run for liveness probes and by monitoring tools to
    verify the container is alive and correctly configured. Also exposes the
    ``mock_mode`` flag so clients can detect the running environment.

    Returns:
        Dict[str, object]: A dict with keys:
            - ``status`` (str): Always "ok" if the service is running.
            - ``mock_mode`` (bool): True if the service is in mock/test mode.
    """
    return {"status": "ok", "mock_mode": settings.mock_mode}


@router.get("/dictionary", summary="Get UI Translation Dictionary", tags=["Localization"])
async def get_dictionary(lang: str = "en") -> Dict[str, str]:
    """
    Returns the complete UI translation dictionary for the requested language.

    All translations are loaded from ``static/translations.json`` into memory
    at startup (via ``load_dictionary_cache()``). This makes language switching
    instant and completely free — no Translation API calls are made at runtime.

    Args:
        lang (str): ISO 639-1 language code (e.g., "hi", "ta", "en").
                    Defaults to "en". Unknown codes fall back to English.

    Returns:
        Dict[str, str]: Key-value mapping of UI string keys to translated values.
                        Falls back to the English BASE_DICTIONARY for unknown codes.
    """
    if lang in DICTIONARY_CACHE:
        return DICTIONARY_CACHE[lang]

    # Graceful fallback for any unknown or unsupported language code
    return DICTIONARY_CACHE.get("en", BASE_DICTIONARY)


@router.post("/translate", summary="Translate Text", tags=["Localization"])
async def translate_text(req: TranslateRequest) -> Dict[str, str]:
    """
    Translates a text string into the specified target language.

    Primarily used by the frontend's Voice-to-Action system to translate
    English confirmation messages (e.g., "Moving to the Election Timeline now.")
    into the user's selected language before passing them to the TTS endpoint.

    In mock mode, returns a ``[LANG] <text>`` prefixed mock string without
    making any API call.

    Args:
        req (TranslateRequest): Request body containing:
            - ``text`` (str): The source text to translate.
            - ``target_language`` (str): ISO 639-1 target language code.

    Returns:
        Dict[str, str]: ``{"translated_text": "<translated string>"}``

    Raises:
        HTTPException (500): If the Google Translation API call fails.
    """
    try:
        translated: str = translate_text_to_language(
            text=req.text,
            target_language=req.target_language,
            translate_client=TRANSLATE_CLIENT,
        )
        return {"translated_text": translated}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/tts", summary="Text to Speech", tags=["Voice"])
async def text_to_speech(req: TTSRequest) -> Dict[str, str]:
    """
    Converts a text string to spoken audio using Google Cloud Text-to-Speech.

    The audio is returned as a Base64-encoded MP3 string. The frontend decodes
    this and plays it directly via the Web Audio API — no file storage required.

    Language codes are mapped to BCP-47 locale codes by the TTS service layer.
    Unknown language codes fall back gracefully to the ``en-US`` voice.

    In mock mode, returns a static silent MP3 in Base64 without any API call.

    Args:
        req (TTSRequest): Request body containing:
            - ``text`` (str): The text to convert to speech.
            - ``language`` (str): ISO 639-1 language code for voice selection.

    Returns:
        Dict[str, str]: ``{"audio_base64": "<base64 MP3 string>"}``

    Raises:
        HTTPException (500): If the Google TTS API call fails.
    """
    try:
        audio_b64: str = synthesize_speech(
            text=req.text,
            language_code=req.language,
            tts_client=TTS_CLIENT,
        )
        return {"audio_base64": audio_b64}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ask", summary="Ask the Electoral AI", tags=["AI"])
async def ask_gemini(req: AskRequest) -> Dict[str, str]:
    """
    Submits a voter's question to Gemini 2.5 Flash and returns the AI answer.

    The AI model is pre-configured to:
      - Respond only about Indian electoral topics (ECI, NVSP, Form 6, EPIC, etc.)
      - Maintain strict political neutrality at all times
      - Respond in the user's selected language (enforced by the system prompt)

    On transient 429 quota errors, the service retries up to 3 times with a
    5-second delay between attempts (handled by ``ask_ai_with_retry``).

    In mock mode, returns a static mock answer without any Vertex AI API call.

    Args:
        req (AskRequest): Request body containing:
            - ``question`` (str): The voter's natural-language question.
            - ``target_language`` (str): ISO 639-1 code for the AI response language.
                                        Defaults to "en".

    Returns:
        Dict[str, str]: ``{"answer": "<AI-generated response>"}``

    Raises:
        HTTPException (500): If the Gemini API fails after all retry attempts.
    """
    try:
        answer: str = ask_ai_with_retry(
            question=req.question,
            language_code=req.target_language,
        )
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
