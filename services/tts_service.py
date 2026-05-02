"""
services/tts_service.py — Google Cloud Text-to-Speech Service Layer
====================================================================
Encapsulates all interactions with the Google Cloud Text-to-Speech API.
This service is responsible for:
  - Mapping ISO 639-1 language codes to BCP-47 locale codes for voice selection
  - Building and executing TTS synthesis requests
  - Returning audio as Base64-encoded MP3 for JSON transport

Design Principle:
    Route handlers call `synthesize_speech()` and receive a ready-to-serve
    Base64 string. All TTS SDK details are confined to this module.

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import base64
from typing import Optional

from google.cloud import texttospeech

from config import settings
from data.electoral_data import TTS_LANGUAGE_MAP


# ─── Mock Audio Constant ──────────────────────────────────────────────────────
# A minimal valid silent MP3 in Base64 format, used as the TTS stub in mock mode.
# This is a real valid MP3 header so the frontend audio player doesn't error.
_MOCK_AUDIO_BASE64: str = (
    "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU5LjE2LjEwMAAAAAAAAAAAAAAA"
    "//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWgAAAAA=="
)


def synthesize_speech(
    text: str,
    language_code: str,
    tts_client: Optional[texttospeech.TextToSpeechClient] = None,
) -> str:
    """
    Converts a text string to spoken audio and returns it as a Base64-encoded MP3.

    In mock_mode, returns a static silent MP3 without making any API call.
    In production, sends the text to Google Cloud Text-to-Speech using a
    gender-neutral voice for the specified language, and encodes the resulting
    audio bytes as Base64 for inclusion in the JSON response.

    Args:
        text (str): The text to synthesize into speech. Can be empty.
        language_code (str): ISO 639-1 language code for voice selection
                             (e.g., "hi", "ta", "en"). Unknown codes fall back to "en-US".
        tts_client (Optional[texttospeech.TextToSpeechClient]): An initialized
                             Google TTS client. Must be provided in production mode.

    Returns:
        str: Base64-encoded MP3 audio content string.

    Raises:
        ValueError: If tts_client is None in production mode.
        Exception: If the TTS API call fails.

    Example:
        >>> client = texttospeech.TextToSpeechClient()
        >>> audio_b64 = synthesize_speech("Vote today", "hi", client)
        >>> # audio_b64 is a Base64 MP3 string
    """
    # ── Mock Mode Path ──────────────────────────────────────────────────────
    if settings.mock_mode:
        return _MOCK_AUDIO_BASE64

    # ── Production Path ─────────────────────────────────────────────────────
    if tts_client is None:
        raise ValueError("tts_client must be provided in production mode.")

    # Map ISO 639-1 code to BCP-47 locale; fall back to en-US for unknown codes
    bcp47_code: str = TTS_LANGUAGE_MAP.get(language_code, "en-US")

    # Build the TTS synthesis request components
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=bcp47_code,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,  # Gender-neutral for inclusivity
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,  # MP3 for broad browser compatibility
    )

    # Execute synthesis and encode result as Base64 for JSON transport
    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config,
    )
    return base64.b64encode(response.audio_content).decode("utf-8")
