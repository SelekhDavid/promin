import os
import time
import logging
import tempfile
import mimetypes
import re
from urllib.parse import urljoin
import asyncio

import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

ASSEMBLYAI_TOKEN = os.getenv("ASSEMBLYAI_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ASSEMBLYAI_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
ASSEMBLYAI_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"
HEADERS = {"authorization": ASSEMBLYAI_TOKEN}

URL_REGEX = re.compile(r"https?://\S+")

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

        await asyncio.sleep(3)

def _audio_links_from_html(html: str, base: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for audio in soup.find_all("audio"):
        src = audio.get("src")
        if src:
            links.append(urljoin(base, src))
        for source in audio.find_all("source"):
            s = source.get("src")
            if s:
                links.append(urljoin(base, s))
    for a in soup.find_all("a", href=True):
        href = a["href"]
        mime, _ = mimetypes.guess_type(href)
        if mime and mime.startswith("audio"):
            links.append(urljoin(base, href))
    return list(dict.fromkeys(links))

def _download_file(url: str) -> str:
    resp = requests.get(url)
    resp.raise_for_status()
    ext = mimetypes.guess_extension(resp.headers.get("content-type", "")) or ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tf:
        tf.write(resp.content)
        return tf.name

async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    urls = URL_REGEX.findall(text)
    if not urls:
        await update.message.reply_text("Please send a valid URL")
        return

    for url in urls:
        await update.message.reply_text(f"Fetching audio from {url}…")
        try:
            page = await asyncio.to_thread(requests.get, url)
            page.raise_for_status()
            html = page.text
            final_url = page.url
            audio_links = await asyncio.to_thread(
                _audio_links_from_html, html, final_url
            )
            if not audio_links:
                await update.message.reply_text("No audio found on the page")
                continue
            for aurl in audio_links:
                tmp = await asyncio.to_thread(_download_file, aurl)
                try:
                    with open(tmp, "rb") as f:
                        await update.message.reply_audio(f)
                finally:
                    os.unlink(tmp)
        except Exception as e:
            await update.message.reply_text(f"Failed to process {url}: {e}")

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_links))
    app.run_polling()

if __name__ == "__main__":
    main()
