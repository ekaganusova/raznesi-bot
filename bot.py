import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    Application
)
from openai import OpenAI
import asyncio
import threading

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Настройка логов
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

# OpenAI клиент
client = OpenAI(api_key=OPENAI_KEY)

# Flask-приложение
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Telegram-приложение
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА КОМАНДЫ /start")
    await update.message.reply_text(
        "Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог."
    )

# Сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logging.warning(f"ПОЛУЧЕНО: {user_input}")

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
        logging.warning("GPT: отправляю запрос...")

        client = OpenAI(api_key=OPENAI_KEY)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты дерзкий, уверенный маркетолог Екатерина. Пиши с юмором, кратко, метко."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        logging.warning("GPT: ответ получен")
        await update.message.reply_text(answer)

    except Exception as e:
        import traceback
        logging.error("Ошибка OpenAI:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("Что-то пошло не так. Попробуй позже.")

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook обработка
@app.route("/")
def index():
    return "Разнеси работает!"

@app.route("/webhook", methods=["POST"])
def webhook():
    logging.warning("==> ВХОД В WEBHOOK")
    try:
        data = request.get_json(force=True)
        logging.warning(f"ПОЛУЧЕН ОБНОВЛЕНИЕ: {data}")
        update = Update.de_json(data, bot)
        application.update_queue.put_nowait(update)
        logging.warning("==> ДОБАВЛЕН В ОЧЕРЕДЬ")
    except Exception as e:
        logging.warning(f"==> ОШИБКА В WEBHOOK: {e}")
    return "ok"

# Webhook настройка
async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

# Асинхронный запуск Telegram-приложения
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

# Запуск
if __name__ == "__main__":
    threading.Thread(target=run_async).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
