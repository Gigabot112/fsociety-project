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


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

# Telegram ID аккаунта администратора,
# который получает заявки
ADMIN_CHAT_ID = 8945804459

# Username администратора
ADMIN_USERNAME = "@mvcl12"


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📩 Подать жалобу",
                callback_data="report"
            )
        ],
        [
            InlineKeyboardButton(
                "👑 VIP",
                callback_data="vip"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Связаться с админом",
                callback_data="admin"
            )
        ],
    ])


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu()
    )


# =========================================================
# МЕНЮ ЖАЛОБ
# =========================================================

def report_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🆓 Бесплатная жалоба",
                callback_data="free"
            )
        ],
        [
            InlineKeyboardButton(
                "👑 VIP — 25 ⭐",
                callback_data="vip_25"
            )
        ],
        [
            InlineKeyboardButton(
                "💎 VIP Gold — 50 ⭐",
                callback_data="vip_50"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data="back"
            )
        ],
    ])


async def show_report_menu(
    query
):
    await query.edit_message_text(
        "📩 Подать жалобу\n\n"

        "🆓 Бесплатная\n"
        "Обработка в течение 1 дня.\n\n"

        "👑 VIP — 25 ⭐\n"
        "Обработка примерно за 1 час.\n\n"

        "💎 VIP Gold — 50 ⭐\n"
        "Обработка примерно за 10–20 минут.\n\n"

        "Выберите вариант:",
        reply_markup=report_menu()
    )


# =========================================================
# ОБЩИЕ КНОПКИ ПОЛЬЗОВАТЕЛЯ
# =========================================================

async def user_buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    data = query.data

    await query.answer()

    # -------------------------
    # Подать жалобу
    # -------------------------

    if data == "report":
        await show_report_menu(query)
        return

    # -------------------------
    # VIP
    # -------------------------

    if data == "vip":

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "👑 VIP — 25 ⭐",
                    callback_data="vip_25"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 VIP Gold — 50 ⭐",
                    callback_data="vip_50"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data="back"
                )
            ],
        ])

        await query.edit_message_text(
            "👑 VIP\n\n"

            "👑 VIP — 25 ⭐\n"
            "Обработка примерно за 1 час.\n\n"

            "💎 VIP Gold — 50 ⭐\n"
            "Обработка примерно за 10–20 минут.",
            reply_markup=keyboard
        )

        return

    # -------------------------
    # Связь с админом
    # -------------------------

    if data == "admin":

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "👤 Открыть профиль админа",
                    url="https://t.me/mvcl12"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data="back"
                )
            ],
        ])

        await query.edit_message_text(
            f"👤 Администратор: {ADMIN_USERNAME}\n\n"
            "Вы можете открыть профиль администратора.",
            reply_markup=keyboard
        )

        return

    # -------------------------
    # Назад
    # -------------------------

    if data == "back":

        await query.edit_message_text(
            "👋 Главное меню:",
            reply_markup=main_menu()
        )

        return

    # -------------------------
    # Бесплатная / VIP
    # -------------------------

    if data in (
        "free",
        "vip_25",
        "vip_50"
    ):

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
            "Отправьте username или ссылку на аккаунт."
        )

        return


# =========================================================
# ОБРАБОТКА ЗАЯВКИ ОТ ПОЛЬЗОВАТЕЛЯ
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    message = update.message
    step = context.user_data.get("step")

    # =====================================================
    # ШАГ 1 — ЦЕЛЬ
    # =====================================================

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

    # =====================================================
    # ШАГ 2 — ПРИЧИНА
    # =====================================================

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

    # =====================================================
    # ШАГ 3 — ДОКАЗАТЕЛЬСТВА
    # =====================================================

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

            context.user_data["evidence"] = message.text
            context.user_data["evidence_type"] = "text"

        else:

            await message.reply_text(
                "Отправьте текст, фотографию или документ."
            )
            return

        price = context.user_data.get("price", 0)

        # -------------------------------------------------
        # БЕСПЛАТНАЯ ЗАЯВКА
        # -------------------------------------------------

        if price == 0:

            await create_report(
                update,
                context
            )

            await message.reply_text(
                "✅ Ваша заявка принята.\n\n"
                "Мы оповестим вас об обработке "
                "в течение 1 дня."
            )

            context.user_data.clear()

            return

        # -------------------------------------------------
        # VIP
        # -------------------------------------------------

        if price == 25:

            title = "VIP — жалоба"
            payload = "vip_25"

        else:

            title = "VIP Gold — жалоба"
            payload = "vip_50"

        await message.reply_text(
            f"📋 Данные заявки получены.\n\n"
            f"Теперь оплатите {price} ⭐."
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
                    price
                )
            ],
        )

        context.user_data["step"] = "payment"


# =========================================================
# СОЗДАНИЕ ЗАЯВКИ
# =========================================================

