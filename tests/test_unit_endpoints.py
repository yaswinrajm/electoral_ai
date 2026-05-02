"""
tests/test_unit_endpoints.py — Unit Tests for FastAPI API Endpoints
====================================================================
Tests every individual API endpoint in isolation using MOCK_MODE=True.

In mock mode, the application bypasses all real Google Cloud SDK calls and
returns deterministic, hardcoded responses. This allows tests to:
  - Run without GCP credentials or network access
  - Execute fast (no API latency)
  - Verify endpoint routing, request validation, and response structure

Mock-mode response formats:
  /api/translate  → {"translated_text": "[<LANG>] <text>"}
  /api/tts        → {"audio_base64": "<static_base64_string>"}
  /api/ask        → {"answer": "This is a mock answer about the election. Mock Mode is currently ON."}
  /api/health     → {"status": "ok", "mock_mode": true}
  /api/dictionary → Full BASE_DICTIONARY (English) or cached translations

Endpoints tested:
  GET  /api/health          — Service health check
  GET  /api/dictionary      — UI translation dictionary retrieval
  POST /api/translate       — Text translation
  POST /api/tts             — Text-to-Speech audio synthesis
  POST /api/ask             — Gemini AI question answering (with retry logic)

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

import pytest
import base64
from fastapi.testclient import TestClient
from main import app

# Shared test client for all unit tests
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════════════════════
# /api/health
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """Unit tests for GET /api/health"""

    def test_health_returns_200(self, client):
        """Health endpoint must return HTTP 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_has_status_field(self, client):
        """Health response must include a 'status' key."""
        response = client.get("/api/health")
        assert "status" in response.json()

    def test_health_status_is_ok(self, client):
        """Health response 'status' value must be 'ok'."""
        response = client.get("/api/health")
        assert response.json()["status"] == "ok"

    def test_health_has_mock_mode_field(self, client):
        """Health response must expose the mock_mode flag."""
        response = client.get("/api/health")
        assert "mock_mode" in response.json()

    def test_health_mock_mode_is_true(self, client):
        """In test environment, mock_mode must be True."""
        response = client.get("/api/health")
        assert response.json()["mock_mode"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# /api/dictionary
# ═══════════════════════════════════════════════════════════════════════════════

class TestDictionaryEndpoint:
    """Unit tests for GET /api/dictionary"""

    def test_dictionary_english_returns_200(self, client):
        """English dictionary request must return HTTP 200."""
        response = client.get("/api/dictionary?lang=en")
        assert response.status_code == 200

    def test_dictionary_english_contains_required_keys(self, client):
        """English dictionary must contain all required UI keys."""
        required_keys = [
            "title", "home", "features", "booth_title",
            "quiz_title", "timeline_title", "vote_btn", "candidate"
        ]
        data = client.get("/api/dictionary?lang=en").json()
        for key in required_keys:
            assert key in data, f"Missing required key: '{key}'"

    def test_dictionary_english_title_value(self, client):
        """English 'title' key must return the correct dashboard title."""
        data = client.get("/api/dictionary?lang=en").json()
        assert data["title"] == "Electoral AI Dashboard"

    def test_dictionary_hindi_returns_200(self, client):
        """Hindi dictionary request must return HTTP 200."""
        response = client.get("/api/dictionary?lang=hi")
        assert response.status_code == 200

    def test_dictionary_hindi_is_non_empty(self, client):
        """Hindi dictionary must not be an empty object."""
        data = client.get("/api/dictionary?lang=hi").json()
        assert len(data) > 0

    def test_dictionary_all_supported_languages(self, client):
        """All 10 supported language codes must return valid non-empty dictionaries."""
        supported_langs = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
        for lang in supported_langs:
            response = client.get(f"/api/dictionary?lang={lang}")
            assert response.status_code == 200, f"Failed for lang: {lang}"
            assert len(response.json()) > 0, f"Empty dict for lang: {lang}"

    def test_dictionary_defaults_to_english_for_no_lang(self, client):
        """Request without lang param must default to English."""
        response = client.get("/api/dictionary")
        assert response.status_code == 200
        assert response.json()["title"] == "Electoral AI Dashboard"


# ═══════════════════════════════════════════════════════════════════════════════
# /api/translate
# ═══════════════════════════════════════════════════════════════════════════════

class TestTranslateEndpoint:
    """Unit tests for POST /api/translate (mock mode returns [LANG] prefix)"""

    def test_translate_returns_200(self, client):
        """Valid translation request must return HTTP 200."""
        response = client.post("/api/translate", json={
            "text": "How do I register to vote?",
            "target_language": "hi"
        })
        assert response.status_code == 200

    def test_translate_response_has_translated_text_key(self, client):
        """Translation response must contain 'translated_text' key."""
        response = client.post("/api/translate", json={
            "text": "Hello",
            "target_language": "ta"
        })
        assert "translated_text" in response.json()

    def test_translate_returns_string(self, client):
        """The 'translated_text' value must be a string."""
        response = client.post("/api/translate", json={
            "text": "Vote",
            "target_language": "te"
        })
        assert isinstance(response.json()["translated_text"], str)

    def test_translate_mock_response_contains_lang_prefix(self, client):
        """In mock mode, translated_text must include the target language prefix."""
        response = client.post("/api/translate", json={
            "text": "Election",
            "target_language": "hi"
        })
        translated = response.json()["translated_text"]
        assert "[HI]" in translated

    def test_translate_english_to_english(self, client):
        """Translating to the source language must not crash."""
        response = client.post("/api/translate", json={
            "text": "Election",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_translate_empty_string(self, client):
        """Empty string translation must return HTTP 200 without crashing."""
        response = client.post("/api/translate", json={
            "text": "",
            "target_language": "hi"
        })
        assert response.status_code == 200

    def test_translate_long_text(self, client):
        """Long text translation must be handled gracefully."""
        long_text = "How do I register to vote? " * 50
        response = client.post("/api/translate", json={
            "text": long_text,
            "target_language": "hi"
        })
        assert response.status_code == 200

    def test_translate_missing_text_field_returns_422(self, client):
        """Request missing 'text' field must return HTTP 422 (Unprocessable Entity)."""
        response = client.post("/api/translate", json={
            "target_language": "hi"
        })
        assert response.status_code == 422

    def test_translate_missing_language_field_returns_422(self, client):
        """Request missing 'target_language' field must return HTTP 422."""
        response = client.post("/api/translate", json={
            "text": "Hello"
        })
        assert response.status_code == 422

    def test_translate_all_10_languages(self, client):
        """Translation must succeed for all 10 supported language codes."""
        supported_langs = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
        for lang in supported_langs:
            response = client.post("/api/translate", json={
                "text": "Election",
                "target_language": lang
            })
            assert response.status_code == 200, f"Failed for lang: {lang}"
            assert "translated_text" in response.json()


# ═══════════════════════════════════════════════════════════════════════════════
# /api/tts
# ═══════════════════════════════════════════════════════════════════════════════

class TestTTSEndpoint:
    """Unit tests for POST /api/tts (Text-to-Speech). In mock mode returns static base64."""

    def test_tts_returns_200(self, client):
        """Valid TTS request must return HTTP 200."""
        response = client.post("/api/tts", json={
            "text": "Welcome to the Electoral AI.",
            "language": "en"
        })
        assert response.status_code == 200

    def test_tts_response_has_audio_base64_key(self, client):
        """TTS response must contain 'audio_base64' key."""
        response = client.post("/api/tts", json={
            "text": "Hello",
            "language": "hi"
        })
        assert "audio_base64" in response.json()

    def test_tts_audio_base64_is_non_empty_string(self, client):
        """The 'audio_base64' value must be a non-empty string."""
        response = client.post("/api/tts", json={
            "text": "Test",
            "language": "en"
        })
        audio_b64 = response.json()["audio_base64"]
        assert isinstance(audio_b64, str)
        assert len(audio_b64) > 0

    def test_tts_all_supported_languages(self, client):
        """TTS must work for all 10 supported language codes."""
        supported_langs = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
        for lang in supported_langs:
            response = client.post("/api/tts", json={
                "text": "Test audio",
                "language": lang
            })
            assert response.status_code == 200, f"TTS failed for lang: {lang}"
            assert "audio_base64" in response.json()

    def test_tts_empty_text(self, client):
        """Empty text TTS request must return HTTP 200 without crashing."""
        response = client.post("/api/tts", json={
            "text": "",
            "language": "en"
        })
        assert response.status_code == 200

    def test_tts_missing_text_field_returns_422(self, client):
        """Request missing 'text' field must return HTTP 422."""
        response = client.post("/api/tts", json={"language": "hi"})
        assert response.status_code == 422

    def test_tts_unknown_language_returns_200(self, client):
        """Unknown language must return HTTP 200 using fallback voice."""
        response = client.post("/api/tts", json={
            "text": "Test",
            "language": "xx"
        })
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# /api/ask
# ═══════════════════════════════════════════════════════════════════════════════

class TestAskEndpoint:
    """Unit tests for POST /api/ask. In mock mode returns a static answer string."""

    MOCK_ANSWER = "This is a mock answer about the election. Mock Mode is currently ON."

    def test_ask_returns_200(self, client):
        """Valid question must return HTTP 200."""
        response = client.post("/api/ask", json={
            "question": "How do I register to vote in India?",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_ask_response_has_answer_key(self, client):
        """Response must contain 'answer' key."""
        response = client.post("/api/ask", json={
            "question": "What is EPIC?",
            "target_language": "en"
        })
        assert "answer" in response.json()

    def test_ask_answer_is_non_empty_string(self, client):
        """The 'answer' value must be a non-empty string."""
        response = client.post("/api/ask", json={
            "question": "What is Form 6?",
            "target_language": "en"
        })
        answer = response.json()["answer"]
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_ask_mock_english_answer(self, client):
        """In mock mode with English, 'answer' must be the standard mock string."""
        response = client.post("/api/ask", json={
            "question": "What is NVSP?",
            "target_language": "en"
        })
        assert response.json()["answer"] == self.MOCK_ANSWER

    def test_ask_mock_non_english_adds_prefix(self, client):
        """In mock mode with non-English, 'answer' must include the language prefix."""
        response = client.post("/api/ask", json={
            "question": "How to vote?",
            "target_language": "hi"
        })
        answer = response.json()["answer"]
        assert "[HI]" in answer

    def test_ask_default_language_is_english(self, client):
        """Ask request without target_language must default to English (not crash)."""
        response = client.post("/api/ask", json={
            "question": "What is NVSP?"
        })
        assert response.status_code == 200

    def test_ask_missing_question_returns_422(self, client):
        """Request missing 'question' field must return HTTP 422."""
        response = client.post("/api/ask", json={
            "target_language": "en"
        })
        assert response.status_code == 422

    def test_ask_empty_question_returns_200(self, client):
        """Empty question string must return HTTP 200 without crashing."""
        response = client.post("/api/ask", json={
            "question": "",
            "target_language": "en"
        })
        assert response.status_code == 200

    def test_ask_all_supported_languages(self, client):
        """Asking in each supported language must return HTTP 200."""
        for lang in ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]:
            response = client.post("/api/ask", json={
                "question": "How do I vote?",
                "target_language": lang
            })
            assert response.status_code == 200, f"Failed for lang: {lang}"
            assert "answer" in response.json()
