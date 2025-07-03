# Telegram Transcription Bot

This repository contains a simple Telegram bot that receives audio messages or files, uploads them to [AssemblyAI](https://www.assemblyai.com/), and replies with the diarized transcription. The output in Telegram clearly shows which speaker said each part of the conversation.

Additionally, you can send the bot a web link. It will scan the page for audio files and send any it finds back to you.

## Requirements
- Python 3.9+
- `python-telegram-bot`
- `requests`
- `beautifulsoup4`

## Setup
1. Install the required packages:
   ```bash
   pip install python-telegram-bot requests beautifulsoup4
   ```
2. Export your API tokens as environment variables:
   ```bash
   export TELEGRAM_TOKEN=<your_telegram_bot_token>
   export ASSEMBLYAI_TOKEN=<your_assemblyai_token>
   ```
3. Run the bot:
   ```bash
   python bot.py
   ```

The bot uses polling, so simply run the script on your machine (macOS supported) and it will start listening for audio messages.
