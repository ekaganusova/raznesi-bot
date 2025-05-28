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
    keyboard = [
        [InlineKeyboardButton("🔥ЖМУ НА КНОПКУ🔥", url="https://t.me/ekaterina_ganusova")],
    ]
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
        await update.message.reply_text(answer + "\n\nОстались вопросы или еще поболтаем? 🤗")
    except Exception:
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Telegram routing
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

from flask import Flask, request
from telegram import Update
import asyncio
import logging
import traceback

# Переменные и инициализация
app = Flask(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Flask webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)

        # Без get_event_loop — просто передаём в созданный loop
        asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
    except Exception:
        logging.error(traceback.format_exc())
    return "ok"
    
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

    app.run(host="0.0.0.0", port=10000)