/* voice.js
 * Drives the "buddy" chat/voice widget on the Design Studio page.
 * Uses the browser's built-in Web Speech API for both:
 *   - Speech-to-Text (SpeechRecognition) when the mic button is pressed
 *   - Text-to-Speech (speechSynthesis) to read buddy's replies aloud
 * in English, Hindi, or Telugu - no server-side ASR/TTS model required.
 */

const SPEECH_CODES = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("buddy-toggle");
    const panel = document.getElementById("buddy-panel");
    const log = document.getElementById("buddy-log");
    const textInput = document.getElementById("buddy-text-input");
    const sendBtn = document.getElementById("buddy-send-btn");
    const micBtn = document.getElementById("buddy-mic-btn");
    const langSelect = document.getElementById("buddy-language");

    if (!toggleBtn) return; // widget not present on this page

    toggleBtn.addEventListener("click", () => panel.classList.toggle("hidden"));

    sendBtn.addEventListener("click", () => sendToBuddy(textInput.value));
    textInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendToBuddy(textInput.value);
    });

    micBtn.addEventListener("click", () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Voice recognition is not supported in this browser. Please type your request instead.");
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = SPEECH_CODES[langSelect.value] || "en-IN";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        micBtn.textContent = "🔴";
        recognition.start();

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            textInput.value = transcript;
            sendToBuddy(transcript);
        };
        recognition.onerror = () => {
            micBtn.textContent = "🎤";
        };
        recognition.onend = () => {
            micBtn.textContent = "🎤";
        };
    });

    async function sendToBuddy(text) {
        if (!text || !text.trim()) return;
        appendMessage("user", text);
        textInput.value = "";

        try {
            const res = await fetch("/api/agent/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text,
                    language: langSelect.value,
                    design_id: window.gruhaCurrentDesignId || null,
                }),
            });
            const data = await res.json();
            appendMessage("bot", data.reply);
            speak(data.reply, langSelect.value);
        } catch (err) {
            appendMessage("bot", "Sorry, something went wrong reaching the assistant.");
        }
    }

    function appendMessage(role, text) {
        const div = document.createElement("div");
        div.className = "buddy-msg " + role;
        div.textContent = text;
        log.appendChild(div);
        log.scrollTop = log.scrollHeight;
    }

    function speak(text, lang) {
        if (!window.speechSynthesis) return;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = SPEECH_CODES[lang] || "en-IN";
        window.speechSynthesis.speak(utterance);
    }
});
