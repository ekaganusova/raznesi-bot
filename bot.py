import os
import logging
import threading
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# Настройки логирования
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# Flask-приложение
app = Flask(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
OWNER_ID = os.environ.get("OWNER_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Telegram Application
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    chat_id = update.message.chat_id
    logging.warning(f"ПОЛУЧЕНО: {idea}")
    try:
        logging.warning("GPT: отправляю запрос...")
        logging.warning(f"OPENAI_KEY: {OPENAI_KEY}")

        client = OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": idea}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        import traceback
        logging.error("Ошибка OpenAI:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("Что-то пошло не так. Попробуй позже.")

# Подключение обработчиков
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook настройка
async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

# Маршрут для проверки
@app.route("/", methods=["GET"])
def home():
    return "ok"

# Webhook приёмник
@app.route(f"/webhook", methods=["POST"])
async def telegram_webhook():
    try:
        logging.warning("==> ВХОД В WEBHOOK")
        update = Update.de_json(request.get_json(force=True), bot)
        logging.warning(f"ПОЛУЧЕН ОБНОВЛЕНИЕ: {request.get_json(force=True)}")
        application.update_queue.put_nowait(update)
        logging.warning("==> ДОБАВЛЕН В ОЧЕРЕДЬ")
    except Exception as e:
        logging.error("Ошибка при обработке запроса:")
        logging.error(e)
    return "ok"

# Асинхронный запуск
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_until_complete(application.updater.start_polling())

# Запуск
if __name__ == "__main__":
    logging.warning("==> ЗАПУСК ПРИЛОЖЕНИЯ")
    threading.Thread(target=run_async).start()
    app.run(host="0.0.0.0", port=10000)
