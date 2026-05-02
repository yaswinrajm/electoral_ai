"""
data/electoral_data.py — Static Electoral Reference Data
==========================================================
Centralizes all static data constants used throughout the Electoral AI backend.
By isolating data from logic, we achieve:
  - Single source of truth for all UI strings, language maps, and election phases
  - Easier maintenance: updating a language or phase requires changing one file
  - Better testability: data can be imported and tested in isolation

This module is purely declarative — it contains NO business logic or I/O.

Exported Constants:
    BASE_DICTIONARY (dict[str, str]):
        Master English source for all UI labels. Used by `generate_translations.py`
        and served directly as the English dictionary by the /api/dictionary endpoint.

    LANGUAGE_MAP (dict[str, str]):
        Maps ISO 639-1 language codes to full English language names.
        Used in constructing Gemini system prompts (e.g., "hi" → "Hindi").

    TTS_LANGUAGE_MAP (dict[str, str]):
        Maps ISO 639-1 codes to BCP-47 locale codes required by Google TTS API
        (e.g., "hi" → "hi-IN"). Falls back to "en-US" for unknown codes.

    ELECTION_PHASES (list[dict]):
        Metadata for the 4 election phases shown in the interactive timeline.
        Each phase maps to an i18n key, an image asset, and an alt text.

    SUPPORTED_LANGUAGES (list[str]):
        The ordered list of ISO 639-1 language codes supported by the application.

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from typing import Dict, List


# ─── Supported Languages ──────────────────────────────────────────────────────
# All 10 supported ISO 639-1 language codes.
# Order matters: the first item is the application default (English).
SUPPORTED_LANGUAGES: List[str] = [
    "en",  # English
    "hi",  # Hindi
    "ta",  # Tamil
    "te",  # Telugu
    "bn",  # Bengali
    "mr",  # Marathi
    "gu",  # Gujarati
    "kn",  # Kannada
    "ml",  # Malayalam
    "pa",  # Punjabi
]


# ─── Language Name Map ────────────────────────────────────────────────────────
# Maps ISO 639-1 codes to full English language names for use in AI system prompts.
# When constructing a system prompt, we tell the model: "Respond in HINDI."
LANGUAGE_MAP: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
}


# ─── TTS Language Map ─────────────────────────────────────────────────────────
# Maps ISO 639-1 codes to BCP-47 locale codes required by Google Cloud TTS API.
# Unknown codes will fall back to "en-US" in the TTS service layer.
TTS_LANGUAGE_MAP: Dict[str, str] = {
    "en": "en-US",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
}


# ─── Election Phase Metadata ──────────────────────────────────────────────────
# Defines the 4 phases of an Indian election cycle for the interactive timeline.
# Each phase has an i18n key (matches BASE_DICTIONARY), image path, and alt text.
ELECTION_PHASES: List[Dict[str, str]] = [
    {
        "id": "phase_1",
        "label": "Nomination Phase",
        "img": "/static/images/nomination.png",
        "alt": "Nomination Document Icon",
    },
    {
        "id": "phase_2",
        "label": "Campaigning Phase",
        "img": "/static/images/campaigning.png",
        "alt": "Campaigning Megaphone Icon",
    },
    {
        "id": "phase_3",
        "label": "Polling Day",
        "img": "/static/images/polling.png",
        "alt": "Polling Ballot Box Icon",
    },
    {
        "id": "phase_4",
        "label": "Counting Day",
        "img": "/static/images/counting.png",
        "alt": "Vote Counting Chart Icon",
    },
]


# ─── UI Translation Dictionary ────────────────────────────────────────────────
# Master English source for all UI strings rendered via data-i18n attributes.
# Keys MUST match the `data-i18n` attribute values in templates/index.html.
#
# To add a new UI string:
#   1. Add the key-value pair here.
#   2. Add the corresponding `data-i18n="key"` attribute to index.html.
#   3. Re-run `python generate_translations.py` to update static/translations.json.
BASE_DICTIONARY: Dict[str, str] = {
    # ── Navigation ──────────────────────────────────────────────────────────
    "title":          "Electoral AI Dashboard",
    "home":           "Home",
    "features":       "Features",
    "contact":        "Contact",
    "core_features":  "Core Features",

    # ── Feature Cards ────────────────────────────────────────────────────────
    "card1_title":    "Real-time Analysis",
    "card1_desc":     "Monitor electoral data and analytics in real-time with high accuracy models.",
    "card2_title":    "Accessible Reporting",
    "card2_desc":     "Generate WCAG 2.1 AA compliant reports ensuring everyone has access to vital data.",
    "learn_more":     "Learn More",

    # ── AI Voice Interface ───────────────────────────────────────────────────
    "voice_guide":    "Voice Guide",
    "ask_ai":         "Ask the AI:",
    "listening":      "Listening...",

    # ── Practice Voting Booth ────────────────────────────────────────────────
    "booth_title":    "Practice Voting Booth",
    "booth_desc":     "Practice how to vote using the electronic ballot unit below.",
    "candidate":      "Candidate",
    "candidate_a":    "Candidate A",
    "candidate_b":    "Candidate B",
    "candidate_c":    "Candidate C",
    "candidate_d":    "Candidate D",
    "vote_btn":       "VOTE",

    # ── Confirmation Modal ───────────────────────────────────────────────────
    "confirm_title":  "Confirm Your Vote",
    "confirm_desc":   "Are you sure you want to vote for this candidate?",
    "cancel":         "Cancel",
    "confirm":        "Confirm",

    # ── Thank You Screen ─────────────────────────────────────────────────────
    "thank_you":      "Thank You for Practicing!",
    "thank_you_desc": "Your vote has been simulated. This was just a practice session to help you understand the process.",
    "back_to_booth":  "Try Again",

    # ── Voter Readiness Quiz ─────────────────────────────────────────────────
    "quiz_title":     "Voter Readiness Quiz",
    "q1":             "Are you registered to vote?",
    "q2":             "Do you have your Voter ID card?",
    "q3":             "Do you know where your polling station is?",
    "yes":            "YES",
    "no":             "NO",
    "quiz_success":   "You are fully ready to vote! Great job!",
    "quiz_warning":   "You have a few things to sort out before voting day. Ask our AI for help!",

    # ── Election Timeline ────────────────────────────────────────────────────
    "timeline_title": "Election Timeline",
    "phase_1":        "Nomination Phase",
    "phase_2":        "Campaigning Phase",
    "phase_3":        "Polling Day",
    "phase_4":        "Counting Day",

    # ── General ──────────────────────────────────────────────────────────────
    "translating":    "Translating Interface...",
}
