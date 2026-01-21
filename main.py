import os
import aiofiles
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langdetect import detect
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# CONFIGURACIÓN
# =========================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 SERVIR CARPETA STATIC
app.mount("/static", StaticFiles(directory="static"), name="static")

reference_language = None

# =========================
# FRONTEND
# =========================
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# =========================
# TRANSCRIBIR, TRADUCIR Y HABLAR
# =========================
@app.post("/transcribe-translate")
async def transcribe_translate(file: UploadFile = File(...)):
    global reference_language

    temp_audio = f"temp_{uuid.uuid4()}.webm"

    async with aiofiles.open(temp_audio, "wb") as f:
        await f.write(await file.read())

    # 🎙️ WHISPER
    with open(temp_audio, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio
        )

    text = transcript.text.strip()
    if not text:
        return {"error": "No se ha detectado voz"}

    detected_language = detect(text)

    if detected_language != "es":
        reference_language = detected_language

    if detected_language == "es" and reference_language:
        target_language = reference_language
        direction = f"ES → {reference_language}"
    else:
        target_language = "es"
        direction = f"{detected_language} → ES"

    # 🧠 TRADUCCIÓN LIMPIA
    prompt = (
        f"Eres un intérprete profesional.\n"
        f"Devuelve únicamente la traducción final al idioma '{target_language}'.\n"
        f"No expliques nada.\n"
        f"No añadas comentarios.\n"
        f"No incluyas comillas.\n\n"
        f"Texto:\n{text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    translated_text = response.choices[0].message.content.strip()

    # 🔊 OPENAI TTS (voz natural)
    audio_name = f"tts_{uuid.uuid4()}.mp3"

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=translated_text
    ) as tts_response:
        tts_response.stream_to_file(audio_name)

    os.remove(temp_audio)

    return {
        "detected_language": detected_language,
        "reference_language": reference_language,
        "direction": direction,
        "original_text": text,
        "translated_text": translated_text,
        "audio_file": audio_name
    }

# =========================
# SERVIR AUDIO
# =========================
@app.get("/audio/{audio_file}")
async def get_audio(audio_file: str):
    return FileResponse(audio_file, media_type="audio/mpeg")
