import os
import json
from google.cloud import translate_v2 as translate
from config import settings

# Base English Dictionary
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

LANGUAGES = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]

def generate():
    print("Initializing Google Translation Client...")
    if settings.google_application_credentials:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(settings.google_application_credentials)
    
    translate_client = translate.Client()
    full_cache = {}

    for lang in LANGUAGES:
        if lang == "en":
            full_cache["en"] = BASE_DICTIONARY
            print("Cached English (Source)")
            continue

        print(f"Translating to {lang}...")
        keys = list(BASE_DICTIONARY.keys())
        values = list(BASE_DICTIONARY.values())
        
        result = translate_client.translate(values, target_language=lang)
        
        translated_dict = {}
        for idx, item in enumerate(result):
            translated_dict[keys[idx]] = item["translatedText"]
        
        full_cache[lang] = translated_dict

    output_path = os.path.join("static", "translations.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_cache, f, ensure_ascii=False, indent=4)
    
    print(f"SUCCESS! All translations saved to {output_path}")

if __name__ == "__main__":
    generate()
