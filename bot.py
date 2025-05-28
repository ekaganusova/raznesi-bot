import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")

# Flask
app = Flask(__name__)

# Telegram
application = Application.builder().token(BOT_TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [[InlineKeyboardButton("🔥ЖМУ НА КНОПКУ🔥", url="https://t.me/ekaterina_ganusova")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "Привет!\n"
            "Я бот, созданный с помощью AI✨, чтобы проверять бизнес-идеи на прочность. "
            "Напиши свою — и я устрою ей разнос как маркетолог: жёстко, с юмором и по делу.\n\n"
            "Как использовать:\n"
            "1. Просто напиши свою идею.\n"
            "2. Получи разнос.\n"
            "3. Есть вопросы? Жми кнопку👇🏻"
        )
        await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logging.error("Ошибка в команде /start:")
        logging.exception(e)

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    logging.info(f"ПОЛУЧЕНО: {idea}")
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Оцениваю запрос...")

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
        answer = response.choices[0].message.content + "\n\nОстались вопросы или ты уже всё понял? 🤭"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

    except Exception as e:
        logging.error("GPT ОШИБКА:")
        logging.exception(e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="GPT сломался. Попробуй позже.")

# Flask Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        logging.error("Ошибка webhook:")
        logging.exception(e)
    return "ok"

# Главная страница
@app.route("/", methods=["GET"])
def index():
    return "OK"

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запуск
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=f"{WEBHOOK_URL}/webhook",
        allowed_updates=Update.ALL_TYPES,
    )