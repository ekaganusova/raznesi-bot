import os
import logging
import threading
import asyncio
import gspread
from flask import Flask, request
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
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

# Переменные окружения
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
GSHEET_KEY = os.environ.get("GSHEET_KEY")
SHEET_NAME = os.environ.get("SHEET_NAME")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# Приветствие
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА /start")

    if not update.message:
        logging.warning("Нет update.message в /start")
        return

    text = (
        "Привет!\n"
        "Я бот, созданный с помощью AI, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разбор как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Хочу такого же бота",
                url="https://t.me/ekaterina_ganusova?startapp=Привет! Хочу такого же бота"
            )
        ]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)
# Сохраняем в Google Sheets
def save_to_sheets(username: str, text: str):
    try:
        gc = gspread.service_account(filename=GSHEET_KEY)
        sh = gc.open(SHEET_NAME)
        worksheet = sh.sheet1
        worksheet.append_row([username, text])
        logging.warning("Сохранено в Google Sheets")
    except Exception as e:
        logging.error(f"Ошибка сохранения в Google Sheets: {e}")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    username = update.message.from_user.username
    logging.warning(f"ПОЛУЧЕНО СООБЩЕНИЕ: {idea}")

    # Сообщение "Оцениваю..."
    await update.message.reply_text("Оцениваю запрос...")

    # Сохранение
    save_to_sheets(username or "no_username", idea)

    try:
        client = OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ]
        )
        answer = response.choices[0].message.content

        # Кнопки после ответа
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova?start=bot")]
        ])
        await update.message.reply_text(answer, reply_markup=buttons)

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
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.route("/", methods=["GET"])
def index():
    return "OK"

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logging.warning("==> ПОЛУЧЕН WEBHOOK")
        logging.warning(data)
        update = Update.de_json(data, application.bot)
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
