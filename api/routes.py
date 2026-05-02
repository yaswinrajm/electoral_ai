"""
api/routes.py — Core API Route Handlers
=========================================
Defines all REST API endpoints for the Electoral AI backend. This module handles:
  - Language dictionary serving (UI translation, pre-cached in static JSON)
  - Real-time text translation via Google Cloud Translation API
  - Text-to-Speech audio synthesis via Google Cloud TTS API
  - AI question answering via Google Vertex AI (Gemini 2.5 Flash)

Key Design Decisions:
  - All Google SDK clients (Translation, TTS) are initialized ONCE at module load
    to minimize per-request latency ("warm initialization").
  - Gemini GenerativeModel instances are cached per language to avoid re-initialization
    overhead on every request.
  - UI translations are pre-generated via `generate_translations.py` and loaded from
    `static/translations.json` at startup — making language switching instant and
    completely free (no Translation API calls at runtime).
  - The AI system prompt locks Gemini to Indian electoral context and enforces
    strict political neutrality with BLOCK_MEDIUM_AND_ABOVE safety thresholds.
  - Retry logic (max 3 attempts, 5s delay) handles transient 429 quota errors.

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import os
import json
import time
import base64

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings

import vertexai
from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech


# ─── Router ───────────────────────────────────────────────────────────────────
router = APIRouter()


# ─── Global Client Singletons ─────────────────────────────────────────────────
# These are initialized once at startup and reused for every request.
# Avoids the overhead of creating new API client connections per request.
TRANSLATE_CLIENT = None
TTS_CLIENT = None
GEMINI_MODEL_CACHE: dict = {}  # Keyed by language code, e.g. {"hi": GenerativeModel(...)}


def init_clients():
    """
    Initializes Google Cloud SDK clients and Vertex AI at application startup.

    This function is called once when the module is first imported. By doing
    this at module level rather than inside request handlers, we avoid the
    latency cost of client initialization on every API call.

    In mock_mode, this function is a no-op — no real API credentials are needed.
    """
    global TRANSLATE_CLIENT, TTS_CLIENT

    if settings.mock_mode:
        return  # Skip initialization in mock/dev mode

    # Initialize Translation client (singleton)
    if TRANSLATE_CLIENT is None:
        TRANSLATE_CLIENT = translate.Client()

    # Initialize Text-to-Speech client (singleton)
    if TTS_CLIENT is None:
        TTS_CLIENT = texttospeech.TextToSpeechClient()

    # Initialize Vertex AI SDK with our GCP project and region
    vertexai.init(project="daring-span-495114-b2", location="us-central1")


# Run at module import time
init_clients()


# ─── Request/Response Models ──────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    """Request body for the /translate endpoint."""
    text: str             # The text to translate
    target_language: str  # BCP-47 language code (e.g., "hi", "ta", "en")


class TTSRequest(BaseModel):
    """Request body for the /tts endpoint."""
    text: str      # The text to convert to speech
    language: str  # Language code for voice selection (e.g., "hi", "ta")


class AskRequest(BaseModel):
    """Request body for the /ask endpoint."""
    question: str                   # The user's question in any language
    target_language: str = "en"     # Language code for the AI response (default: English)


# ─── UI Translation Dictionary ────────────────────────────────────────────────
# This is the master English source for all UI labels, buttons, and text.
# The `generate_translations.py` script translates this into all supported
# languages and saves the output to `static/translations.json`.
BASE_DICTIONARY = {
    "title":         "Electoral AI Dashboard",
    "home":          "Home",
    "features":      "Features",
    "contact":       "Contact",
    "core_features": "Core Features",
    "card1_title":   "Real-time Analysis",
    "card1_desc":    "Monitor electoral data and analytics in real-time with high accuracy models.",
    "card2_title":   "Accessible Reporting",
    "card2_desc":    "Generate WCAG 2.1 AA compliant reports ensuring everyone has access to vital data.",
    "learn_more":    "Learn More",
    "voice_guide":   "Voice Guide",
    "ask_ai":        "Ask the AI:",
    "listening":     "Listening...",
    "booth_title":   "Practice Voting Booth",
    "booth_desc":    "Practice how to vote using the electronic ballot unit below.",
    "candidate":     "Candidate",
    "candidate_a":   "Candidate A",
    "candidate_b":   "Candidate B",
    "candidate_c":   "Candidate C",
    "candidate_d":   "Candidate D",
    "vote_btn":      "VOTE",
    "confirm_title": "Confirm Your Vote",
    "confirm_desc":  "Are you sure you want to vote for this candidate?",
    "cancel":        "Cancel",
    "confirm":       "Confirm",
    "thank_you":     "Thank You for Practicing!",
    "thank_you_desc":"Your vote has been simulated. This was just a practice session to help you understand the process.",
    "back_to_booth": "Try Again",
    "quiz_title":    "Voter Readiness Quiz",
    "q1":            "Are you registered to vote?",
    "q2":            "Do you have your Voter ID card?",
    "q3":            "Do you know where your polling station is?",
    "yes":           "YES",
    "no":            "NO",
    "quiz_success":  "You are fully ready to vote! Great job!",
    "quiz_warning":  "You have a few things to sort out before voting day. Ask our AI for help!",
    "timeline_title":"Election Timeline",
    "phase_1":       "Nomination Phase",
    "phase_2":       "Campaigning Phase",
    "phase_3":       "Polling Day",
    "phase_4":       "Counting Day",
    "translating":   "Translating Interface..."
}

# ─── In-Memory Translation Cache ──────────────────────────────────────────────
# Pre-populated with English to avoid any API call for the default language.
# All other languages are loaded from the pre-generated static JSON file below.
DICTIONARY_CACHE: dict = {
    "en": BASE_DICTIONARY
}

# Load pre-generated translations from disk at startup.
# This file is created by running: python generate_translations.py
# After loading, all 10 languages are served from memory — zero API cost.
TRANSLATIONS_FILE = os.path.join("static", "translations.json")
if os.path.exists(TRANSLATIONS_FILE):
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        DICTIONARY_CACHE.update(json.load(f))


# ─── Helper: Gemini Model Factory ─────────────────────────────────────────────

def get_clients(target_language: str = "en"):
    """
    Returns initialized API clients and a language-specific Gemini model instance.

    For performance, Gemini models are cached per language code. The first call
    for a given language creates and caches the model; subsequent calls return
    the cached instance immediately.

    Args:
        target_language (str): BCP-47 language code for the desired AI response
                               language. Defaults to "en" (English).

    Returns:
        tuple: (translate_client, tts_client, gemini_model)
               Returns (None, None, None) in mock_mode.
    """
    if settings.mock_mode:
        return None, None, None

    # Return cached model if it already exists for this language
    if target_language in GEMINI_MODEL_CACHE:
        return TRANSLATE_CLIENT, TTS_CLIENT, GEMINI_MODEL_CACHE[target_language]

    # Map ISO 639-1 language codes to full language names for the system prompt
    lang_map = {
        "en": "English", "hi": "Hindi",  "ta": "Tamil",
        "te": "Telugu",  "bn": "Bengali", "mr": "Marathi",
        "gu": "Gujarati","kn": "Kannada", "ml": "Malayalam",
        "pa": "Punjabi"
    }
    lang_name = lang_map.get(target_language, "English")

    # System instruction enforces political neutrality and Indian electoral context.
    # The language directive ensures the model responds in the user's chosen language.
    system_instruction = (
        f"You are a politically neutral Electoral AI assistant for the Election Commission of India. "
        f"Your sole purpose is to provide factual, procedural information regarding Indian elections, "
        f"voting mechanics, voter registration (like Form 6, EPIC, NVSP), and schedules. "
        f"Do not express political opinions, biases, or comment on specific candidates or political events. "
        f"YOU MUST RESPOND STRICTLY IN {lang_name.upper()}."
    )

    # Safety filters: block medium and above for all harm categories
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT:        HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:       HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    # Create a new GenerativeModel instance with the language-specific system prompt
    model = GenerativeModel(
        "gemini-2.5-flash",
        safety_settings=safety_settings,
        system_instruction=[system_instruction]
    )

    # Cache the model for future requests in this language
    GEMINI_MODEL_CACHE[target_language] = model
    return TRANSLATE_CLIENT, TTS_CLIENT, model


# ─── API Endpoints ────────────────────────────────────────────────────────────

@router.get("/health", summary="Health Check")
async def health_check():
    """
    Returns the operational status of the backend service.
    Used by Cloud Run and monitoring tools to verify the container is healthy.
    """
    return {"status": "ok", "mock_mode": settings.mock_mode}


@router.get("/dictionary", summary="Get UI Translation Dictionary")
async def get_dictionary(lang: str = "en"):
    """
    Returns the complete UI translation dictionary for the requested language.

    Translations are served entirely from the pre-generated `translations.json`
    file loaded into memory at startup — making this endpoint near-instant and
    completely free at runtime (no Google Translation API calls are made).

    Args:
        lang (str): ISO 639-1 language code (e.g., "hi", "ta", "en").

    Returns:
        dict: Key-value pairs of UI string keys to their translated values.
              Falls back to English if the requested language is not available.
    """
    if lang in DICTIONARY_CACHE:
        return DICTIONARY_CACHE[lang]

    # Graceful fallback: return English if language is not in the pre-generated cache
    return DICTIONARY_CACHE.get("en", BASE_DICTIONARY)


@router.post("/translate", summary="Translate Text")
async def translate_text(req: TranslateRequest):
    """
    Translates a given text string into the specified target language.

    Primarily used for translating voice navigation confirmation messages
    (e.g., "Moving to the Election Timeline now") into the user's language
    before passing them to the TTS engine.

    Args:
        req (TranslateRequest): Contains `text` and `target_language`.

    Returns:
        dict: {"translated_text": str}

    Raises:
        HTTPException 500: If the Google Translation API call fails.
    """
    if settings.mock_mode:
        return {"translated_text": f"[{req.target_language.upper()}] {req.text}"}

    try:
        translate_client, _, _ = get_clients()
        result = translate_client.translate(req.text, target_language=req.target_language)
        return {"translated_text": result["translatedText"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts", summary="Text to Speech")
async def text_to_speech(req: TTSRequest):
    """
    Converts a text string into spoken audio using Google Cloud Text-to-Speech.

    The audio is returned as a Base64-encoded MP3 string, which the frontend
    plays directly via the Web Audio API without any file storage.

    Language codes are mapped to BCP-47 locale codes required by the TTS API
    (e.g., "hi" → "hi-IN", "ta" → "ta-IN").

    Args:
        req (TTSRequest): Contains `text` (string to speak) and `language` (ISO code).

    Returns:
        dict: {"audio_base64": str} — Base64-encoded MP3 audio content.

    Raises:
        HTTPException 500: If the Google TTS API call fails.
    """
    if settings.mock_mode:
        # Return a minimal valid silent MP3 in Base64 for testing
        return {"audio_base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU5LjE2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWgAAAAA=="}

    try:
        _, tts_client, _ = get_clients()

        # Map ISO 639-1 codes to BCP-47 locale codes for TTS voice selection
        tts_lang_map = {
            "en": "en-US", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN",
            "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
            "ml": "ml-IN", "pa": "pa-IN"
        }
        bcp47 = tts_lang_map.get(req.language, "en-US")

        # Build the TTS synthesis request
        synthesis_input = texttospeech.SynthesisInput(text=req.text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=bcp47,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL  # Gender-neutral voice
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3  # MP3 for broad browser compatibility
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Encode the raw audio bytes to Base64 for JSON transport
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        return {"audio_base64": audio_b64}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", summary="Ask the Electoral AI")
async def ask_gemini(req: AskRequest):
    """
    Sends a voter's question to Gemini 2.5 Flash via Vertex AI and returns the answer.

    The Gemini model is pre-configured with a system instruction that:
      - Locks responses to Indian electoral topics only (ECI, NVSP, Form 6, EPIC, etc.)
      - Enforces strict political neutrality
      - Forces the response to be in the user's selected language

    Retry Logic:
        On a 429 (quota exceeded) error, the handler will wait 5 seconds and
        retry up to 3 times before propagating the error to the client.

    Args:
        req (AskRequest): Contains the `question` (user query) and
                          `target_language` (ISO code for the response language).

    Returns:
        dict: {"answer": str} — The AI-generated response text.

    Raises:
        HTTPException 500: If all retry attempts fail or another error occurs.
    """
    if settings.mock_mode:
        mock_response = "This is a mock answer about the election. Mock Mode is currently ON."
        if req.target_language != "en":
            mock_response = f"[{req.target_language.upper()}] {mock_response}"
        return {"answer": mock_response}

    try:
        _, _, gemini_model = get_clients(req.target_language)
        prompt = f"Answer the following question accurately and concisely: {req.question}"

        # Retry loop: handles transient 429 quota errors from Vertex AI
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = gemini_model.generate_content(prompt)
                return {"answer": response.text}
            except Exception as e:
                error_str = str(e)
                is_quota_error = "429" in error_str
                is_last_attempt = attempt >= max_retries - 1

                if is_quota_error and not is_last_attempt:
                    # Wait before retrying to allow quota to reset
                    time.sleep(5)
                    continue
                else:
                    raise HTTPException(status_code=500, detail=error_str)

    except HTTPException:
        raise  # Re-raise HTTPExceptions without wrapping them again
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
