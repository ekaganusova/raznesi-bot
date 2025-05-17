import os
import openai
from openai import OpenAI
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Настройка логирования (для Render)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

# Ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning("==> ОБРАБОТКА КОМАНДЫ /start")
    await update.message.reply_text(
        "Привет! Я бот Екатерины. Напиши свою идею, и я устрою ей разнос как маркетолог."
    )

# GPT-разнос
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

        client = openai.OpenAI(api_key=OPENAI_KEY)

        response = client.chat.completions.create(
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

# Запуск бота
if __name__ == "__main__":
    logging.warning("==> ЗАПУСК ПРИЛОЖЕНИЯ")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
