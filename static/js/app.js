document.addEventListener('DOMContentLoaded', () => {
    const langSelect = document.getElementById('language-select');
    let currentLang = langSelect.value;
    let currentDictionary = {};
    
    // Translation Logic
    async function updateLanguage() {
        currentLang = langSelect.value;
        document.documentElement.lang = currentLang;
        
        // Add a loading effect while the deep translation occurs
        document.querySelectorAll('[data-i18n]').forEach(el => {
            el.classList.add('animate-pulse', 'text-gray-400');
        });
        
        try {
            const res = await fetch(`/api/dictionary?lang=${currentLang}`);
            currentDictionary = await res.json();
            
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (currentDictionary[key]) {
                    el.innerText = currentDictionary[key];
                }
                el.classList.remove('animate-pulse', 'text-gray-400');
            });
        } catch (e) {
            console.error("Translation error", e);
            document.querySelectorAll('[data-i18n]').forEach(el => {
                el.classList.remove('animate-pulse', 'text-gray-400');
            });
        }
    }

    langSelect.addEventListener('change', updateLanguage);
    updateLanguage();

    // Voice Guide Logic
    const voiceGuideBtn = document.getElementById('voice-guide-btn');
    voiceGuideBtn.addEventListener('click', async () => {
        const textToRead = (currentDictionary.quiz_title || "") + ". " + 
                           (currentDictionary.timeline_title || "") + ". " +
                           (currentDictionary.ask_ai || "") + ". " +
                           (currentDictionary.booth_title || "");
        
        try {
            voiceGuideBtn.classList.add('opacity-50');
            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textToRead, language: currentLang })
            });
            const data = await response.json();
            
            if (data.audio_base64) {
                const audio = new Audio("data:audio/mp3;base64," + data.audio_base64);
                audio.play();
                audio.onended = () => voiceGuideBtn.classList.remove('opacity-50');
            }
        } catch (e) {
            console.error(e);
            voiceGuideBtn.classList.remove('opacity-50');
        }
    });

    // --- VOTER READINESS QUIZ LOGIC ---
    let quizScore = 0;
    const quizQuestions = document.querySelectorAll('.quiz-question');
    const quizResult = document.getElementById('quiz-result');
    const quizResultText = document.getElementById('quiz-result-text');

    document.querySelectorAll('.quiz-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const currentQ = e.target.closest('.quiz-question');
            const answer = e.target.getAttribute('data-answer');
            const index = parseInt(currentQ.getAttribute('data-question')) - 1;

            if (answer === 'yes') quizScore++;

            currentQ.classList.add('hidden');
            
            if (index + 1 < quizQuestions.length) {
                quizQuestions[index + 1].classList.remove('hidden');
            } else {
                // Quiz finished
                quizResult.classList.remove('hidden');
                if (quizScore === 3) {
                    quizResult.classList.add('bg-green-100', 'border-green-600', 'text-green-800');
                    quizResultText.innerText = currentDictionary.quiz_success || "Ready!";
                    quizResultText.setAttribute('data-i18n', 'quiz_success');
                } else {
                    quizResult.classList.add('bg-red-100', 'border-red-600', 'text-red-800');
                    quizResultText.innerText = currentDictionary.quiz_warning || "Not ready.";
                    quizResultText.setAttribute('data-i18n', 'quiz_warning');
                }
            }
        });
    });

    // --- DYNAMIC TIMELINE LOGIC ---
    const timelineSlider = document.getElementById('timeline-slider');
    const timelineCard = document.getElementById('timeline-card');
    const timelineIcon = document.getElementById('timeline-icon');
    const timelinePhaseName = document.getElementById('timeline-phase-name');

    const phases = [
        { id: "phase_1", img: "/static/images/nomination.png", alt: "Nomination Document Icon" },
        { id: "phase_2", img: "/static/images/campaigning.png", alt: "Campaigning Megaphone Icon" },
        { id: "phase_3", img: "/static/images/polling.png", alt: "Polling Ballot Box Icon" },
        { id: "phase_4", img: "/static/images/counting.png", alt: "Vote Counting Chart Icon" }
    ];

    timelineSlider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value) - 1;
        const phase = phases[val];
        
        // Add tiny bounce animation
        timelineCard.classList.remove('scale-100');
        timelineCard.classList.add('scale-95');
        
        setTimeout(() => {
            timelineIcon.src = phase.img;
            timelineIcon.alt = phase.alt;
            timelinePhaseName.setAttribute('data-i18n', phase.id);
            timelinePhaseName.innerText = currentDictionary[phase.id] || "Phase";
            
            timelineCard.classList.remove('scale-95');
            timelineCard.classList.add('scale-100');
        }, 150);
    });

    // Practice Voting Booth Logic
    const modal = document.getElementById('vote-modal');
    const modalSymbol = document.getElementById('modal-symbol');
    const modalName = document.getElementById('modal-candidate-name');
    const confirmBtn = document.getElementById('confirm-vote-btn');
    const cancelBtn = document.getElementById('cancel-vote-btn');
    const boothContent = document.getElementById('booth-content');
    const thankYouScreen = document.getElementById('thank-you-screen');
    const retryBtn = document.getElementById('back-to-booth-btn');

    function playBeep() {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, audioCtx.currentTime); 
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);

        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 1.0); 
    }

    document.querySelectorAll('.vote-action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const candidate = btn.getAttribute('data-candidate');
            const symbol = btn.getAttribute('data-symbol');
            
            modalName.innerText = candidate;
            modalSymbol.src = symbol;
            modal.classList.remove('hidden');
        });
    });

    cancelBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    confirmBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        playBeep();
        
        // Show thank you screen
        boothContent.classList.add('hidden');
        thankYouScreen.classList.remove('hidden');
    });

    retryBtn.addEventListener('click', () => {
        thankYouScreen.classList.add('hidden');
        boothContent.classList.remove('hidden');
    });

    // Voice Input (Web Speech API) + Gemini
    const micBtn = document.getElementById('mic-btn');
    const aiOutput = document.getElementById('ai-output');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        micBtn.addEventListener('click', () => {
            // Need to map the short codes to proper BCP-47 for Speech API if necessary, but 'hi', 'te' etc mostly work.
            recognition.lang = currentLang;
            recognition.start();
            aiOutput.innerText = currentDictionary.listening || "Listening...";
            micBtn.classList.add('animate-ripple', 'bg-red-600');
        });

        async function playVoiceFeedback(text) {
            try {
                // Deep Translate the feedback first
                const trResponse = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text, target_language: currentLang })
                });
                const trData = await trResponse.json();
                const translatedText = trData.translated_text || text;

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
                console.error(e);
            }
        }

        recognition.onresult = async (event) => {
            const transcript = event.results[0][0].transcript;
            const lowerTrans = transcript.toLowerCase();
            micBtn.classList.remove('animate-ripple', 'bg-red-600');
            
            // Voice-to-Action Logic
            if (lowerTrans.includes('steps') || lowerTrans.includes('timeline')) {
                aiOutput.innerText = `You: ${transcript}\nAction: Navigating to Election Timeline...`;
                document.getElementById('election-timeline').scrollIntoView({ behavior: 'smooth' });
                playVoiceFeedback("Moving to the Election Timeline now.");
                return;
            } else if (lowerTrans.includes('practice') || lowerTrans.includes('vote')) {
                aiOutput.innerText = `You: ${transcript}\nAction: Opening Virtual Ballot Simulator...`;
                document.getElementById('voting-booth').scrollIntoView({ behavior: 'smooth' });
                playVoiceFeedback("Opening the Practice Voting Booth.");
                return;
            } else if (lowerTrans.includes('help') || lowerTrans.includes('status')) {
                aiOutput.innerText = `You: ${transcript}\nAction: Starting Voter Readiness Quiz...`;
                document.getElementById('voter-quiz').scrollIntoView({ behavior: 'smooth' });
                playVoiceFeedback("Starting the Voter Readiness Quiz.");
                return;
            }

            aiOutput.innerText = `You: ${transcript}\nProcessing...`;
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: transcript, target_language: currentLang })
                });
                const data = await response.json();
                
                if (data.answer) {
                    aiOutput.innerText = `You: ${transcript}\nAI: ${data.answer}`;
                    
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
                    aiOutput.innerText = `You: ${transcript}\nAI Error: ${data.detail || 'Unknown error'}`;
                }
            } catch (e) {
                console.error(e);
                aiOutput.innerText = "Error reaching AI.";
            }
        };
        
        recognition.onerror = () => {
            micBtn.classList.remove('animate-ripple', 'bg-red-600');
            aiOutput.innerText = "Microphone error or permission denied.";
        };
    }
});
