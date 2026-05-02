/**
 * app.js — Electoral AI Frontend Logic
 * ======================================
 * This script powers the entire client-side interactivity of the
 * Multilingual Electoral AI Dashboard. It handles:
 *
 *  1. LANGUAGE SWITCHING — Fetches pre-translated UI dictionaries from the
 *     backend and updates all `[data-i18n]` elements on the page instantly.
 *
 *  2. VOICE GUIDE — Reads out a summary of the page sections using
 *     the Google Text-to-Speech API (via /api/tts).
 *
 *  3. VOTER READINESS QUIZ — Sequential question flow with scoring logic
 *     to assess voter preparedness.
 *
 *  4. ELECTION TIMELINE — Slider-driven interactive visualization of the
 *     four election phases with animated card transitions.
 *
 *  5. PRACTICE VOTING BOOTH — Simulates the EVM (Electronic Voting Machine)
 *     flow: select a candidate → confirm → hear a beep → see thank you screen.
 *
 *  6. VOICE INPUT + AI (Web Speech API + Gemini) — The core feature.
 *     - Captures microphone input via the browser's Web Speech API.
 *     - Applies keyword detection for Voice-to-Action navigation.
 *     - Sends unmatched queries to the /api/ask endpoint (Vertex AI Gemini).
 *     - Speaks the AI response back using /api/tts.
 *
 * Author:  Yaswin Raj M
 * Project: Google Prompt War Hackathon — Multilingual Electoral AI
 */

