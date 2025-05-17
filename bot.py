import os
import openai
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from flask import Flask
import asyncio

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

openai.api_key = OPENAI_KEY

# Логирование
logging.basicConfig(level=logging.INFO)

# Flask для Render
app = Flask(__name__)

@app.route("/")
def index():
    return "Разнеси работает!"

# Telegram-приложение
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА КОМАНДЫ /start")
    await update.message.reply_text(
        "Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог."
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logging.warning(f"ПОЛУЧЕНО: {user_input}")

    prompt = f"""
Ты — опытный маркетолог. Пользователь написал идею или описание бизнеса. Сделай разбор в формате:

1. УТП — [твой ответ]
2. Проблема — [твой ответ]
3. Ошибка упаковки — [твой ответ]
4. Предложение улучшения — [твой ответ]

Заверши фразой: "Уровень боли: [оценка от 1 до 10]. Хочешь персональный разнос — пиши @ekaterina_ganusova".

Текст пользователя: {user_input}
"""

    try:
        logging.warning("GPT: отправляю запрос...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты дерзкий, уверенный маркетолог Екатерина. Пиши с юмором, кратко, метко."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        logging.warning("GPT: ответ получен")
        await update.message.reply_text(answer)

    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй позже.")

# Регистрация хендлеров
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запуск Flask и Telegram
if __name__ == "__main__":
    async def main():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        logging.warning("==> Telegram бот запущен через polling")
        await application.updater.idle()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Flask на фоне
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()

    loop.run_until_complete(main())
