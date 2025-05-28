import os
import logging
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Настройки
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
WEBHOOK_URL = "https://raznesi-bot.onrender.com"

# Flask
app = Flask(__name__)

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")

# Telegram
application = Application.builder().token(BOT_TOKEN).build()

# Устанавливаем ключ OpenAI
openai.api_key = OPENAI_KEY

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔥ЖМУ НА КНОПКУ🔥", url="https://t.me/ekaterina_ganusova")]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет!\n"
        "Я бот, созданный с помощью AI✨, чтобы проверять бизнес-идеи на прочность. "
        "Напиши свою — и я устрою ей разнос как маркетолог: жёстко, с юмором и по делу.\n\n"
        "Как использовать:\n"
        "1. Просто напиши свою идею.\n"
        "2. Получи разнос.\n"
        "3. Если есть вопросы или хочешь такого же бота — жми на кнопку👇🏻",
        reply_markup=markup
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text
    logging.info(f"ПОЛУЧЕНО: {idea}")
    try:
        await update.message.reply_text("Оцениваю запрос...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты — требовательный маркетолог. Отвечай строго, по делу и с юмором."},
                {"role": "user", "content": f"Идея: {idea}"}
            ]
        )
        answer = response['choices'][0]['message']['content']
        await update.message.reply_text(answer + "\n\nОстались вопросы или еще поболтаем? 🤗")
    except Exception:
        logging.error("GPT ОШИБКА:")
        logging.error(traceback.format_exc())
        await update.message.reply_text("GPT сломался. Попробуй позже.")

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook обработчик
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)

        asyncio.run(application.process_update(update))

    except Exception:
        logging.error("Ошибка webhook:")
        logging.error(traceback.format_exc())
    return "ok"

# Проверка главной страницы
@app.route("/")
def index():
    return "OK"

# Установка webhook
async def setup():
    await application.initialize()
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await application.start()
    logging.info("Бот запущен и webhook установлен")

# Запуск сервиса
if __name__ == "__main__":
    def run_bot():
        asyncio.run(setup())

    import threading
    threading.Thread(target=run_bot).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
        