import logging
import os
import openai
import asyncio
import threading
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import http.server
import socketserver

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
OWNER_ID = os.getenv("OWNER_ID")

openai.api_key = OPENAI_KEY

# Логирование
logging.basicConfig(level=logging.INFO)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог.")

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты дерзкий, уверенный маркетолог Екатерина. Пиши с юмором, кратко, метко."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуй позже.")

# Заглушка для Render (порт)
def keep_render_happy():
    PORT = int(os.environ.get("PORT", 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Dummy server started on port {PORT}")
        httpd.serve_forever()

threading.Thread(target=keep_render_happy, daemon=True).start()

# Основной запуск
async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
