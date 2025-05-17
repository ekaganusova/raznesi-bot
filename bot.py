import os
import openai
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from flask import Flask, request

# Переменные
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Конфигурация
openai.api_key = OPENAI_KEY
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    print(f"ПОЛУЧЕНО: {user_input}")

    prompt = f"""
Ты — опытный маркетолог. Пользователь написал идею или описание бизнеса. Сделай разбор в формате:

1. УТП — [твой ответ]
2. Проблема — [твой ответ]
3. Ошибка упаковки — [твой ответ]
4. Предложение улучшения — [твой ответ]

Заверши фразой: "Уровень боли: [оценка от 1 до 10]. Хочешь персональный разнос — пиши @ekaterina_ganusova".

Текст пользователя: {user_input}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты дерзкий, уверенный маркетолог Екатерина. Пиши с юмором, кратко, метко."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй позже.")

# Инициализация Telegram-бота
from telegram.ext import Application

application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Устанавливаем Webhook
@app.route("/")
def index():
    return "Разнеси работает!"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        application.update_queue.put_nowait(update)
        return "ok"

async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")

import threading
import asyncio

def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

threading.Thread(target=run_async).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
