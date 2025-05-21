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

# Настройки логов
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

app = Flask(__name__)

WEBHOOK_URL = "https://raznesi-bot.onrender.com"
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

bot = Bot(token=BOT_TOKEN)

async def post_init(application: Application):
    await application.bot.initialize()
    logging.warning("==> BOT ИНИЦИАЛИЗИРОВАН")

application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

# Приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА /start")
    keyboard = [
        [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova?start=bot_request")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        "Привет!\n"
        "Я бот, созданный с помощью AI, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разбор как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос."
    )

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    user = update.effective_user
    username = user.username or f"id_{user.id}"
    logging.warning(f"ПОЛУЧЕНО СООБЩЕНИЕ: {idea} от {username}")

    try:
        await update.message.reply_text("Оцениваю запрос...")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENAI_KEY
        )

        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ],
            extra_headers={
                "HTTP-Referer": "https://t.me/raznesi_ai_bot",
                "X-Title": "Разнеси Бот"
            }
        )

        answer = response.choices[0].message.content
        keyboard = [
            [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova?start=bot_request")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(answer, reply_markup=reply_markup)

        # Сохраняем в таблицу, если хочешь включить:
        # save_to_sheet(username, idea)

    except Exception as e:
        import traceback
        logging.error("ОШИБКА GPT:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook
async def setup():
    await bot.delete_webhook()
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.route("/", methods=["GET"])
def index():
    return "OK"

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
