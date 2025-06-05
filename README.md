# Telegram Merge Bot

This bot collects forwarded messages and merges them on command.

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

Set the `TELEGRAM_BOT_TOKEN` environment variable and start the bot:

```bash
export TELEGRAM_BOT_TOKEN=YOUR_TOKEN
python bot.py
```

Use `/start` to see help. Forward messages, then `/merge` to get the combined text. Use `/clear` to drop stored messages and `/rename` to set custom participant names.
