# Electoral AI Dashboard 🗳️

> **Google Prompt War Hackathon Submission**
> A voice-first, multilingual AI assistant that empowers Indian voters to understand the electoral process in their native language.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com/)
[![Vertex AI](https://img.shields.io/badge/Google-Vertex%20AI-orange)](https://cloud.google.com/vertex-ai)
[![Cloud Run](https://img.shields.io/badge/Deployed-Cloud%20Run-blue)](https://cloud.google.com/run)
[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://electoral-ai-658402772794.us-central1.run.app)

---

## 📋 Table of Contents

- [Chosen Vertical](#-chosen-vertical)
- [Approach & Logic](#-approach--logic)
- [Solution Architecture](#-solution-architecture)
- [Project Structure](#-project-structure)
- [Configuration (.env)](#-configuration-env)
- [How to Run Locally](#-how-to-run-locally)
- [How to Run Tests](#-how-to-run-tests)
- [API Reference](#-api-reference)
- [Assumptions](#-assumptions)
- [Live Deployment](#-live-deployment)

---

## 🎯 Chosen Vertical

**Civic Technology / Democratic Access**

India has 970+ million registered voters speaking 22 official languages. The biggest barrier to voter participation is not motivation — it is **information access**. Millions of first-time voters, rural citizens, and elderly voters cannot navigate the English-centric electoral information ecosystem.

This project directly addresses that gap: a voice-first, multilingual AI agent that makes the entire Indian electoral process **understandable in 10 regional languages** — from voter registration to polling day procedure.

---

## 🧠 Approach & Logic

### Core Idea
Rather than building another chatbot, we built a **structured electoral guidance system** powered by Gemini. The system:

1. Listens to the user's spoken question (via Web Speech API)
2. Sends it to Gemini 2.5 Flash with a **strict political neutrality system prompt**
3. Forces the AI to respond **only in the user's chosen language** (not just translate after the fact)
4. Speaks the answer back via Google Cloud Text-to-Speech

### Voice-to-Action Navigation
Beyond Q&A, the app implements **Voice-to-Action**: the user can say "show me the timeline" or "practice voting" and the JavaScript keyword-detector navigates them to the correct section — making the entire dashboard hands-free.

### Multilingual Architecture
| Layer | Technology | Design Choice |
|---|---|---|
| UI Translation | Static JSON (pre-generated) | Zero runtime cost — served from memory |
| Voice Input | Browser Web Speech API | No server latency for STT |
| AI Responses | Vertex AI Gemini 2.5 Flash | Language-enforced via system prompt |
| Text-to-Speech | Google Cloud TTS | BCP-47 locale mapped per language |
| Real-time Translation | Google Cloud Translation v2 | Used only for navigation confirmations |

---

## 🏗️ Solution Architecture

```
User (Browser)
│
├── Web Speech API (client-side STT)
│     ↓ transcript
├── JavaScript (app.js)
│   ├── Keyword detection → section navigation
│   └── POST /api/ask → AI Q&A
│
└── FastAPI Backend
    ├── api/routes.py          ← Thin HTTP controller
    ├── services/
    │   ├── ai_service.py      ← Gemini inference + retry logic
    │   ├── translation_service.py  ← Google Translation API
    │   └── tts_service.py     ← Google Cloud TTS → Base64 MP3
    ├── data/
    │   └── electoral_data.py  ← All static constants (dict, maps, phases)
    └── config.py              ← Environment-driven settings (no hardcoded secrets)
          ↓
    Google Cloud APIs (Vertex AI, Translation, TTS)
```

### Key Design Decisions
- **Module-level client initialization**: Google SDK clients are created once at startup, not per-request. Eliminates cold-start latency from ~2000ms to ~50ms per request.
- **Static translation caching**: All 10 language UI dictionaries are pre-generated to `static/translations.json` by `generate_translations.py`. Zero Translation API cost at runtime.
- **Per-language Gemini model cache**: One `GenerativeModel` instance per language, cached in `_GEMINI_MODEL_CACHE`. Forces the model to respond in the correct language via system prompt.
- **Service layer separation**: Routes are thin controllers; all business logic lives in `services/`. This enables unit testing without HTTP overhead.

---

## 📁 Project Structure

```
electoral_ai/
│
├── api/
│   └── routes.py                # HTTP endpoint controllers (thin layer)
│
├── data/
│   └── electoral_data.py        # All static constants: dictionaries, maps, phases
│
├── services/
│   ├── ai_service.py            # Gemini model factory, retry logic
│   ├── translation_service.py   # Google Translation API wrapper
│   └── tts_service.py           # Google TTS API wrapper → Base64 MP3
│
├── tests/
│   ├── conftest.py              # Pytest fixtures (GCP credentials setup)
│   ├── test_unit_endpoints.py   # Unit tests for all 5 API endpoints (37 tests)
│   ├── test_integration_voice_flow.py  # E2E voice pipeline tests (21 tests)
│   └── test_language_fallback.py       # Robustness/fallback tests (29 tests)
│
├── static/
│   ├── css/style.css            # Application styles
│   ├── js/app.js                # Voice-to-Action + UI logic
│   └── translations.json        # Pre-generated UI translations (10 languages)
│
├── templates/
│   └── index.html               # Single-page dashboard template
│
├── config.py                    # Pydantic Settings (env-driven, no hardcoded secrets)
├── main.py                      # FastAPI app bootstrap + page routes
├── generate_translations.py     # One-time script to pre-generate translations.json
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition for Cloud Run
└── .env                         # Local environment variables (NOT committed)
```

---

## ⚙️ Configuration (.env)

All settings are loaded from environment variables. Create a `.env` file in the project root:

```env
# Google Cloud Platform
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1

# Path to your GCP service account key (NEVER commit this file)
GOOGLE_APPLICATION_CREDENTIALS=./gcp-key.json

# Set to true to run without real GCP credentials (for local dev/testing)
MOCK_MODE=false
```

> ⚠️ **Security**: `gcp-key.json` and `.env` are both listed in `.gitignore`. Never commit either file.

On **Google Cloud Run**, the service uses its default service account and environment variables injected via the Cloud Run configuration — no key file needed.

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.11+
- A Google Cloud project with Vertex AI, Translation, and TTS APIs enabled
- A GCP service account key JSON file

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yaswinrajm/electoral_ai.git
cd electoral_ai

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file (see Configuration section above)

# 5. (Optional) Pre-generate UI translations
python generate_translations.py

# 6. Start the development server
uvicorn main:app --reload --port 8080

# 7. Open http://localhost:8080 in Google Chrome
```

> **Note**: Voice input requires **Google Chrome**. The Web Speech API is not fully supported in all browsers.

---

## 🧪 How to Run Tests

The test suite comprises **87 tests** across 3 files, organized into:
- **Unit tests**: Each API endpoint tested in isolation
- **Integration tests**: Full voice-input → AI answer → TTS pipeline
- **Fallback tests**: Unsupported language codes, empty inputs, noisy transcripts

### Setup

The tests use the real GCP APIs with your `gcp-key.json` credentials (set automatically by `tests/conftest.py`). No additional configuration needed.

```bash
# Run all tests with coverage report
python -m pytest tests/ --cov=api --cov=services --cov=data --cov=config --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_unit_endpoints.py -v

# Run a single test class
python -m pytest tests/test_language_fallback.py::TestDictionaryLanguageFallback -v

# Run only the fast structural tests (health + dictionary — no API calls)
python -m pytest tests/ -k "health or dictionary" -v
```

> **Performance Note**: Each test makes real API calls to Gemini/TTS/Translation. The full suite takes ~15 minutes due to API latency. For rapid iteration, use the `-k` flag to run specific tests.

### Test Coverage Summary

| File | Tests | Coverage |
|---|---|---|
| `test_unit_endpoints.py` | 37 | Health, Dictionary, Translate, TTS, Ask |
| `test_integration_voice_flow.py` | 21 | Full voice pipeline, navigation, noisy inputs |
| `test_language_fallback.py` | 29 | Unknown codes, edge cases, rapid switching |
| **Total** | **87** | **api/routes.py: 88%, config.py: 100%** |

---

## 📡 API Reference

All endpoints are prefixed with `/api`. Interactive docs available at `/docs` (Swagger UI).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe; returns `{"status": "ok", "mock_mode": bool}` |
| `GET` | `/api/dictionary?lang=hi` | Returns the full UI translation dictionary for the given language |
| `POST` | `/api/translate` | Translates a text string to the target language |
| `POST` | `/api/tts` | Converts text to Base64-encoded MP3 audio |
| `POST` | `/api/ask` | Submits a voter question to Gemini AI; returns the answer |

**Example — Ask the AI:**
```bash
curl -X POST https://electoral-ai-658402772794.us-central1.run.app/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I register to vote?", "target_language": "hi"}'
```

---

## 📌 Assumptions

1. **Browser compatibility**: Voice input uses the browser's native Web Speech API. Google Chrome provides the most reliable support. Firefox and Safari have partial or no support.

2. **Translation quality**: UI translations in `static/translations.json` were generated once using Google Cloud Translation API v2. They are high-quality but not professionally reviewed. For production, a native speaker review is recommended.

3. **Electoral context**: The AI is prompted to respond specifically about Indian elections governed by the Election Commission of India (ECI). Questions about elections in other countries will be politely redirected.

4. **Quota management**: The application implements 3-retry logic with 5-second delays for Gemini quota errors (429). For high-traffic deployments, upgrade the Vertex AI quota in the GCP console.

5. **Security model**: On Cloud Run, the service uses the default service account. Locally, a service account JSON key is required. The key file is excluded from version control via `.gitignore`.

6. **Static translation cache**: Adding new UI strings requires re-running `generate_translations.py` and redeploying. This is a deliberate trade-off for zero runtime translation cost.

---

## 🌐 Live Deployment

**Live URL**: [https://electoral-ai-658402772794.us-central1.run.app](https://electoral-ai-658402772794.us-central1.run.app)

Deployed on **Google Cloud Run** (`us-central1`) with:
- Auto-scaling to zero (no idle costs)
- Default Cloud Run service account (no key file in container)
- Production environment variables set via Cloud Run configuration

---

*Built with ❤️ for the Google Prompt War Hackathon by Yaswin Raj M*
