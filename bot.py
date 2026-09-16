import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Это новый FSociety Bot.\n\n"
        "Бот успешно работает!"
    )


telegram_app.add_handler(CommandHandler("start", start))


@app.get("/")
def home():
    return "FSociety Bot is running!"


@app.post("/webhook")
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return "OK"


if __name__ == "__main__":
    import asyncio

    async def main():
        await telegram_app.initialize()
        await telegram_app.start()

        port = int(os.getenv("PORT", 8080))
        app.run(host="0.0.0.0", port=port)

    asyncio.run(main())