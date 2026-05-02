# 🗳️ Multilingual Electoral AI Dashboard

A voice-first, inclusive dashboard designed for the **Google Prompt War Hackathon**. This AI assistant empowers Indian voters by providing factual, procedural, and multilingual information about elections, registration, and voting mechanics.

🚀 **Live Demo:** [https://electoral-ai-658402772794.us-central1.run.app](https://electoral-ai-658402772794.us-central1.run.app)

---

## ✨ Key Features

- **🎙️ Voice-First Interaction:** Hands-free navigation and querying designed for accessibility.
- **🌍 10+ Indian Languages:** Instant switching between English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, and Punjabi.
- **🤖 Vertex AI (Gemini 2.5 Flash):** Enterprise-grade AI responses for neutral, factual electoral guidance.
- **🗳️ Virtual Ballot Simulator:** A practice booth for voters to familiarize themselves with the electronic voting process.
- **📊 Smart Election Timeline:** Interactive visualization of the election phases (Nomination, Campaigning, Polling, Counting).
- **✅ Voter Readiness Quiz:** Quick interactive checklist to ensure voters have their IDs and registrations ready.
- **⚡ High Performance:** Optimized with static translation caching and warm-initialized SDKs for near-zero latency.

---

## 🛠️ Tech Stack

- **Backend:** Python (FastAPI, Uvicorn)
- **Frontend:** Vanilla JS, HTML5, CSS3 (Tailwind CSS)
- **AI/ML:** Google Vertex AI (Gemini 2.5 Flash)
- **Cloud APIs:** Google Cloud Translation API, Google Text-to-Speech API
- **Deployment:** Google Cloud Run (Containerized via Docker)
- **CI/CD:** GitHub

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Google Cloud Project with Vertex AI, Translation, and TTS APIs enabled.
- Service Account Key (`gcp-key.json`) with necessary permissions.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yaswinrajm/electoral_ai.git
   cd electoral_ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=gcp-key.json
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --reload --port 8080
   ```

5. **Open in Browser:**
   Go to `http://localhost:8080`

---

## 🏗️ Architecture

The app uses a modular structure:
- `api/routes.py`: Core logic for AI inference, translation, and TTS.
- `static/js/app.js`: Frontend logic for voice interaction and UI updates.
- `templates/index.html`: The premium, high-contrast dashboard UI.
- `generate_translations.py`: Utility script to pre-cache UI strings for 100% credit efficiency.

---

## 📜 Neutrality & Safety
This AI is strictly configured to remain politically neutral. It uses **Gemini 2.5 Flash** with custom system instructions to provide only procedural and factual information, avoiding any political bias or candidate commentary.

---

## 🏆 Hackathon Credits
Built for the **Google Prompt War Hackathon** using Google Cloud Vertex AI and Cloud Run.

---

Developed with ❤️ by **Yaswin Raj M**