document.addEventListener('DOMContentLoaded', () => {

    // ─── Language & Dictionary State ────────────────────────────────────────
    const langSelect = document.getElementById('language-select');
    let currentLang = langSelect.value;       // Active ISO 639-1 language code
    let currentDictionary = {};               // Holds the currently loaded translation map


    // ─── Language Switching ──────────────────────────────────────────────────

    /**
     * Fetches the translation dictionary for the currently selected language
     * and updates all `[data-i18n]` elements on the page.
     *
     * Translation dictionaries are pre-cached on the server (loaded from
     * static/translations.json), so this call is near-instant.
     */
    async function updateLanguage() {
        currentLang = langSelect.value;
        document.documentElement.lang = currentLang; // Update <html lang="..."> for accessibility

        // Show a subtle pulsing effect while loading translations
        document.querySelectorAll('[data-i18n]').forEach(el => {
            el.classList.add('animate-pulse', 'text-gray-400');
        });

        try {
            const res = await fetch(`/api/dictionary?lang=${currentLang}`);
            currentDictionary = await res.json();

            // Update every element that has a data-i18n key
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (currentDictionary[key]) {
                    el.innerText = currentDictionary[key];
                }
                el.classList.remove('animate-pulse', 'text-gray-400');
            });
        } catch (e) {
            console.error("Translation error:", e);
            // Remove loading state even on failure to avoid stuck UI
            document.querySelectorAll('[data-i18n]').forEach(el => {
                el.classList.remove('animate-pulse', 'text-gray-400');
            });
        }
    }

    // Trigger language update whenever the dropdown changes
    langSelect.addEventListener('change', updateLanguage);
    // Load the default language on first page load
    updateLanguage();


    // ─── Voice Guide ─────────────────────────────────────────────────────────

    /**
     * Reads out a spoken summary of the dashboard's main sections.
     * Uses the /api/tts endpoint to generate audio in the user's chosen language.
     */
    const voiceGuideBtn = document.getElementById('voice-guide-btn');
    voiceGuideBtn.addEventListener('click', async () => {
        // Build the summary text from the current translation dictionary
        const textToRead = (currentDictionary.quiz_title || "") + ". " +
                           (currentDictionary.timeline_title || "") + ". " +
                           (currentDictionary.ask_ai || "") + ". " +
                           (currentDictionary.booth_title || "");

        try {
            voiceGuideBtn.classList.add('opacity-50'); // Visual feedback: button is active

            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textToRead, language: currentLang })
            });
            const data = await response.json();

            if (data.audio_base64) {
                const audio = new Audio("data:audio/mp3;base64," + data.audio_base64);
                audio.play();
                // Re-enable button when audio finishes
                audio.onended = () => voiceGuideBtn.classList.remove('opacity-50');
            }
        } catch (e) {
            console.error("Voice guide error:", e);
            voiceGuideBtn.classList.remove('opacity-50');
        }
    });


    // ─── Voter Readiness Quiz ─────────────────────────────────────────────────

    /**
     * Sequential quiz flow: shows one question at a time, scores "yes" answers,
     * and displays a success or warning result when all questions are answered.
     */
    let quizScore = 0;
    const quizQuestions = document.querySelectorAll('.quiz-question');
    const quizResult = document.getElementById('quiz-result');
    const quizResultText = document.getElementById('quiz-result-text');

    document.querySelectorAll('.quiz-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const currentQ = e.target.closest('.quiz-question');
            const answer = e.target.getAttribute('data-answer');
            const index = parseInt(currentQ.getAttribute('data-question')) - 1;

            // Increment score for "yes" answers
            if (answer === 'yes') quizScore++;

            // Hide the current question and show the next one
            currentQ.classList.add('hidden');

            if (index + 1 < quizQuestions.length) {
                quizQuestions[index + 1].classList.remove('hidden');
            } else {
                // All questions answered — show result
                quizResult.classList.remove('hidden');

                if (quizScore === 3) {
                    // Full score: voter is ready
                    quizResult.classList.add('bg-green-100', 'border-green-600', 'text-green-800');
                    quizResultText.innerText = currentDictionary.quiz_success || "Ready!";
                    quizResultText.setAttribute('data-i18n', 'quiz_success');
                } else {
                    // Incomplete: voter needs to take action
                    quizResult.classList.add('bg-red-100', 'border-red-600', 'text-red-800');
                    quizResultText.innerText = currentDictionary.quiz_warning || "Not ready.";
                    quizResultText.setAttribute('data-i18n', 'quiz_warning');
                }
            }
        });
    });


    // ─── Smart Election Timeline ──────────────────────────────────────────────

    /**
     * Slider-driven phase switcher. Animates the card with a subtle scale
     * transition when the user moves between the four election phases.
     */
    const timelineSlider = document.getElementById('timeline-slider');
    const timelineCard = document.getElementById('timeline-card');
    const timelineIcon = document.getElementById('timeline-icon');
    const timelinePhaseName = document.getElementById('timeline-phase-name');

    // Phase metadata: maps slider values 1-4 to image assets and i18n keys
    const phases = [
        { id: "phase_1", img: "/static/images/nomination.png",  alt: "Nomination Document Icon" },
        { id: "phase_2", img: "/static/images/campaigning.png", alt: "Campaigning Megaphone Icon" },
        { id: "phase_3", img: "/static/images/polling.png",     alt: "Polling Ballot Box Icon" },
        { id: "phase_4", img: "/static/images/counting.png",    alt: "Vote Counting Chart Icon" }
    ];

    timelineSlider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value) - 1;
        const phase = phases[val];

        // Step 1: Animate card down (scale-out)
        timelineCard.classList.remove('scale-100');
        timelineCard.classList.add('scale-95');

        // Step 2: After 150ms, swap content and animate back in (scale-in)
        setTimeout(() => {
            timelineIcon.src = phase.img;
            timelineIcon.alt = phase.alt;
            timelinePhaseName.setAttribute('data-i18n', phase.id);
            timelinePhaseName.innerText = currentDictionary[phase.id] || "Phase";

            timelineCard.classList.remove('scale-95');
            timelineCard.classList.add('scale-100');
        }, 150);
    });


    // ─── Practice Voting Booth ────────────────────────────────────────────────

    /**
     * Simulates the EVM voting flow:
     *   1. User clicks VOTE next to a candidate
     *   2. A confirmation modal appears with the candidate's name and symbol
     *   3. User confirms → a beep sound plays → the "Thank You" screen is shown
     *   4. User can retry from the beginning
     */
    const modal = document.getElementById('vote-modal');
    const modalSymbol = document.getElementById('modal-symbol');
    const modalName = document.getElementById('modal-candidate-name');
    const confirmBtn = document.getElementById('confirm-vote-btn');
    const cancelBtn = document.getElementById('cancel-vote-btn');
    const boothContent = document.getElementById('booth-content');
    const thankYouScreen = document.getElementById('thank-you-screen');
    const retryBtn = document.getElementById('back-to-booth-btn');

    /**
     * Plays a short 800Hz sine wave beep sound to simulate the EVM
     * confirmation tone heard after pressing the VOTE button on a real machine.
     * Uses the Web Audio API for zero-latency audio generation.
     */
    function playBeep() {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, audioCtx.currentTime); // 800Hz = EVM-like tone
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);        // 50% volume

        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 1.0); // Play for 1 second
    }

    // Open confirmation modal when a VOTE button is clicked
    document.querySelectorAll('.vote-action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const candidate = btn.getAttribute('data-candidate');
            const symbol = btn.getAttribute('data-symbol');

            // Populate modal with selected candidate details
            modalName.innerText = candidate;
            modalSymbol.src = symbol;
            modal.classList.remove('hidden');
        });
    });

    // Cancel button: close modal without voting
    cancelBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    // Confirm button: close modal, play beep, show thank-you screen
    confirmBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        playBeep();
        boothContent.classList.add('hidden');
        thankYouScreen.classList.remove('hidden');
    });

    // Retry button: reset the booth to allow another practice vote
    retryBtn.addEventListener('click', () => {
        thankYouScreen.classList.add('hidden');
        boothContent.classList.remove('hidden');
    });


    // ─── Voice Input + AI Query ───────────────────────────────────────────────

    /**
     * Core voice interaction system:
     *   1. User clicks the microphone button
     *   2. Browser captures audio via Web Speech API
     *   3. Transcript is checked for navigation keywords (Voice-to-Action)
     *   4. If no keyword match, the query is sent to Gemini via /api/ask
     *   5. The AI response is displayed and spoken back via /api/tts
     */
    const micBtn = document.getElementById('mic-btn');
    const aiOutput = document.getElementById('ai-output');

    // Check if the browser supports the Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;     // Stop after first utterance
        recognition.interimResults = false; // Only final results, no live transcription

        // Start listening when the mic button is pressed
        micBtn.addEventListener('click', () => {
            recognition.lang = currentLang; // Use currently selected language for recognition
            recognition.start();
            aiOutput.innerText = currentDictionary.listening || "Listening...";
            micBtn.classList.add('animate-ripple', 'bg-red-600'); // Visual feedback
        });

        /**
         * Translates a confirmation message and plays it via TTS.
         * Used for Voice-to-Action feedback (e.g., "Moving to the Timeline now").
         *
         * @param {string} text - English confirmation message to translate and speak.
         */
        async function playVoiceFeedback(text) {
            try {
                // First, translate the confirmation message to the user's language
                const trResponse = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text, target_language: currentLang })
                });
                const trData = await trResponse.json();
                const translatedText = trData.translated_text || text;

                // Then, convert the translated text to speech
                const ttsResponse = await fetch('/api/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: translatedText, language: currentLang })
                });
                const ttsData = await ttsResponse.json();
                if (ttsData.audio_base64) {
                    new Audio("data:audio/mp3;base64," + ttsData.audio_base64).play();
                }
            } catch (e) {
                console.error("Voice feedback error:", e);
            }
        }

        /**
         * Called when the speech recognition engine produces a final result.
         * Handles two cases:
         *   A) Navigation keyword detected → scroll to section + audio confirmation.
         *   B) General question → send to Gemini API + speak the response.
         */
        recognition.onresult = async (event) => {
            const transcript = event.results[0][0].transcript;
            const lowerTrans = transcript.toLowerCase();

            // Remove visual feedback from mic button
            micBtn.classList.remove('animate-ripple', 'bg-red-600');

            // ── Voice-to-Action Navigation ───────────────────────────────────
            // Keywords trigger page scroll and audio confirmation instead of
            // sending the query to Gemini, saving API credits and reducing latency.

            if (lowerTrans.includes('steps') || lowerTrans.includes('timeline')) {
                // Navigate to the Election Timeline section
                aiOutput.innerText = `You: ${transcript}\nAction: Navigating to Election Timeline...`;
                document.getElementById('election-timeline').scrollIntoView({ behavior: 'smooth' });
                playVoiceFeedback("Moving to the Election Timeline now.");
                return;

            } else if (lowerTrans.includes('practice') || lowerTrans.includes('vote')) {
                // Navigate to the Practice Voting Booth section
                aiOutput.innerText = `You: ${transcript}\nAction: Opening Virtual Ballot Simulator...`;
                document.getElementById('voting-booth').scrollIntoView({ behavior: 'smooth' });
                playVoiceFeedback("Opening the Practice Voting Booth.");
                return;

            } else if (lowerTrans.includes('help') || lowerTrans.includes('status')) {
                // Navigate to the Voter Readiness Quiz section
                aiOutput.innerText = `You: ${transcript}\nAction: Starting Voter Readiness Quiz...`;
                document.getElementById('voter-quiz').scrollIntoView({ behavior: 'smooth' });
                playVoiceFeedback("Starting the Voter Readiness Quiz.");
                return;
            }

            // ── General AI Query ──────────────────────────────────────────────
            // No keyword matched — send the full question to Gemini via the backend.
            aiOutput.innerText = `You: ${transcript}\nProcessing...`;

            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: transcript, target_language: currentLang })
                });
                const data = await response.json();

                if (data.answer) {
                    // Display the AI's text response
                    aiOutput.innerText = `You: ${transcript}\nAI: ${data.answer}`;

                    // Speak the response back using TTS
                    const ttsResponse = await fetch('/api/tts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: data.answer, language: currentLang })
                    });
                    const ttsData = await ttsResponse.json();
                    if (ttsData.audio_base64) {
                        new Audio("data:audio/mp3;base64," + ttsData.audio_base64).play();
                    }
                } else {
                    // Display error detail from the API response if answer is missing
                    aiOutput.innerText = `You: ${transcript}\nAI Error: ${data.detail || 'Unknown error'}`;
                }
            } catch (e) {
                console.error("AI query error:", e);
                aiOutput.innerText = "Error reaching AI. Please try again.";
            }
        };

        // Handle microphone errors (e.g., permission denied)
        recognition.onerror = () => {
            micBtn.classList.remove('animate-ripple', 'bg-red-600');
            aiOutput.innerText = "Microphone error or permission denied.";
        };

    } else {
        // Browser does not support Web Speech API — hide the mic button
        console.warn("Web Speech API is not supported in this browser.");
        if (micBtn) micBtn.style.display = 'none';
    }

}); // End DOMContentLoaded
