import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_USERNAME = "@mvcl12"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Подать жалобу", callback_data="report")],
        [InlineKeyboardButton("👑 VIP", callback_data="vip")],
        [InlineKeyboardButton("👤 Связаться с админом", callback_data="admin")]
    ]

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "report":
        keyboard = [
            [InlineKeyboardButton("🆓 Бесплатная жалоба", callback_data="free")],
            [InlineKeyboardButton("👑 VIP — 25 ⭐", callback_data="vip_25")],
            [InlineKeyboardButton("💎 VIP Gold — 50 ⭐", callback_data="vip_50")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]

        await query.edit_message_text(
            "📩 Подать жалобу\n\n"
            "🆓 Бесплатная — обработка в течение 1 дня.\n\n"
            "Выберите вариант:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "vip":
        keyboard = [
            [InlineKeyboardButton("👑 VIP — 25 ⭐", callback_data="vip_25")],
            [InlineKeyboardButton("💎 VIP Gold — 50 ⭐", callback_data="vip_50")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]

        await query.edit_message_text(
            "👑 VIP\n\n"
            "👑 VIP — 25 ⭐\n"
            "⏱ Приоритетная обработка — примерно 1 час.\n\n"
            "💎 VIP Gold — 50 ⭐\n"
            "⚡ Приоритетная обработка — примерно 10–20 минут.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin":
        await query.edit_message_text(
            f"👤 Связаться с админом\n\n"
            f"Администратор: {ADMIN_USERNAME}\n\n"
            "Нажмите на username, чтобы открыть профиль."
        )

    elif query.data == "free":
        await query.edit_message_text(
            "🆓 Бесплатная жалоба\n\n"
            "⏱ Обработка — в течение 1 дня.\n\n"
            "Следующим шагом добавим форму заявки."
        )

    elif query.data == "vip_25":
        await query.edit_message_text(
            "👑 VIP — 25 ⭐\n\n"
            "⏱ Приоритетная обработка — примерно 1 час.\n\n"
            "Оплату Stars подключим следующим шагом."
        )

    elif query.data == "vip_50":
        await query.edit_message_text(
            "💎 VIP Gold — 50 ⭐\n\n"
            "⚡ Приоритетная обработка — примерно 10–20 минут.\n\n"
            "Оплату Stars подключим следующим шагом."
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("📩 Подать жалобу", callback_data="report")],
            [InlineKeyboardButton("👑 VIP", callback_data="vip")],
            [InlineKeyboardButton("👤 Связаться с админом", callback_data="admin")]
        ]

        await query.edit_message_text(
            "👋 Главное меню:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не найден")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()