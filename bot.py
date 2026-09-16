import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_CHAT_ID = 8945804459
ADMIN_USERNAME = "@mvcl12"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("📩 Подать жалобу", callback_data="report")],
        [InlineKeyboardButton("👑 VIP", callback_data="vip")],
        [InlineKeyboardButton("👤 Связаться с админом", callback_data="admin")],
    ]

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\nВыберите нужный раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "report":
        keyboard = [
            [InlineKeyboardButton("🆓 Бесплатная жалоба", callback_data="free")],
            [InlineKeyboardButton("👑 VIP — 25 ⭐", callback_data="vip_25")],
            [InlineKeyboardButton("💎 VIP Gold — 50 ⭐", callback_data="vip_50")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")],
        ]

        await query.edit_message_text(
            "📩 Подать жалобу\n\n"
            "🆓 Бесплатная — обработка в течение 1 дня.\n"
            "👑 VIP — 25 ⭐ — примерно за 1 час.\n"
            "💎 VIP Gold — 50 ⭐ — примерно за 10–20 минут.\n\n"
            "Выберите вариант:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if query.data == "vip":
        keyboard = [
            [InlineKeyboardButton("👑 VIP — 25 ⭐", callback_data="vip_25")],
            [InlineKeyboardButton("💎 VIP Gold — 50 ⭐", callback_data="vip_50")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")],
        ]

        await query.edit_message_text(
            "👑 VIP\n\n"
            "👑 VIP — 25 ⭐ — примерно за 1 час.\n\n"
            "💎 VIP Gold — 50 ⭐ — примерно за 10–20 минут.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if query.data == "admin":
        keyboard = [
            [
                InlineKeyboardButton(
                    "👤 Открыть профиль админа",
                    url="https://t.me/mvcl12",
                )
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")],
        ]

        await query.edit_message_text(
            f"👤 Администратор: {ADMIN_USERNAME}\n\n"
            "Вы можете самостоятельно перейти в профиль администратора.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if query.data == "back":
        keyboard = [
            [InlineKeyboardButton("📩 Подать жалобу", callback_data="report")],
            [InlineKeyboardButton("👑 VIP", callback_data="vip")],
            [InlineKeyboardButton("👤 Связаться с админом", callback_data="admin")],
        ]

        await query.edit_message_text(
            "👋 Главное меню:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if query.data in ("free", "vip_25", "vip_50"):
        if query.data == "free":
            report_type = "🆓 Бесплатная"
            processing_time = "в течение 1 дня"
            price = 0

        elif query.data == "vip_25":
            report_type = "👑 VIP"
            processing_time = "примерно за 1 час"
            price = 25

        else:
            report_type = "💎 VIP Gold"
            processing_time = "примерно за 10–20 минут"
            price = 50

        context.user_data.clear()
        context.user_data["step"] = "target"
        context.user_data["report_type"] = report_type
        context.user_data["processing_time"] = processing_time
        context.user_data["price"] = price

        await query.message.reply_text(
            f"{report_type}\n\n"
            "Шаг 1 из 3.\n"
            "Отправьте username или ссылку на аккаунт, "
            "на который подаётся жалоба."
        )
        return


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    step = context.user_data.get("step")

    if step == "target":
        if not message.text:
            await message.reply_text("Пожалуйста, отправьте username или ссылку текстом.")
            return

        context.user_data["target"] = message.text.strip()
        context.user_data["step"] = "reason"

        await message.reply_text(
            "Шаг 2 из 3.\n"
            "Напишите причину жалобы."
        )
        return

    if step == "reason":
        if not message.text:
            await message.reply_text("Пожалуйста, напишите причину текстом.")
            return

        context.user_data["reason"] = message.text.strip()
        context.user_data["step"] = "evidence"

        await message.reply_text(
            "Шаг 3 из 3.\n"
            "Отправьте доказательства.\n\n"
            "Можно отправить текст, фотографию или документ."
        )
        return

    if step == "evidence":
        if message.photo:
            context.user_data["evidence"] = message.photo[-1].file_id
            context.user_data["evidence_type"] = "photo"

        elif message.document:
            context.user_data["evidence"] = message.document.file_id
            context.user_data["evidence_type"] = "document"

        elif message.text:
            context.user_data["evidence"] = message.text
            context.user_data["evidence_type"] = "text"

        else:
            await message.reply_text(
                "Пожалуйста, отправьте текст, фотографию или документ."
            )
            return

        price = context.user_data.get("price", 0)

        if price == 0:
            await send_report_to_admin(update, context)

            await message.reply_text(
                "✅ Ваша заявка принята.\n\n"
                "Мы оповестим вас об обработке в течение 1 дня."
            )

            context.user_data.clear()
            return

        if price == 25:
            title = "VIP — жалоба"
            payload = "vip_25"
        else:
            title = "VIP Gold — жалоба"
            payload = "vip_50"

        await message.reply_text(
            f"📋 Данные заявки получены.\n\n"
            f"Теперь оплатите {price} ⭐ для отправки заявки."
        )

        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description="Приоритетная обработка жалобы",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(title, price)],
        )

        context.user_data["step"] = "payment"
        return


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query

    if query.invoice_payload == "vip_25":
        expected_price = 25
    elif query.invoice_payload == "vip_50":
        expected_price = 50
    else:
        await query.answer(
            ok=False,
            error_message="Неизвестный заказ.",
        )
        return

    if query.total_amount != expected_price:
        await query.answer(
            ok=False,
            error_message="Неверная сумма.",
        )
        return

    await query.answer(ok=True)


async def successful_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    payment = update.message.successful_payment

    if payment.invoice_payload == "vip_25":
        expected_price = 25
        processing_time = "примерно за 1 час"
    else:
        expected_price = 50
        processing_time = "примерно за 10–20 минут"

    if payment.total_amount != expected_price:
        await update.message.reply_text(
            "⚠️ Не удалось подтвердить оплату."
        )
        return

    await send_report_to_admin(update, context)

    await update.message.reply_text(
        "✅ Ваша VIP-заявка принята.\n\n"
        f"Оплата {expected_price} ⭐ подтверждена.\n"
        f"Мы оповестим вас об обработке {processing_time}."
    )

    context.user_data.clear()


async def send_report_to_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    username = (
        f"@{user.username}"
        if user.username
        else "нет username"
    )

    report_type = context.user_data.get(
        "report_type",
        "Неизвестно",
    )

    target = context.user_data.get(
        "target",
        "Не указан",
    )

    reason = context.user_data.get(
        "reason",
        "Не указана",
    )

    evidence = context.user_data.get(
        "evidence",
        "Нет",
    )

    evidence_type = context.user_data.get(
        "evidence_type",
        "text",
    )

    text = (
        "📥 НОВАЯ ЗАЯВКА\n\n"
        f"Тип: {report_type}\n"
        f"Пользователь: {username}\n"
        f"Chat ID пользователя: {user.id}\n\n"
        f"🎯 Цель: {target}\n\n"
        f"📝 Причина:\n{reason}\n\n"
        "📎 Доказательства:"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
    )

    if evidence_type == "photo":
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=evidence,
        )

    elif evidence_type == "document":
        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=evidence,
        )

    else:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=evidence,
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не найден")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(report|vip|admin|back|free|vip_25|vip_50)$",
        )
    )

    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.ALL,
            message_handler,
        )
    )

    app.add_handler(
        PreCheckoutQueryHandler(precheckout)
    )

    print("Бот запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()