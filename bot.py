import os
import logging
import threading
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# Настройка логов
logging.basicConfig(level=logging.WARNING, format="%(asctime)s — %(levelname)s — %(message)s")

# Flask-приложение
app = Flask(__name__)

# Настройки
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Создание приложения Telegram
application = Application.builder().token(BOT_TOKEN).build()
loop = asyncio.new_event_loop()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova")],
        [InlineKeyboardButton("Отличный разбор, хочу больше", url="https://t.me/ekaterina_ganusova")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Привет!\n"
        "Я бот, созданный с помощью AI, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разнос как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос."
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    await update.message.reply_text("Оцениваю запрос...")
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ],
            extra_headers={
                "HTTP-Referer": "https://raznesi-bot.onrender.com",
                "X-Title": "raznesi_bot"
            }
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        import traceback
        logging.error("GPT ОШИБКА:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook обработка
@app.route("/", methods=["GET"])
def index():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        loop.call_soon_threadsafe(asyncio.create_task, application.process_update(update))
        logging.warning("==> ПОЛУЧЕН WEBHOOK")
    except Exception as e:
        logging.error("Ошибка webhook:")
        logging.error(e)
    return "ok"

# Настройка webhook
async def setup_webhook():
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await application.initialize()
    await application.start()

# Запуск приложения
if __name__ == "__main__":
    logging.warning("==> ЗАПУСК ПРИЛОЖЕНИЯ")

    def run_bot():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_webhook())

    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
    