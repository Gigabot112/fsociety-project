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
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_CHAT_ID = 8945804459
ADMIN_USERNAME = "@mvcl12"

TARGET, REASON, EVIDENCE, WAIT_PAYMENT = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Подать жалобу", callback_data="report")],
        [InlineKeyboardButton("👑 VIP", callback_data="vip")],
        [InlineKeyboardButton("👤 Связаться с админом", callback_data="admin")],
    ]

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def menu_buttons(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.data == "report":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🆓 Бесплатная жалоба",
                    callback_data="free",
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 VIP — 25 ⭐",
                    callback_data="vip_25",
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 VIP Gold — 50 ⭐",
                    callback_data="vip_50",
                )
            ],
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

    elif query.data == "vip":
        keyboard = [
            [
                InlineKeyboardButton(
                    "👑 VIP — 25 ⭐",
                    callback_data="vip_25",
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 VIP Gold — 50 ⭐",
                    callback_data="vip_50",
                )
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")],
        ]

        await query.edit_message_text(
            "👑 VIP\n\n"
            "👑 VIP — 25 ⭐\n"
            "⏱ Обработка примерно за 1 час.\n\n"
            "💎 VIP Gold — 50 ⭐\n"
            "⚡ Обработка примерно за 10–20 минут.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "admin":
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

    elif query.data == "back":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📩 Подать жалобу",
                    callback_data="report",
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 VIP",
                    callback_data="vip",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 Связаться с админом",
                    callback_data="admin",
                )
            ],
        ]

        await query.edit_message_text(
            "👋 Главное меню:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def start_report(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

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
    context.user_data["report_type"] = report_type
    context.user_data["processing_time"] = processing_time
    context.user_data["price"] = price

    await query.message.reply_text(
        f"{report_type}\n\n"
        "Шаг 1 из 3.\n"
        "Отправьте username или ссылку на аккаунт, "
        "на который подаётся жалоба."
    )

    return TARGET


async def receive_target(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["target"] = update.message.text.strip()

    await update.message.reply_text(
        "Шаг 2 из 3.\n"
        "Напишите причину жалобы."
    )

    return REASON


async def receive_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["reason"] = update.message.text.strip()

    await update.message.reply_text(
        "Шаг 3 из 3.\n"
        "Отправьте доказательства.\n\n"
        "Можно отправить текст, фотографию или документ."
    )

    return EVIDENCE


async def receive_evidence(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    message = update.message

    if message.text:
        context.user_data["evidence"] = message.text
        context.user_data["evidence_type"] = "text"

    elif message.photo:
        context.user_data["evidence"] = message.photo[-1].file_id
        context.user_data["evidence_type"] = "photo"

    elif message.document:
        context.user_data["evidence"] = message.document.file_id
        context.user_data["evidence_type"] = "document"

    else:
        await message.reply_text(
            "Пожалуйста, отправьте доказательства "
            "текстом, фотографией или документом."
        )
        return EVIDENCE

    price = context.user_data["price"]

    if price == 0:
        await send_report_to_admin(update, context)

        await message.reply_text(
            "✅ Ваша заявка принята.\n\n"
            "Мы оповестим вас об обработке "
            "в течение 1 дня."
        )

        context.user_data.clear()
        return ConversationHandler.END

    if price == 25:
        title = "VIP — жалоба"
        description = "Приоритетная обработка жалобы"
        payload = "vip_25"
    else:
        title = "VIP Gold — жалоба"
        description = "Приоритетная обработка жалобы"
        payload = "vip_50"

    await message.reply_text(
        "📋 Данные заявки получены.\n\n"
        f"Теперь оплатите {price} ⭐ для отправки заявки на обработку."
    )

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(title, price)],
    )

    return WAIT_PAYMENT


async def precheckout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.pre_checkout_query

    if query.invoice_payload not in ("vip_25", "vip_50"):
        await query.answer(
            ok=False,
            error_message="Неизвестный заказ.",
        )
        return

    expected_price = 25 if query.invoice_payload == "vip_25" else 50

    if query.total_amount != expected_price:
        await query.answer(
            ok=False,
            error_message="Неверная сумма оплаты.",
        )
        return

    await query.answer(ok=True)


async def successful_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
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
        return ConversationHandler.END

    await send_report_to_admin(update, context)

    await update.message.reply_text(
        "✅ Ваша VIP-заявка принята.\n\n"
        f"Оплата {expected_price} ⭐ подтверждена.\n"
        f"Мы оповестим вас об обработке "
        f"{processing_time}."
    )

    context.user_data.clear()

    return ConversationHandler.END


async def send_report_to_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    username = (
        f"@{user.username}"
        if user.username
        else "нет username"
    )

    report_type = context.user_data.get(
        "report_type", "Неизвестно"
    )
    target = context.user_data.get(
        "target", "Не указан"
    )
    reason = context.user_data.get(
        "reason", "Не указана"
    )
    evidence = context.user_data.get(
        "evidence", "Нет"
    )
    evidence_type = context.user_data.get(
        "evidence_type", "text"
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


async def cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Заявка отменена."
    )

    return ConversationHandler.END


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не найден")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    report_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_report,
                pattern="^(free|vip_25|vip_50)$",
            )
        ],
        states={
            TARGET: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_target,
                )
            ],
            REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_reason,
                )
            ],
            EVIDENCE: [
                MessageHandler(
                    filters.TEXT
                    | filters.PHOTO
                    | filters.Document.ALL,
                    receive_evidence,
                )
            ],
            WAIT_PAYMENT: [
                MessageHandler(
                    filters.SUCCESSFUL_PAYMENT,
                    successful_payment,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
        allow_reentry=True,
    )

    app.add_handler(report_conversation)

    app.add_handler(
        CallbackQueryHandler(
            menu_buttons,
            pattern="^(report|vip|admin|back)$",
        )
    )

    app.add_handler(
        PreCheckoutQueryHandler(precheckout)
    )

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()