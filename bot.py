import os
import time
import logging
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

ASSEMBLYAI_TOKEN = os.getenv("ASSEMBLYAI_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ASSEMBLYAI_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
ASSEMBLYAI_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"
HEADERS = {"authorization": ASSEMBLYAI_TOKEN}

if not ASSEMBLYAI_TOKEN:
    raise RuntimeError("ASSEMBLYAI_TOKEN environment variable not set")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable not set")

async def upload_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        response = requests.post(ASSEMBLYAI_UPLOAD_URL, headers=HEADERS, data=f)
    response.raise_for_status()
    return response.json()["upload_url"]

async def request_transcript(audio_url: str) -> str:

    json = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "language_code": "uk",
    }

    json = {"audio_url": audio_url, "speaker_labels": True}

    response = requests.post(ASSEMBLYAI_TRANSCRIPT_URL, json=json, headers=HEADERS)
    response.raise_for_status()
    transcript_id = response.json()["id"]
    status_url = f"{ASSEMBLYAI_TRANSCRIPT_URL}/{transcript_id}"
    while True:
        status_resp = requests.get(status_url, headers=HEADERS)
        status_resp.raise_for_status()
        status = status_resp.json()
        if status["status"] == "completed":
            return status["text"]
        if status["status"] == "error":
            raise RuntimeError(f"Transcription failed: {status['error']}")
        time.sleep(3)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = None
    if update.message.voice:
        file = await update.message.voice.get_file()
    elif update.message.audio:
        file = await update.message.audio.get_file()
    else:
 7zm8qz-codex/переглянути-базу-коду-та-запропонувати-завдання
        await update.message.reply_text(
            "Будь ласка, надішліть аудіоповідомлення або файл."

        await update.message.reply_text("Please send an audio message or file.")

        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tf:
        await file.download_to_drive(tf.name)

        await update.message.reply_text(
            "Транскрибую… це може зайняти трохи часу"
        )

        await update.message.reply_text("Transcribing... this may take a moment")

        try:
            audio_url = await upload_audio(tf.name)
            transcript = await request_transcript(audio_url)
            await update.message.reply_text(transcript)
        finally:
            os.unlink(tf.name)

def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    app.run_polling()

if __name__ == "__main__":
    main()