async def create_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
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
            "Неизвестно"
        ),

        "processing_time": context.user_data.get(
            "processing_time",
            "Не указан"
        ),

        "target": context.user_data.get(
            "target",
            "Не указана"
        ),

        "reason": context.user_data.get(
            "reason",
            "Не указана"
        ),

        "evidence": context.user_data.get(
            "evidence",
            "Нет"
        ),

        "evidence_type": context.user_data.get(
            "evidence_type",
            "text"
        ),

        "status": "pending",
    }

    # Сохраняем заявку внутри приложения
    reports = context.application.bot_data.setdefault(
        "reports",
        {}
    )

    reports[report_id] = report

    # =====================================================
    # ВОТ ЭТИ КНОПКИ ПОЛУЧИТ АДМИН
    # =====================================================

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ ПРИНЯТЬ ЗАЯВКУ",
                callback_data=f"ADMIN_ACCEPT:{report_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ ОТКЛОНИТЬ ЗАЯВКУ",
                callback_data=f"ADMIN_REJECT:{report_id}"
            )
        ],
    ])

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
        "Вложение отправлено следующим сообщением.\n\n"

        "⏳ Статус: ожидает решения."
    )

    # Отправляем ГЛАВНОЕ сообщение с кнопками
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        reply_markup=admin_keyboard
    )

    # =====================================================
    # ОТПРАВЛЯЕМ ДОКАЗАТЕЛЬСТВА
    # =====================================================

    if report["evidence_type"] == "photo":

        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=report["evidence"],
            caption=(
                f"📎 Доказательство заявки "
                f"{report_id}"
            )
        )

    elif report["evidence_type"] == "document":

        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=report["evidence"],
            caption=(
                f"📎 Доказательство заявки "
                f"{report_id}"
            )
        )

    else:

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📎 Доказательство заявки "
                f"{report_id}:\n\n"
                f"{report['evidence']}"
            )
        )


# =========================================================
# АДМИН — ПРИНЯТЬ ЗАЯВКУ
# =========================================================

async def admin_accept(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    # Проверяем администратора
    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    await query.answer("Заявка принята.")

    report_id = query.data.split(":", 1)[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.edit_message_text(
            "⚠️ Заявка не найдена.\n\n"
            "Возможно, бот был перезапущен."
        )

        return

    report["status"] = "accepted"

    # Меняем кнопки/сообщение
    await query.edit_message_text(
        "✅ ЗАЯВКА ПРИНЯТА\n\n"

        f"🆔 ID: {report_id}\n"
        f"Тип: {report['report_type']}\n\n"

        f"🎯 Цель:\n"
        f"{report['target']}\n\n"

        "Статус: принято к рассмотрению."
    )

    # Сообщаем заявителю
    try:

        await context.bot.send_message(
            chat_id=report["user_id"],
            text=(
                "✅ Ваша заявка принята "
                "к рассмотрению.\n\n"

                f"Тип: {report['report_type']}\n"
                f"Срок: {report['processing_time']}\n\n"

                "Модератор получил вашу заявку "
                "и предоставленные доказательства."
            )
        )

    except Exception:
        pass


# =========================================================
# АДМИН — ОТКЛОНИТЬ ЗАЯВКУ
# =========================================================

async def admin_reject(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    # Проверяем администратора
    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    await query.answer("Заявка отклонена.")

    report_id = query.data.split(":", 1)[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.edit_message_text(
            "⚠️ Заявка не найдена.\n\n"
            "Возможно, бот был перезапущен."
        )

        return

    report["status"] = "rejected"

    await query.edit_message_text(
        "❌ ЗАЯВКА ОТКЛОНЕНА\n\n"

        f"🆔 ID: {report_id}\n"
        f"Тип: {report['report_type']}\n\n"

        f"🎯 Цель:\n"
        f"{report['target']}\n\n"

        "Статус: отклонено."
    )

    # Сообщаем заявителю
    try:

        await context.bot.send_message(
            chat_id=report["user_id"],
            text=(
                "❌ Ваша заявка была "
                "отклонена модератором.\n\n"

                "Если вы считаете, что это произошло "
                "по ошибке, обратитесь к администратору."
            )
        )

    except Exception:
        pass


# =========================================================
# PRE-CHECKOUT
# =========================================================

async def precheckout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.pre_checkout_query

    if query.invoice_payload == "vip_25":

        expected_price = 25

    elif query.invoice_payload == "vip_50":

        expected_price = 50

    else:

        await query.answer(
            ok=False,
            error_message="Неизвестный заказ."
        )

        return

    if query.total_amount != expected_price:

        await query.answer(
            ok=False,
            error_message="Неверная сумма."
        )

        return

    await query.answer(ok=True)


# =========================================================
# УСПЕШНАЯ ОПЛАТА
# =========================================================

async def successful_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    payment = update.message.successful_payment

    if payment.invoice_payload == "vip_25":

        expected_price = 25
        processing_time = "примерно за 1 час"

    elif payment.invoice_payload == "vip_50":

        expected_price = 50
        processing_time = "примерно за 10–20 минут"

    else:

        await update.message.reply_text(
            "⚠️ Неизвестный платёж."
        )

        return

    if payment.total_amount != expected_price:

        await update.message.reply_text(
            "⚠️ Не удалось подтвердить оплату."
        )

        return

    await create_report(
        update,
        context
    )

    await update.message.reply_text(
        "✅ Ваша VIP-заявка принята.\n\n"

        f"Оплата {expected_price} ⭐ подтверждена.\n"

        f"Обработка: {processing_time}."
    )

    context.user_data.clear()


# =========================================================
# ЗАПУСК БОТА
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден."
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
            start
        )
    )

    # -----------------------------------------------------
    # АДМИНСКИЕ КНОПКИ
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            admin_accept,
            pattern=r"^ADMIN_ACCEPT:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_reject,
            pattern=r"^ADMIN_REJECT:"
        )
    )

    # -----------------------------------------------------
    # ОСТАЛЬНЫЕ КНОПКИ
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            user_buttons,
            pattern=r"^(report|vip|admin|back|free|vip_25|vip_50)$"
        )
    )

    # -----------------------------------------------------
    # УСПЕШНАЯ ОПЛАТА
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment
        )
    )

    # -----------------------------------------------------
    # ОБЫЧНЫЕ СООБЩЕНИЯ
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.ALL,
            message_handler
        )
    )

    # -----------------------------------------------------
    # PRE-CHECKOUT
    # -----------------------------------------------------

    app.add_handler(
        PreCheckoutQueryHandler(
            precheckout
        )
    )

    print("Бот запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()