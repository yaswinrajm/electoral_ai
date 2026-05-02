# 🗳️ Multilingual Electoral AI Dashboard

A voice-first, inclusive AI dashboard built for the **Google Prompt War Hackathon**. This solution empowers Indian voters — especially first-time and rural voters — with factual, accessible, multilingual guidance on elections, voter registration, and the voting process.

🚀 **Live Demo:** [https://electoral-ai-658402772794.us-central1.run.app](https://electoral-ai-658402772794.us-central1.run.app)

---

## 🎯 Chosen Vertical

**Civic Technology / Electoral Literacy**

India is the world's largest democracy, yet millions of voters — particularly first-time voters, senior citizens, and those in rural or non-English-speaking communities — lack easy access to clear, unbiased information about how to register, where to vote, and what to expect on polling day.

This solution directly addresses the information gap in **electoral literacy** by making voter guidance:
- **Voice-driven** (for low-literacy or differently-abled users)
- **Multilingual** (10 Indian languages, including Hindi, Tamil, Telugu, Bengali)
- **AI-powered** (instant Q&A using Gemini 2.5 Flash via Vertex AI)
- **Accessible** (high-contrast UI, large fonts, WCAG 2.1 AA design principles)

---

## 💡 Approach and Logic

The core design principle was **"Voice First, Language Agnostic"** — the app must work for a voter regardless of whether they are literate, comfortable with English, or familiar with technology.

### Design Decisions:
1. **Voice as the primary input:** Instead of typing, users speak their question. The browser's Web Speech API captures audio, sends it to the backend, and the AI responds with both text and spoken audio (Text-to-Speech).
2. **Gemini as the Knowledge Engine:** A carefully crafted system prompt locks Gemini 2.5 Flash to only provide factual, neutral, India-specific electoral information. It explicitly blocks political opinions.
3. **No Cold-Translation Cost:** All UI strings (labels, buttons, headings) were pre-translated into all 10 languages using the Google Translation API and saved into a static `translations.json`. This means language switching is instant and costs $0 at runtime.
4. **Voice-to-Action Navigation:** Keyword detection in transcribed speech (e.g., "Timeline", "Practice", "Quiz") automatically scrolls the user to the relevant section with an audio confirmation.

---

## ⚙️ How the Solution Works

```
User speaks → Web Speech API transcribes audio
    ↓
Frontend detects keywords → Triggers navigation or sends to backend
    ↓
Backend (FastAPI) receives question + target language
    ↓
Google Translation API translates question to English (if needed)
    ↓
Vertex AI (Gemini 2.5 Flash) generates a neutral, factual response
    ↓
Google Text-to-Speech converts response to audio in user's language
    ↓
Frontend plays audio + displays text response
```

### Key Components:

| Component | File | Role |
|---|---|---|
| AI Engine | `api/routes.py` | Handles Gemini inference, translation, TTS |
| Voice Logic | `static/js/app.js` | Speech recognition, keyword detection, audio playback |
| UI Dashboard | `templates/index.html` | High-contrast, accessible, multilingual interface |
| Translation Cache | `static/translations.json` | Pre-baked UI translations (zero-cost at runtime) |
| Config | `config.py` | Environment and credential management |

### Features:
- **🎙️ Voice-First Interaction:** Ask questions hands-free in any supported language.
- **🌍 10 Indian Languages:** English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi.
- **🗳️ Virtual Ballot Simulator:** Practice using the EVM (Electronic Voting Machine) before polling day.
- **📊 Smart Election Timeline:** Interactive visual guide through Nomination, Campaigning, Polling, and Counting phases.
- **✅ Voter Readiness Quiz:** Quick checklist — Voter ID, registration, polling booth awareness.

---

## 🏗️ Architecture

```
Cloud Run Container
├── FastAPI (main.py)
│   └── /api/routes.py
│       ├── GET  /health
│       ├── GET  /dictionary?lang=hi   (static translation cache)
│       ├── POST /ask                  (Gemini 2.5 Flash via Vertex AI)
│       ├── POST /translate            (Google Translation API)
│       └── POST /tts                  (Google Text-to-Speech)
└── Static Files
    ├── templates/index.html
    ├── static/js/app.js
    ├── static/css/style.css
    └── static/translations.json
```

**Deployment:** Google Cloud Run (auto-scales to zero, pay-per-request)
**Auth:** Service Account with Vertex AI User + Translation API roles

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Frontend | Vanilla JS, HTML5, Tailwind CSS |
| AI Model | Gemini 2.5 Flash (via Google Vertex AI) |
| Translation | Google Cloud Translation API v2 |
| Voice Output | Google Cloud Text-to-Speech API |
| Voice Input | Browser Web Speech API |
| Deployment | Google Cloud Run + Docker |
| Source Control | GitHub |

---

## 📌 Assumptions Made

1. **India-specific context only:** The AI is configured via system prompt to answer questions exclusively about Indian elections (ECI rules, NVSP, Form 6, EPIC). Questions about other countries are out of scope by design.
2. **Browser must support Web Speech API:** Voice input depends on the browser's built-in speech recognition. Chrome is recommended. Safari and Firefox may have limited support.
3. **Party names are fictional:** The "Practice Voting Booth" uses generic party symbols (Lotus, Hand, Elephant, Cycle) but labels them as fictional candidates to maintain strict political neutrality.
4. **Translation accuracy:** Machine translations via Google Translate are used for UI strings. While accurate for standard text, domain-specific electoral terminology may occasionally differ from official government translations.
5. **Single user session:** The app does not persist conversation history across sessions. Each page refresh starts a fresh conversation with the AI.
6. **TTS Language Mapping:** Text-to-Speech language codes are mapped to major Indian regional locales (e.g., `hi-IN`, `ta-IN`). Dialectal variations within a language are not currently handled.

---

## 📜 Neutrality & Safety

This AI is strictly configured to remain **politically neutral**. Gemini 2.5 Flash is initialized with a custom system instruction that:
- Restricts responses to factual, procedural electoral information only.
- Explicitly prohibits political opinions, candidate commentary, or party endorsements.
- Enforces `BLOCK_MEDIUM_AND_ABOVE` safety filters across all harm categories.

---

## 🚀 Getting Started (Local)

```bash
# Clone the repo
git clone https://github.com/yaswinrajm/electoral_ai.git
cd electoral_ai

# Install dependencies
pip install -r requirements.txt

# Add your GCP credentials
# Place gcp-key.json in the root and update .env:
# GOOGLE_APPLICATION_CREDENTIALS=gcp-key.json

# Run the server
uvicorn main:app --reload --port 8080
```

Visit `http://localhost:8080`

---

## 🏆 Hackathon

Built for the **Google Prompt War Hackathon** using Google Cloud Vertex AI, Cloud Run, Translation API, and Text-to-Speech API.

---

Developed with ❤️ by **Yaswin Raj M**
