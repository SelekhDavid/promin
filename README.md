
# Телеграм-бот транскрипції

Цей репозиторій містить простий телеграм-бот, що приймає аудіо повідомлення або файли, надсилає їх до [AssemblyAI](https://www.assemblyai.com/) і повертає розділену за мовцями транскрипцію. Мова інтерфейсу бота та транскрипцій — українська.

## Вимоги

# Telegram Transcription Bot

This repository contains a simple Telegram bot that receives audio messages or files, uploads them to [AssemblyAI](https://www.assemblyai.com/), and replies with the diarized transcription.

## Requirements
 main
- Python 3.9+
- `python-telegram-bot`
- `requests`

## Налаштування
1. Встановіть необхідні пакети:
   ```bash
   pip install python-telegram-bot requests
   ```
2. Експортуйте ваші токени як змінні середовища:
   ```bash
   export TELEGRAM_TOKEN=<ваш_токен_бота>
   export ASSEMBLYAI_TOKEN=<ваш_токен_assemblyai>
   ```
3. Запустіть бота:

## Setup
1. Install the required packages:
   ```bash
   pip install python-telegram-bot requests
   ```
2. Export your API tokens as environment variables:
   ```bash
   export TELEGRAM_TOKEN=<your_telegram_bot_token>
   export ASSEMBLYAI_TOKEN=<your_assemblyai_token>
   ```
3. Run the bot:
    main
   ```bash
   python bot.py
   ```


Бот використовує опитування, тому достатньо запустити скрипт на вашій системі (працює на macOS) і він почне очікувати аудіо.

The bot uses polling, so simply run the script on your machine (macOS supported) and it will start listening for audio messages.
main
