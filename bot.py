import os
import uuid

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

# Аккаунт, который получает заявки
ADMIN_CHAT_ID = 8945804459

# Username администратора
ADMIN_USERNAME = "@mvcl12"


# Временное хранилище заявок
pending_reports = {}


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

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

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# КНОПКИ
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    data = query.data

    # -------------------------
    # Подать жалобу
    # -------------------------

    if data == "report":

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
            [
                InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data="back",
                )
            ],
        ]

        await query.edit_message_text(
            "📩 Подать жалобу\n\n"

            "🆓 Бесплатная\n"
            "Обработка в течение 1 дня.\n\n"

            "👑 VIP — 25 ⭐\n"
            "Приоритетная обработка примерно за 1 час.\n\n"

            "💎 VIP Gold — 50 ⭐\n"
            "Приоритетная обработка примерно за 10–20 минут.\n\n"

            "Выберите вариант:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # -------------------------
    # VIP
    # -------------------------

    if data == "vip":

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
            [
                InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data="back",
                )
            ],
        ]

        await query.edit_message_text(
            "👑 VIP\n\n"

            "👑 VIP — 25 ⭐\n"
            "Обработка примерно за 1 час.\n\n"

            "💎 VIP Gold — 50 ⭐\n"
            "Обработка примерно за 10–20 минут.",
            
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # -------------------------
    # Администратор
    # -------------------------

    if data == "admin":

        keyboard = [
            [
                InlineKeyboardButton(
                    "👤 Открыть профиль админа",
                    url="https://t.me/mvcl12",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data="back",
                )
            ],
        ]

        await query.edit_message_text(
            f"👤 Администратор: {ADMIN_USERNAME}\n\n"
            "Вы можете самостоятельно открыть профиль "
            "администратора.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # -------------------------
    # Назад
    # -------------------------

    if data == "back":

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

        return

    # -------------------------
    # Выбор типа заявки
    # -------------------------

    if data in ("free", "vip_25", "vip_50"):

        if data == "free":
            report_type = "🆓 Бесплатная"
            processing_time = "в течение 1 дня"
            price = 0

        elif data == "vip_25":
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

    # =========================
    # АДМИН: ПРИНЯТЬ ЗАЯВКУ
    # =========================

    if data.startswith("accept:"):

        # Проверяем, что кнопку нажимает именно админ
        if query.from_user.id != ADMIN_CHAT_ID:
            await query.answer(
                "⛔ У вас нет доступа.",
                show_alert=True,
            )
            return

        report_id = data.split(":", 1)[1]

        report = pending_reports.get(report_id)

        if not report:
            await query.answer(
                "Заявка уже обработана или не найдена.",
                show_alert=True,
            )
            return

        report["status"] = "accepted"

        # Меняем сообщение у администратора
        await query.edit_message_text(
            "✅ ЗАЯВКА ПРИНЯТА\n\n"

            f"ID заявки: {report_id}\n"
            f"Тип: {report['report_type']}\n"
            f"Цель: {report['target']}\n\n"

            "Заявка принята к рассмотрению.\n"
            "Данные и доказательства доступны выше."
        )

        # Сообщаем пользователю
        try:
            await context.bot.send_message(
                chat_id=report["user_id"],
                text=(
                    "✅ Ваша заявка принята к рассмотрению.\n\n"
                    f"Тип: {report['report_type']}\n"
                    f"Срок обработки: {report['processing_time']}\n\n"
                    "Модератор получил вашу заявку и "
                    "предоставленные доказательства."
                ),
            )

        except Exception:
            pass

        return

    # =========================
    # АДМИН: ОТКЛОНИТЬ ЗАЯВКУ
    # =========================

    if data.startswith("reject:"):

        # Проверяем администратора
        if query.from_user.id != ADMIN_CHAT_ID:
            await query.answer(
                "⛔ У вас нет доступа.",
                show_alert=True,
            )
            return

        report_id = data.split(":", 1)[1]

        report = pending_reports.get(report_id)

        if not report:
            await query.answer(
                "Заявка уже обработана или не найдена.",
                show_alert=True,
            )
            return

        report["status"] = "rejected"

        await query.edit_message_text(
            "❌ ЗАЯВКА ОТКЛОНЕНА\n\n"

            f"ID заявки: {report_id}\n"
            f"Тип: {report['report_type']}\n"
            f"Цель: {report['target']}"
        )

        # Сообщаем пользователю
        try:
            await context.bot.send_message(
                chat_id=report["user_id"],
                text=(
                    "❌ Ваша заявка была отклонена "
                    "модератором.\n\n"
                    "Если вы считаете, что это произошло "
                    "по ошибке, вы можете обратиться к администратору."
                ),
            )

        except Exception:
            pass

        return


# =========================
# ПОЛУЧЕНИЕ ДАННЫХ ЗАЯВКИ
# =========================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.message

    step = context.user_data.get("step")

    # -------------------------
    # Шаг 1 — цель
    # -------------------------

    if step == "target":

        if not message.text:
            await message.reply_text(
                "Пожалуйста, отправьте username или ссылку текстом."
            )
            return

        context.user_data["target"] = message.text.strip()

        context.user_data["step"] = "reason"

        await message.reply_text(
            "Шаг 2 из 3.\n"
            "Напишите причину жалобы."
        )

        return

    # -------------------------
    # Шаг 2 — причина
    # -------------------------

    if step == "reason":

        if not message.text:
            await message.reply_text(
                "Пожалуйста, напишите причину текстом."
            )
            return

        context.user_data["reason"] = message.text.strip()

        context.user_data["step"] = "evidence"

        await message.reply_text(
            "Шаг 3 из 3.\n"
            "Отправьте доказательства.\n\n"
            "Можно отправить текст, фотографию или документ."
        )

        return

    # -------------------------
    # Шаг 3 — доказательства
    # -------------------------

    if step == "evidence":

        if message.photo:

            context.user_data["evidence"] = (
                message.photo[-1].file_id
            )

            context.user_data["evidence_type"] = "photo"

        elif message.document:

            context.user_data["evidence"] = (
                message.document.file_id
            )

            context.user_data["evidence_type"] = "document"

        elif message.text:

            context.user_data["evidence"] = (
                message.text
            )

            context.user_data["evidence_type"] = "text"

        else:

            await message.reply_text(
                "Пожалуйста, отправьте текст, фотографию или документ."
            )

            return

        price = context.user_data.get("price", 0)

        # Бесплатная заявка
        if price == 0:

            await create_report(
                update,
                context,
            )

            await message.reply_text(
                "✅ Ваша заявка принята.\n\n"
                "Мы оповестим вас об обработке "
                "в течение 1 дня."
            )

            context.user_data.clear()

            return

        # Платная заявка
        if price == 25:

            title = "VIP — жалоба"
            payload = "vip_25"

        else:

            title = "VIP Gold — жалоба"
            payload = "vip_50"

        await message.reply_text(
            f"📋 Данные заявки получены.\n\n"
            f"Теперь оплатите {price} ⭐ "
            "для отправки заявки."
        )

        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description="Приоритетная обработка жалобы",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[
                LabeledPrice(
                    title,
                    price,
                )
            ],
        )

        context.user_data["step"] = "payment"

        return


# =========================
# СОЗДАНИЕ ЗАЯВКИ
# =========================

async def create_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    report_id = uuid.uuid4().hex[:8].upper()

    username = (
        f"@{user.username}"
        if user.username
        else "нет username"
    )

    report = {
        "id": report_id,
        "user_id": user.id,
        "username": username,

        "report_type": context.user_data.get(
            "report_type",
            "Неизвестно",
        ),

        "processing_time": context.user_data.get(
            "processing_time",
            "Не указан",
        ),

        "target": context.user_data.get(
            "target",
            "Не указана",
        ),

        "reason": context.user_data.get(
            "reason",
            "Не указана",
        ),

        "evidence": context.user_data.get(
            "evidence",
            "Нет",
        ),

        "evidence_type": context.user_data.get(
            "evidence_type",
            "text",
        ),

        "status": "pending",
    }

    pending_reports[report_id] = report

    # Кнопки администратора
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Принять заявку",
                callback_data=f"accept:{report_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отклонить заявку",
                callback_data=f"reject:{report_id}",
            )
        ],
    ]

    admin_text = (
        "📥 НОВАЯ ЗАЯВКА\n\n"

        f"🆔 ID заявки: {report_id}\n\n"

        f"Тип: {report['report_type']}\n"

        f"Пользователь: {report['username']}\n"

        f"Chat ID пользователя: {report['user_id']}\n\n"

        f"🎯 Цель:\n"
        f"{report['target']}\n\n"

        f"📝 Причина:\n"
        f"{report['reason']}\n\n"

        "📎 Доказательства:\n"
        "См. вложение ниже.\n\n"

        "⏳ Статус: ожидает решения модератора."
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # Отправляем доказательства
    if report["evidence_type"] == "photo":

        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=report["evidence"],
            caption=f"📎 Доказательство заявки {report_id}",
        )

    elif report["evidence_type"] == "document":

        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=report["evidence"],
            caption=f"📎 Доказательство заявки {report_id}",
        )

    else:

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📎 Доказательство заявки {report_id}:\n\n"
                f"{report['evidence']}"
            ),
        )


# =========================
# PRE-CHECKOUT
# =========================

async def precheckout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

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


# =========================
# УСПЕШНАЯ ОПЛАТА
# =========================

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

    await create_report(
        update,
        context,
    )

    await update.message.reply_text(
        "✅ Ваша VIP-заявка принята.\n\n"

        f"Оплата {expected_price} ⭐ подтверждена.\n"

        f"Мы оповестим вас об обработке "
        f"{processing_time}."
    )

    context.user_data.clear()


# =========================
# ЗАПУСК
# =========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден"
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # Кнопки
    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern=(
                "^(report|vip|admin|back|free|"
                "vip_25|vip_50|accept:.*|reject:.*)$"
            ),
        )
    )

    # Успешная оплата
    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment,
        )
    )

    # Обычные сообщения
    app.add_handler(
        MessageHandler(
            filters.ALL,
            message_handler,
        )
    )

    # Проверка оплаты
    app.add_handler(
        PreCheckoutQueryHandler(
            precheckout,
        )
    )

    print("Бот запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()