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
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "language_code": "uk",
        "speech_model": "best",
        "format_text": True,
    }
    resp = requests.post(ASSEMBLYAI_TRANSCRIPT_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    transcript_id = resp.json()["id"]
    status_url = f"{ASSEMBLYAI_TRANSCRIPT_URL}/{transcript_id}"

    while True:
        status_resp = requests.get(status_url, headers=HEADERS)
        status_resp.raise_for_status()
        data = status_resp.json()

        if data["status"] == "completed":
            utterances = data.get("utterances")
            if utterances:
                parts = []
                for utt in utterances:
                    # номер спикера +1, если это число
                    sp = utt.get("speaker")
                    try:
                        label = f"Speaker {int(sp) + 1}"
                    except:
                        label = f"Speaker {sp}"
                    text = utt.get("text", "").strip()
                    parts.append(f"{label}: {text}")
                return "\n".join(parts)
            return data.get("text", "")

        if data["status"] == "error":
            raise RuntimeError(f"Transcription failed: {data.get('error')}")

        time.sleep(3)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = None
    if update.message.voice:
        file = await update.message.voice.get_file()
    elif update.message.audio:
        file = await update.message.audio.get_file()
    else:
        await update.message.reply_text(
            "Будь ласка, надішліть аудіоповідомлення або файл."
        )
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tf:
        await file.download_to_drive(tf.name)
        await update.message.reply_text(
            "Транскрибую… це може зайняти трохи часу"
        )
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
