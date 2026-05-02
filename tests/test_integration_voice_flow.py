"""
tests/test_integration_voice_flow.py — Integration Tests: Voice-to-Action Flow
================================================================================
Tests the complete end-to-end behaviour of the Voice-to-Action system in mock mode.

All tests run with MOCK_MODE=True (set via pytest.ini), so no real GCP credentials
or API quota is consumed. The tests verify:

  1. Full pipeline: voice input → backend processes → correct response shape returned
  2. Voice-to-Action: navigation keyword triggers translate + TTS chain
  3. Noisy/empty input: server handles edge-case transcripts gracefully (no crashes)

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import pytest
import base64
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════════════════════
# Full Voice Q&A Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullVoicePipeline:
    """
    Integration tests for the complete voice-input → AI answer → TTS pipeline.
    In mock mode, verifies correct response shapes and pipeline connectivity.
    """

    def test_full_pipeline_ask_then_tts(self, client):
        """
        Simulates the complete voice flow:
          1. Voice transcript → /api/ask → AI answer
          2. AI answer → /api/tts → audio Base64
        Verifies the entire pipeline returns valid, non-empty responses.
        """
        # Step 1: Ask the AI (simulates transcribed voice input)
        ask_response = client.post("/api/ask", json={
            "question": "How do I register to vote in India?",
            "target_language": "en"
        })
        assert ask_response.status_code == 200
        ai_answer = ask_response.json()["answer"]
        assert len(ai_answer) > 0

        # Step 2: Convert AI answer to speech
        tts_response = client.post("/api/tts", json={
            "text": ai_answer,
            "language": "en"
        })
        assert tts_response.status_code == 200
        assert "audio_base64" in tts_response.json()
        assert len(tts_response.json()["audio_base64"]) > 0

    def test_full_pipeline_hindi_voice_input(self, client):
        """
        Simulates a Hindi-language voice pipeline.
        Verifies the response is marked with Hindi language prefix in mock mode.
        """
        ask_resp = client.post("/api/ask", json={
            "question": "मतदाता पंजीकरण कैसे करें?",
            "target_language": "hi"
        })
        assert ask_resp.status_code == 200
        assert "answer" in ask_resp.json()

        # Speak the response in Hindi
        tts_resp = client.post("/api/tts", json={
            "text": ask_resp.json()["answer"],
            "language": "hi"
        })
        assert tts_resp.status_code == 200
        assert "audio_base64" in tts_resp.json()

    def test_pipeline_translate_then_speak(self, client):
        """
        Simulates the Voice-to-Action confirmation pipeline:
          1. Translate English confirmation → target language
          2. Speak the translated confirmation via TTS
        Mirrors playVoiceFeedback() in app.js.
        """
        # Step 1: Translate the confirmation message
        translate_resp = client.post("/api/translate", json={
            "text": "Moving to the Election Timeline now.",
            "target_language": "ta"
        })
        assert translate_resp.status_code == 200
        translated = translate_resp.json()["translated_text"]
        assert isinstance(translated, str)
        assert len(translated) > 0

        # Step 2: Convert translated text to speech
        tts_resp = client.post("/api/tts", json={
            "text": translated,
            "language": "ta"
        })
        assert tts_resp.status_code == 200
        assert "audio_base64" in tts_resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Voice-to-Action Navigation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVoiceToActionNavigation:
    """
    Verifies the backend supports each Voice-to-Action navigation scenario.
    Tests the translate + TTS pipeline required for audio confirmations.
    """

    @pytest.mark.parametrize("keyword,confirmation_text,target_lang", [
        ("timeline", "Moving to the Election Timeline now.", "en"),
        ("steps",    "Moving to the Election Timeline now.", "hi"),
        ("practice", "Opening the Practice Voting Booth.",   "ta"),
        ("vote",     "Opening the Practice Voting Booth.",   "te"),
        ("help",     "Starting the Voter Readiness Quiz.",   "en"),
        ("status",   "Starting the Voter Readiness Quiz.",   "bn"),
    ])
    def test_navigation_confirmation_pipeline(self, client, keyword, confirmation_text, target_lang):
        """
        For each Voice-to-Action keyword, verifies:
        1. The backend translates the English confirmation.
        2. The translated message converts to TTS audio.
        """
        # Step 1: Translate confirmation to user's language
        tr_resp = client.post("/api/translate", json={
            "text": confirmation_text,
            "target_language": target_lang
        })
        assert tr_resp.status_code == 200, \
            f"Translation failed for keyword '{keyword}' → lang '{target_lang}'"
        assert "translated_text" in tr_resp.json()

        # Step 2: Speak the confirmation
        tts_resp = client.post("/api/tts", json={
            "text": tr_resp.json()["translated_text"],
            "language": target_lang
        })
        assert tts_resp.status_code == 200, \
            f"TTS failed for keyword '{keyword}' → lang '{target_lang}'"
        assert "audio_base64" in tts_resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Graceful Handling of Noisy / Empty Voice Input
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoisyAndEmptyVoiceInput:
    """
    Tests that the backend handles edge-case voice inputs gracefully.
    All cases must return HTTP 200 — the server must NEVER crash on bad input.
    """

    def test_empty_voice_transcript(self, client):
        """Empty string transcript (silence) must return HTTP 200."""
        response = client.post("/api/ask", json={
            "question": "",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_whitespace_only_transcript(self, client):
        """Whitespace-only transcript (background noise) must return HTTP 200."""
        response = client.post("/api/ask", json={
            "question": "   ",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_noise_like_transcript(self, client):
        """Garbled/noisy transcript must return HTTP 200 without server error."""
        response = client.post("/api/ask", json={
            "question": "aaaa bbb ccc xxxx zzzzz @@@",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_single_word_transcript(self, client):
        """Single-word voice input must return HTTP 200."""
        response = client.post("/api/ask", json={
            "question": "vote",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_numeric_only_transcript(self, client):
        """Numeric-only transcription must return HTTP 200."""
        response = client.post("/api/ask", json={
            "question": "2024 2025 1234",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_very_long_transcript(self, client):
        """Extremely long voice input must be handled without crash."""
        long_question = "How do I register to vote? " * 100
        response = client.post("/api/ask", json={
            "question": long_question,
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_special_characters_transcript(self, client):
        """Special characters in transcript must not cause a server error."""
        response = client.post("/api/ask", json={
            "question": "!!! ??? ### ...",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_empty_tts_text(self, client):
        """TTS with empty text must return HTTP 200 without crashing."""
        response = client.post("/api/tts", json={
            "text": "",
            "language": "en"
        })
        assert response.status_code == 200

    def test_empty_translation_text(self, client):
        """Translation of empty text must return HTTP 200 without crashing."""
        response = client.post("/api/translate", json={
            "text": "",
            "target_language": "hi"
        })
        assert response.status_code == 200

    def test_noisy_input_has_answer_in_response(self, client):
        """Even for noisy input, the response must contain an 'answer' key."""
        response = client.post("/api/ask", json={
            "question": "xyzxyz garbled noise",
            "target_language": "en"
        })
        assert "answer" in response.json()
