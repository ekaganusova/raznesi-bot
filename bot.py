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

# Настройки логов
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# Flask-приложение
app = Flask(__name__)

# Жёстко заданный webhook
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Переменные окружения
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

# Telegram Application
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# Команда /start
from telegram import ReplyKeyboardMarkup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА /start")
    welcome_text = (
        "Привет!\n"
        "Я бот, созданный с помощью AI, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разбор как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос."
    )
    await update.message.reply_text(welcome_text)

# Обработка сообщений
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    username = update.message.from_user.username
    logging.warning(f"ПОЛУЧЕНО СООБЩЕНИЕ: {idea}")

    # Уведомление о том, что бот обрабатывает
    await update.message.reply_text("Оцениваю запрос…")

    try:
        logging.warning("GPT: отправляю запрос...")
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENAI_KEY
        )

        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ]
        )
        answer = response.choices[0].message.content
        logging.warning("GPT: ответ получен")

        # Сохранение в Google Sheets
        save_to_sheet(username, idea)

        # Кнопка «Хочу такого же бота»
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova?start=want_bot")]
        ])

        await update.message.reply_text(answer, reply_markup=button)

    except Exception as e:
        import traceback
        logging.error("ОШИБКА GPT:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Подключение обработчиков
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook настройка
async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.route("/", methods=["GET"])
def index():
    return "OK"

# Обработка webhook-запроса
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logging.warning("==> ПОЛУЧЕН WEBHOOK")
        logging.warning(data)
        update = Update.de_json(data, bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        logging.error("Ошибка webhook:")
        logging.error(e)
    return "ok"

# Асинхронный запуск
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup())
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())

# Запуск
if __name__ == "__main__":
    logging.warning("==> ЗАПУСК ПРИЛОЖЕНИЯ")
    threading.Thread(target=run_async).start()
    app.run(host="0.0.0.0", port=10000)
