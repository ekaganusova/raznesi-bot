import logging
import os
import openai
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Установи в Render переменные окружения
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: "https://your-service.onrender.com/webhook"

# Инициализация Flask
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s", level=logging.INFO
)

# Инициализация Telegram-бота
application = Application.builder().token(TELEGRAM_TOKEN).build()


@app.route("/")
def index():
    return "OK", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.create_task(application.process_update(update))
    except Exception as e:
        logging.error("Ошибка webhook:\n%s", e)
    return "OK", 200


# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши что-нибудь, и я тебе отвечу.")


# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        logging.info("ПОЛУЧЕНО: %s", user_message)

        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": user_message}],
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )

        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]

        await update.message.reply_text(answer)

    except Exception as e:
        logging.error("GPT ОШИБКА:\n%s", e)
        await update.message.reply_text("Ошибка обработки запроса 😢")


# Регистрация хендлеров
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# Установка webhook при запуске
def setup_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    response = requests.post(url, data={"url": f"{WEBHOOK_URL}/webhook"})
    if response.status_code == 200:
        logging.info("Webhook установлен: %s/webhook", WEBHOOK_URL)
    else:
        logging.error("Не удалось установить webhook: %s", response.text)


if __name__ == "__main__":
    setup_webhook()
    logging.info("Бот запущен и webhook установлен")
    app.run(host="0.0.0.0", port=10000)
        