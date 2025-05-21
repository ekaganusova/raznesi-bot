import os
import logging
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# Логи
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# Flask
app = Flask(__name__)

# Переменные окружения
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Telegram bot
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА /start")
    keyboard = [
        [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova?start=hi")],
        [InlineKeyboardButton("Отличный разбор, хочу больше", url="https://t.me/ekaterina_ganusova")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Привет!\n"
        "Я бот, созданный с помощью AI, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разбор как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос."
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

# Сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    logging.warning(f"ПОЛУЧЕНО: {idea}")
    await update.message.reply_text("Оцениваю запрос...")

    try:
        client = OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ]
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

@app.route("/", methods=["GET"])
def index():
    return "OK"

@app.route(f"/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    application.update_queue.put_nowait(update)
    logging.warning("==> ПОЛУЧЕН WEBHOOK")
    return "ok"

if __name__ == "__main__":
    logging.warning("==> ЗАПУСК ПРИЛОЖЕНИЯ")
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=f"{WEBHOOK_URL}/webhook",
    )