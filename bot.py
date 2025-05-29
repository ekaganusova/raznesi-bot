import os
import logging
import asyncio
import requests

from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Инициализация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)
logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.INFO)

application = Application.builder().token(TELEGRAM_TOKEN).build()

@app.route("/")
def index():
    return "OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)

    async def process():
        await application.process_update(update)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(process())
    return "ok", 200

# Команда /start без приветствия
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass  # Ничего не отправляем

# Обработка текстов
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        logging.info("ПОЛУЧЕНО: %s", user_message)

        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": user_message}],
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )

        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        await update.message.reply_text(answer.strip() + "\n\nПродолжаем?😉")

    except Exception as e:
        logging.error("GPT ОШИБКА: %s", e)
        await update.message.reply_text("Произошла ошибка при обработке запроса 😢")

# Хендлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

def setup_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    response = requests.post(url, data={"url": f"{WEBHOOK_URL}/webhook"})
    if response.status_code == 200:
        logging.info("Webhook установлен: %s/webhook", WEBHOOK_URL)
    else:
        logging.error("Не удалось установить webhook: %s", response.text)

if __name__ == "__main__":
    setup_webhook()
    logging.info("Бот запущен и webhook установлен")
    app.run(host="0.0.0.0", port=10000)