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
from telegram.ext import Application
import threading
import asyncio

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

openai.api_key = OPENAI_KEY

# Логирование
logging.basicConfig(level=logging.INFO)

# Flask-сервер
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог."
    )

# Обработка сообщений
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
        print("GPT: отправляю запрос...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты дерзкий, уверенный маркетолог Екатерина. Пиши с юмором, кратко, метко."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        print("GPT: ответ получен")
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        print(f"ОШИБКА GPT: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй позже.")

# Telegram-приложение
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook вход
@app.route("/")
def index():
    return "Разнеси работает!"

@app.route("/webhook", methods=["POST"])
def webhook():
    print("==> ВХОД В WEBHOOK")
    try:
        data = request.get_json(force=True)
        print(f"ПОЛУЧЕН ОБНОВЛЕНИЕ: {data}")
        print(f"ТИП ОБНОВЛЕНИЯ: {data.get('message')}")
        update = Update.de_json(data, bot)
        print("==> UPDATE СОБРАН")
        application.update_queue.put_nowait(update)
        print("==> UPDATE ДОБАВЛЕН В ОЧЕРЕДЬ")
    except Exception as e:
        print(f"==> ОШИБКА В WEBHOOK: {e}")
    return "ok"

# Настройка Webhook
async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

# Асинхронный запуск
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

threading.Thread(target=run_async).start()

# Запуск сервера Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
