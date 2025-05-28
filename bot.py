import os
import logging
import asyncio
import traceback 
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# Настройки
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")

# Flask
app = Flask(__name__)

# Telegram
application = Application.builder().token(BOT_TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔥ЖМУ НА КНОПКУ🔥", url="https://t.me/ekaterina_ganusova")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "Привет!\n"
        "Я бот, созданный с помощью AI✨, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разнос как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос.\n"
        "3. Если есть вопросы или хочешь такого же бота — жми на кнопку👇🏻"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

# Ответ на сообщение
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logging.warning("==> ПОЛУЧЕН WEBHOOK")

        update = Update.de_json(data, application.bot)

        # Логируем входящий текст (если это сообщение)
        if update.message:
            logging.info(f"ТЕКСТ СООБЩЕНИЯ: {update.message.text}")
        elif update.callback_query:
            logging.info(f"CALLBACK: {update.callback_query.data}")

        # Обработка обновления
        asyncio.run(application.process_update(update))

    except Exception as e:
        logging.error("Ошибка webhook:")
        logging.exception(e)

    return "ok"
    
# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask routes
@app.route("/")
def index():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logging.warning("==> ПОЛУЧЕН WEBHOOK")
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        logging.error("Ошибка webhook:")
        logging.error(e)
    return "ok"

# Установка webhook
async def setup_webhook():
    logging.warning("==> НАСТРОЙКА ВЕБХУКА")
    await application.initialize()
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await application.start()

# Запуск
if __name__ == "__main__":
    import threading
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_webhook())
    threading.Thread(target=run).start()

    app.run(host="0.0.0.0", port=10000)