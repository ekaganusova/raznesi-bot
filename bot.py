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

# Flask
app = Flask(__name__)

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")

# Telegram bot
application = Application.builder().token(BOT_TOKEN).build()

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔥ЖМУ НА КНОПКУ🔥", url="https://t.me/ekaterina_ganusova")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет!\nЯ бот-маркетолог. Напиши идею, и я устрою разнос.\n\nЖми кнопку👇🏻",
        reply_markup=markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    logging.info(f"ПОЛУЧЕНО: {idea}")
    try:
        await update.message.reply_text("Оцениваю запрос...")
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ],
            extra_headers={
                "HTTP-Referer": WEBHOOK_URL,
                "X-Title": "raznesi_bot"
            }
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer + "\n\nОстались вопросы или ты уже всё понял? 🤭")
    except Exception:
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Telegram routing
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))
    except Exception:
        logging.error(traceback.format_exc())
    return "ok"

@app.route("/")
def index():
    return "OK"

# Установка Webhook
async def setup():
    await application.initialize()
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await application.start()
    logging.info("Бот запущен и webhook установлен")

# Запуск Flask и Telegram
if __name__ == "__main__":
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup())
    import threading
    threading.Thread(target=run).start()

    # ВАЖНО: Render требует app.run
    app.run(host="0.0.0.0", port=10000)