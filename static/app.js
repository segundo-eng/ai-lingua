let mediaRecorder;
let audioChunks = [];
let lastAudioUrl = null;

const recordBtn = document.getElementById("recordBtn");
const statusEl = document.getElementById("status");
const detectedEl = document.getElementById("detected");
const originalEl = document.getElementById("original");
const translatedEl = document.getElementById("translated");
const repeatBtn = document.getElementById("repeatBtn");
const loader = document.getElementById("loader");
const directionEl = document.getElementById("direction");
const resetBtn = document.getElementById("resetBtn");

recordBtn.onclick = async () => {

    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        recordBtn.classList.remove("recording");
        recordBtn.disabled = true;
        statusEl.textContent = "Procesando traducción…";
        statusEl.className = "status processing";
        loader.classList.remove("hidden");
        return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = sendAudio;

    mediaRecorder.start();
    recordBtn.classList.add("recording");
    statusEl.textContent = "🎧 Escuchando con atención…";
    statusEl.className = "status recording";
};

async function sendAudio() {

    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", blob, "audio.webm");

    const res = await fetch("/transcribe-translate", {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    detectedEl.textContent = data.detected_language || "---";
    originalEl.textContent = data.original_text || "---";
    translatedEl.textContent = data.translated_text || "---";
    directionEl.textContent = data.direction
        ? `🌐 Dirección de traducción: ${data.direction}`
        : "";

    statusEl.textContent = "Listo";
    statusEl.className = "status idle";
    loader.classList.add("hidden");
    recordBtn.disabled = false;

    if (data.audio_file) {
        lastAudioUrl = `/audio/${data.audio_file}`;
        repeatBtn.disabled = false;
        playAudio(lastAudioUrl);
    }
}

repeatBtn.onclick = () => {
    if (lastAudioUrl) playAudio(lastAudioUrl);
};

resetBtn.onclick = () => {
    detectedEl.textContent = "---";
    originalEl.textContent = "---";
    translatedEl.textContent = "---";
    directionEl.textContent = "";
    repeatBtn.disabled = true;
    statusEl.textContent = "Pulsa y habla con claridad (mejor frases cortas)";
};

function playAudio(url) {
    const audio = new Audio(url);
    audio.play();
}
