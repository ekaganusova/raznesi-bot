import os
import logging
import threading
import asyncio
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# Логирование
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# Flask-приложение
app = Flask(__name__)

# Webhook URL
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Переменные окружения
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

# Telegram Application
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА /start")
    keyboard = [
        [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova?start=bot")],
        [InlineKeyboardButton("Отличный разбор, хочу больше", url="https://t.me/ekaterina_ganusova")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет!\nЯ бот, созданный с помощью AI, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разнос как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос.",
        reply_markup=reply_markup
    )

# Обработка текста
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    logging.warning(f"ПОЛУЧЕНО СООБЩЕНИЕ: {idea}")

    try:
        await update.message.reply_text("Оцениваю запрос...")

        client = OpenAI(
            api_key=OPENAI_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ],
            extra_headers={
                "HTTP-Referer": "https://raznesi-bot.onrender.com",
                "X-Title": "RaznesiBot"
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

# Webhook setup
async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

# Главная страница
@app.route("/", methods=["GET"])
def index():
    return "OK"

# Обработка Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logging.warning("==> ПОЛУЧЕН WEBHOOK")
        logging.warning(data)
        update = Update.de_json(data, bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        logging.error("Ошибка в webhook:")
        logging.error(e)
    return "ok"

# Асинхронный запуск
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

# Запуск приложения
if __name__ == "__main__":
    logging.warning("==> ЗАПУСК ПРИЛОЖЕНИЯ")
    threading.Thread(target=run_async).start()
    app.run(host="0.0.0.0", port=10000)
