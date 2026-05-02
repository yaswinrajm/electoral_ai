import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
import json
import base64
import vertexai
from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech

router = APIRouter()

# Global Client Cache
TRANSLATE_CLIENT = None
TTS_CLIENT = None
GEMINI_MODEL_CACHE = {}

def init_clients():
    global TRANSLATE_CLIENT, TTS_CLIENT
    if settings.mock_mode:
        return
    if TRANSLATE_CLIENT is None:
        TRANSLATE_CLIENT = translate.Client()
    if TTS_CLIENT is None:
        TTS_CLIENT = texttospeech.TextToSpeechClient()
    vertexai.init(project="daring-span-495114-b2", location="us-central1")

init_clients()

class TranslateRequest(BaseModel):
    text: str
    target_language: str

class TTSRequest(BaseModel):
    text: str
    language: str

class AskRequest(BaseModel):
    question: str
    target_language: str = "en"

# Base English Dictionary for Deep Translation
BASE_DICTIONARY = {
    "title": "Electoral AI Dashboard",
    "home": "Home",
    "features": "Features",
    "contact": "Contact",
    "core_features": "Core Features",
    "card1_title": "Real-time Analysis",
    "card1_desc": "Monitor electoral data and analytics in real-time with high accuracy models.",
    "card2_title": "Accessible Reporting",
    "card2_desc": "Generate WCAG 2.1 AA compliant reports ensuring everyone has access to vital data.",
    "learn_more": "Learn More",
    "voice_guide": "Voice Guide",
    "ask_ai": "Ask the AI:",
    "listening": "Listening...",
    "booth_title": "Practice Voting Booth",
    "booth_desc": "Practice how to vote using the electronic ballot unit below.",
    "candidate": "Candidate",
    "candidate_a": "Candidate A",
    "candidate_b": "Candidate B",
    "candidate_c": "Candidate C",
    "candidate_d": "Candidate D",
    "vote_btn": "VOTE",
    "confirm_title": "Confirm Your Vote",
    "confirm_desc": "Are you sure you want to vote for this candidate?",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "thank_you": "Thank You for Practicing!",
    "thank_you_desc": "Your vote has been simulated. This was just a practice session to help you understand the process.",
    "back_to_booth": "Try Again",
    "quiz_title": "Voter Readiness Quiz",
    "q1": "Are you registered to vote?",
    "q2": "Do you have your Voter ID card?",
    "q3": "Do you know where your polling station is?",
    "yes": "YES",
    "no": "NO",
    "quiz_success": "You are fully ready to vote! Great job!",
    "quiz_warning": "You have a few things to sort out before voting day. Ask our AI for help!",
    "timeline_title": "Election Timeline",
    "phase_1": "Nomination Phase",
    "phase_2": "Campaigning Phase",
    "phase_3": "Polling Day",
    "phase_4": "Counting Day",
    "translating": "Translating Interface..."
}

# In-memory dictionary cache: { "lang_code": { key: value } }
# Pre-populated with English to avoid unnecessary API calls
DICTIONARY_CACHE = {
    "en": BASE_DICTIONARY
}

def get_clients(target_language="en"):
    if settings.mock_mode:
        return None, None, None
        
    global GEMINI_MODEL_CACHE
    
    # Check if model for this language is already in cache
    if target_language in GEMINI_MODEL_CACHE:
        return TRANSLATE_CLIENT, TTS_CLIENT, GEMINI_MODEL_CACHE[target_language]

    # Dynamic system instruction based on language
    lang_map = {
        "en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu", 
        "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati", 
        "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi"
    }
    lang_name = lang_map.get(target_language, "English")

    system_instruction = f"You are a politically neutral Electoral AI assistant for the Election Commission of India. Your sole purpose is to provide factual, procedural information regarding Indian elections, voting mechanics, voter registration (like Form 6, EPIC, NVSP), and schedules. Do not express political opinions, biases, or comment on specific candidates or political events. YOU MUST RESPOND STRICTLY IN {lang_name.upper()}."
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    model = GenerativeModel(
        "gemini-2.5-flash",
        safety_settings=safety_settings,
        system_instruction=[system_instruction]
    )
    
    GEMINI_MODEL_CACHE[target_language] = model
    return TRANSLATE_CLIENT, TTS_CLIENT, model

@router.get("/health")
async def health_check():
    return {"status": "ok", "mock_mode": settings.mock_mode}

# Load pre-generated translations at startup
TRANSLATIONS_FILE = os.path.join("static", "translations.json")
if os.path.exists(TRANSLATIONS_FILE):
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        DICTIONARY_CACHE.update(json.load(f))

@router.get("/dictionary")
async def get_dictionary(lang: str = "en"):
    """Returns the deep translated dictionary for the requested language from local cache."""
    if lang in DICTIONARY_CACHE:
        return DICTIONARY_CACHE[lang]
        
    # Fallback to English if language not found in pre-generated cache
    return DICTIONARY_CACHE.get("en", BASE_DICTIONARY)

@router.post("/translate")
async def translate_text(req: TranslateRequest):
    if settings.mock_mode:
        return {"translated_text": f"[{req.target_language.upper()}] {req.text}"}
        
    try:
        translate_client, _, _ = get_clients()
        result = translate_client.translate(req.text, target_language=req.target_language)
        return {"translated_text": result["translatedText"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    if settings.mock_mode:
        return {"audio_base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU5LjE2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWgAAAAA=="}
        
    try:
        _, tts_client, _ = get_clients()
        from google.cloud import texttospeech
        
        # Map simple codes to BCP-47 for TTS
        tts_lang_map = {
            "en": "en-US", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN",
            "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
            "ml": "ml-IN", "pa": "pa-IN"
        }
        bcp47 = tts_lang_map.get(req.language, "en-US")
        
        synthesis_input = texttospeech.SynthesisInput(text=req.text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=bcp47,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        return {"audio_base64": audio_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_gemini(req: AskRequest):
    if settings.mock_mode:
        mock_response = "This is a mock answer about the election. Mock Mode is currently ON."
        if req.target_language != "en":
            mock_response = f"[{req.target_language.upper()}] {mock_response}"
        return {"answer": mock_response}
        
    try:
        _, _, gemini_model = get_clients(req.target_language)
        prompt = f"Answer the following question accurately and concisely: {req.question}"
        
        # Implement retry logic for 429 Quota Exceeded
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = gemini_model.generate_content(prompt)
                return {"answer": response.text}
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries - 1:
                    time.sleep(5)  # Wait 5 seconds and retry
                    continue
                else:
                    raise HTTPException(status_code=500, detail=error_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
