import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# Логирование
logging.basicConfig(level=logging.WARNING, format="%(asctime)s — %(levelname)s — %(message)s")

# Flask-приложение
app = Flask(__name__)

# Настройки
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Telegram Application
application = Application.builder().token(BOT_TOKEN).updater(None).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logging.warning("==> ВЫЗВАН /start")
        keyboard = [
            [InlineKeyboardButton("Хочу такого же бота", url="https://t.me/ekaterina_ganusova")],
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
    except Exception as e:
        logging.error("ОШИБКА В start():")
        logging.error(e)

# Сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idea = update.message.text
        logging.warning(f"ПОЛУЧЕНО: {idea}")
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
                "HTTP-Referer": "https://raznesi-bot.onrender.com",
                "X-Title": "raznesi_bot"
            }
        )

        answer = response.choices[0].message.content
        logging.warning(f"GPT ОТВЕТ: {answer}")
        await update.message.reply_text(answer)

    except Exception as e:
        import traceback
        logging.error("GPT ОШИБКА:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask-маршруты
@app.route("/")
def index():
    return "OK"

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = request.get_json(force=True)
        logging.warning("==> ПОЛУЧЕН WEBHOOK")
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logging.error("ОШИБКА ВНУТРИ WEBHOOK:")
        logging.error(e)
    return "ok"

# Запуск
async def setup():
    logging.warning("==> НАСТРОЙКА ВЕБХУКА")
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await application.initialize()
    await application.start()

if __name__ == "__main__":
    import asyncio
    import threading

    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup())

    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)