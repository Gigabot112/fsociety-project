import os
import uuid
import base64

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

# AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

# Администратор
ADMIN_CHAT_ID = 8945804459
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


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def show_report_menu(query):
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
# AI — АНАЛИЗ ФОТО
# =========================================================

async def analyze_photo_with_ai(
    photo_bytes: bytes,
    target: str,
    reason: str
):
    if not OPENAI_API_KEY:
        return (
            "⚠️ AI не подключён.\n\n"
            "Добавьте OPENAI_API_KEY в GitHub Secrets."
        )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY
        )

        encoded = base64.b64encode(
            photo_bytes
        ).decode("utf-8")

        image_data = (
            "data:image/jpeg;base64,"
            + encoded
        )

        prompt = f"""
Ты помогаешь модератору подготовить черновик
жалобы в Telegram.

Цель жалобы:
{target}

Причина, указанная пользователем:
{reason}

Проанализируй предоставленное изображение.

ВАЖНО:
- Не утверждай то, чего на изображении нет.
- Отделяй видимые факты от предположений.
- Не принимай окончательное решение о нарушении.
- Не выдумывай имена, аккаунты или события.
- Составь нейтральный и краткий черновик для
  ручной проверки модератором.

Ответь в формате:

👁 Что видно:
...

📝 Что сообщил пользователь:
...

📋 Черновик жалобы:
...

⚠️ Что нужно проверить модератору:
...
"""

        response = await client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        {
                            "type": "input_image",
                            "image_url": image_data,
                            "detail": "high",
                        },
                    ],
                }
            ],
        )

        return response.output_text

    except Exception as error:
        print(
            "AI ERROR:",
            repr(error)
        )

        return (
            "⚠️ Не удалось выполнить AI-анализ.\n\n"
            "Модератору необходимо проверить "
            "фотографию вручную."
        )


# =========================================================
# ГОТОВЫЙ ТЕКСТ ЖАЛОБЫ
# =========================================================

def build_complaint_text(report):

    if report["evidence_type"] == "photo":
        evidence_description = (
            "К заявке приложено фотографическое "
            "доказательство."
        )

    elif report["evidence_type"] == "document":
        evidence_description = (
            "К заявке приложен документ "
            "с доказательствами."
        )

    else:
        evidence_description = (
            f"Текстовое доказательство:\n"
            f"{report['evidence']}"
        )

    return (
        "📋 ГОТОВЫЙ ЧЕРНОВИК ЖАЛОБЫ\n\n"
        f"Аккаунт/объект: {report['target']}\n\n"
        f"Причина жалобы:\n"
        f"{report['reason']}\n\n"
        f"{evidence_description}\n\n"
        "Прошу проверить указанный аккаунт/контент "
        "на соответствие правилам Telegram и принять "
        "соответствующие меры, если нарушение "
        "подтвердится.\n\n"
        "Это черновик для ручной проверки модератором."
    )


# =========================================================
# VIP — КНОПКИ ОПЛАТЫ
# =========================================================

def vip_payment_keyboard(price: int):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"💳 Оплатить {price} ⭐",
                url="https://t.me/mvcl12"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Я подтвердил оплату",
                callback_data=f"USER_PAYMENT_CONFIRMED:{price}"
            )
        ],
    ])


# =========================================================
# VIP — ИНСТРУКЦИЯ ПО ОПЛАТЕ
# =========================================================

async def show_vip_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    price = context.user_data.get("price")

    if price not in (25, 50):
        return

    if price == 25:
        gift = "🌹 подарок за 25 ⭐"
        processing = "примерно 1 час"
    else:
        gift = "💐 подарок за 50 ⭐"
        processing = "примерно 10–20 минут"

    context.user_data["step"] = "waiting_payment"

    await update.message.reply_text(
        "📋 Данные заявки получены.\n\n"
        f"💳 Для VIP-заявки необходимо оплатить "
        f"{price} ⭐ администратору.\n\n"
        f"👤 Администратор: {ADMIN_USERNAME}\n\n"
        f"Отправьте администратору {gift}.\n\n"
        f"После отправки подарка вернитесь сюда "
        f"и нажмите кнопку «Я подтвердил оплату».\n\n"
        f"⏱ После подтверждения оплаты обработка "
        f"займёт {processing}.",
        reply_markup=vip_payment_keyboard(price)
    )


# =========================================================
# СОЗДАНИЕ VIP ЗАЯВКИ ПОСЛЕ ПОДТВЕРЖДЕНИЯ ПОЛЬЗОВАТЕЛЯ
# =========================================================

async def create_vip_payment_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    price: int
):

    user = update.effective_user

    report_id = uuid.uuid4().hex[:8].upper()

    username = (
        f"@{user.username}"
        if user.username
        else "нет username"
    )

    if price == 25:
        report_type = "👑 VIP"
        processing_time = "примерно за 1 час"
    else:
        report_type = "💎 VIP Gold"
        processing_time = "примерно за 10–20 минут"

    report = {
        "id": report_id,
        "user_id": user.id,
        "username": username,
        "report_type": report_type,
        "processing_time": processing_time,
        "price": price,
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
        "status": "waiting_admin_payment_confirmation",
        "payment_confirmed": False,
        "ai_analysis": None,
    }

    reports = context.application.bot_data.setdefault(
        "reports",
        {}
    )

    reports[report_id] = report

    # Сохраняем ID для пользователя
    context.user_data["report_id"] = report_id

    # =====================================================
    # КНОПКИ ДЛЯ АДМИНА
    # =====================================================

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ ДА, ОПЛАТА ПОЛУЧЕНА",
                callback_data=f"PAYMENT_YES:{report_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ НЕТ, ОПЛАТА НЕ ПОЛУЧЕНА",
                callback_data=f"PAYMENT_NO:{report_id}"
            )
        ],
    ])

    # =====================================================
    # АДМИНУ
    # =====================================================

    admin_text = (
        "💰 ПРОВЕРКА VIP-ОПЛАТЫ\n\n"
        f"🆔 ID заявки: {report_id}\n\n"
        f"Тариф: {report_type}\n"
        f"Сумма: {price} ⭐\n"
        f"Пользователь: {username}\n"
        f"Chat ID: {user.id}\n\n"
        "⚠️ Пользователь утверждает, что отправил "
        f"{price} ⭐ администратору.\n\n"
        "Проверьте свой Telegram-аккаунт.\n\n"
        "Получили подарок?"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        reply_markup=admin_keyboard
    )

    # =====================================================
    # ПОЛЬЗОВАТЕЛЮ
    # =====================================================

    await update.callback_query.message.reply_text(
        "⏳ Спасибо.\n\n"
        "Ваше подтверждение отправлено администратору.\n\n"
        "Администратор проверит получение подарка. "
        "После подтверждения ваша VIP-заявка будет "
        "принята в обработку."
    )


# =========================================================
# ПОЛЬЗОВАТЕЛЬ — ПОДТВЕРДИЛ ОПЛАТУ
# =========================================================

async def user_payment_confirmed(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    price = int(
        query.data.split(":")[1]
    )

    report_id = context.user_data.get(
        "report_id"
    )

    if not report_id:

        await query.message.reply_text(
            "⚠️ Заявка не найдена.\n\n"
            "Пожалуйста, начните оформление заново."
        )

        return

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.message.reply_text(
            "⚠️ Заявка не найдена."
        )

        return

    if report["price"] != price:

        await query.message.reply_text(
            "⚠️ Сумма заявки не совпадает."
        )

        return

    if report["status"] != "waiting_payment":

        await query.message.reply_text(
            "⚠️ Эта заявка уже отправлена "
            "на проверку."
        )

        return

    # Меняем статус
    report["status"] = (
        "waiting_admin_payment_confirmation"
    )

    # =====================================================
    # АДМИНУ
    # =====================================================

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ ДА, ОПЛАТА ПОЛУЧЕНА",
                callback_data=f"PAYMENT_YES:{report_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ НЕТ, ОПЛАТА НЕ ПОЛУЧЕНА",
                callback_data=f"PAYMENT_NO:{report_id}"
            )
        ],
    ])

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "🔔 ПОЛЬЗОВАТЕЛЬ ПОДТВЕРДИЛ ОПЛАТУ\n\n"
            f"🆔 Заявка: {report_id}\n"
            f"Тариф: {report['report_type']}\n"
            f"Сумма: {price} ⭐\n"
            f"Пользователь: {report['username']}\n\n"
            "Пожалуйста, проверьте свой аккаунт "
            "и подтвердите получение подарка."
        ),
        reply_markup=admin_keyboard
    )

    # =====================================================
    # ПОЛЬЗОВАТЕЛЮ
    # =====================================================

    await query.message.reply_text(
        "⏳ Подтверждение отправлено.\n\n"
        "Администратор проверит получение оплаты."
    )


# =========================================================
# АДМИН — ОПЛАТА ПОЛУЧЕНА
# =========================================================

async def payment_yes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    await query.answer(
        "Оплата подтверждена."
    )

    report_id = query.data.split(
        ":",
        1
    )[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.message.reply_text(
            "⚠️ Заявка не найдена."
        )

        return

    if report["status"] != (
        "waiting_admin_payment_confirmation"
    ):

        await query.answer(
            "Эта заявка уже обработана.",
            show_alert=True
        )

        return

    # Подтверждаем оплату
    report["payment_confirmed"] = True
    report["status"] = "pending"

    # =====================================================
    # АДМИНСКОЕ СООБЩЕНИЕ
    # =====================================================

    try:
        await query.edit_message_text(
            "✅ ОПЛАТА ПОДТВЕРЖДЕНА\n\n"
            f"🆔 Заявка: {report_id}\n"
            f"Сумма: {report['price']} ⭐\n"
            f"Пользователь: {report['username']}\n\n"
            "Заявка отправлена на рассмотрение."
        )
    except Exception:
        pass

    # =====================================================
    # ПОЛЬЗОВАТЕЛЮ
    # =====================================================

    await context.bot.send_message(
        chat_id=report["user_id"],
        text=(
            "✅ Ваша VIP-заявка принята!\n\n"
            f"Оплата {report['price']} ⭐ подтверждена.\n\n"
            "Мы приняли вашу VIP-заявку.\n"
            "Оповестим вас о результате в течение "
            f"{report['processing_time']}."
        )
    )

    # =====================================================
    # ОТПРАВЛЯЕМ ЗАЯВКУ АДМИНУ
    # =====================================================

    await send_confirmed_report_to_admin(
        context,
        report
    )


# =========================================================
# АДМИН — ОПЛАТА НЕ ПОЛУЧЕНА
# =========================================================

async def payment_no(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    await query.answer()

    report_id = query.data.split(
        ":",
        1
    )[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.message.reply_text(
            "⚠️ Заявка не найдена."
        )

        return

    report["status"] = "payment_not_confirmed"

    # Сохраняем заявку, которой админ должен ответить
    context.user_data[
        "payment_no_report"
    ] = report_id

    try:
        await query.edit_message_text(
            "❌ ОПЛАТА НЕ ПОДТВЕРЖДЕНА\n\n"
            f"Заявка: {report_id}\n"
            f"Пользователь: {report['username']}\n\n"
            "Напишите следующим сообщением причину.\n"
            "Ваш текст будет отправлен пользователю."
        )
    except Exception:
        pass


# =========================================================
# ОТПРАВКА ПОДТВЕРЖДЁННОЙ ЗАЯВКИ АДМИНУ
# =========================================================

async def send_confirmed_report_to_admin(
    context: ContextTypes.DEFAULT_TYPE,
    report
):

    report_id = report["id"]

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
        "📥 VIP-ЗАЯВКА\n\n"
        f"🆔 ID заявки: {report_id}\n\n"
        f"Тип: {report['report_type']}\n"
        f"Оплата: {report['price']} ⭐ — подтверждена\n"
        f"Пользователь: {report['username']}\n"
        f"Chat ID пользователя: {report['user_id']}\n\n"
        f"🎯 Цель:\n"
        f"{report['target']}\n\n"
        f"📝 Причина:\n"
        f"{report['reason']}\n\n"
        "📎 Доказательство отправлено ниже.\n\n"
        "⏳ Статус: ожидает решения."
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text
    )

    if report["evidence_type"] == "photo":

        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=report["evidence"],
            caption=(
                f"📎 Доказательство заявки {report_id}"
            ),
            reply_markup=admin_keyboard
        )

    elif report["evidence_type"] == "document":

        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=report["evidence"],
            caption=(
                f"📎 Доказательство заявки {report_id}"
            ),
            reply_markup=admin_keyboard
        )

    else:

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"📎 Доказательство заявки "
                f"{report_id}:\n\n"
                f"{report['evidence']}"
            ),
            reply_markup=admin_keyboard
        )


# =========================================================
# СОЗДАНИЕ БЕСПЛАТНОЙ ЗАЯВКИ
# =========================================================

async def create_free_report(
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
        "report_type": "🆓 Бесплатная",
        "processing_time": "в течение 1 дня",
        "price": 0,
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
        "payment_confirmed": True,
        "ai_analysis": None,
    }

    reports = context.application.bot_data.setdefault(
        "reports",
        {}
    )

    reports[report_id] = report

    await send_confirmed_report_to_admin(
        context,
        report
    )


# =========================================================
# АДМИН — ПРИНЯТЬ ЗАЯВКУ
# =========================================================

async def admin_accept(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    report_id = query.data.split(
        ":",
        1
    )[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.answer(
            "Заявка не найдена.",
            show_alert=True
        )

        return

    if report["status"] != "pending":

        await query.answer(
            "Эта заявка уже обработана.",
            show_alert=True
        )

        return

    await query.answer(
        "Заявка принята."
    )

    report["status"] = "accepted"

    # =====================================================
    # AI АНАЛИЗ
    # =====================================================

    if (
        report["evidence_type"] == "photo"
        and OPENAI_API_KEY
    ):

        try:

            file = await context.bot.get_file(
                report["evidence"]
            )

            photo_bytes = (
                await file.download_as_bytearray()
            )

            ai_result = await analyze_photo_with_ai(
                bytes(photo_bytes),
                report["target"],
                report["reason"]
            )

            report["ai_analysis"] = ai_result

        except Exception as error:

            print(
                "PHOTO AI ERROR:",
                repr(error)
            )

            report["ai_analysis"] = (
                "AI-анализ фотографии "
                "не выполнен."
            )

    # =====================================================
    # СТАТУС АДМИНУ
    # =====================================================

    status_text = (
        "✅ ЗАЯВКА ПРИНЯТА\n\n"
        f"🆔 ID: {report_id}\n"
        f"Тип: {report['report_type']}\n\n"
        "Статус: принято к рассмотрению."
    )

    try:

        if query.message.photo:

            await query.edit_message_caption(
                caption=status_text,
                reply_markup=None
            )

        elif query.message.document:

            await query.edit_message_caption(
                caption=status_text,
                reply_markup=None
            )

        else:

            await query.edit_message_text(
                text=status_text,
                reply_markup=None
            )

    except Exception as error:

        print(
            "EDIT ERROR:",
            repr(error)
        )

    # =====================================================
    # ПОЛЬЗОВАТЕЛЮ
    # =====================================================

    try:

        await context.bot.send_message(
            chat_id=report["user_id"],
            text=(
                "✅ Ваша заявка принята "
                "к рассмотрению.\n\n"
                f"Тип: {report['report_type']}\n"
                f"Срок: {report['processing_time']}\n\n"
                "Модератор получил вашу заявку "
                "и доказательства."
            )
        )

    except Exception as error:

        print(
            "USER MESSAGE ERROR:",
            repr(error)
        )

    # =====================================================
    # ГОТОВЫЙ ЧЕРНОВИК
    # =====================================================

    complaint = build_complaint_text(
        report
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=complaint
    )

    # =====================================================
    # AI РЕЗУЛЬТАТ
    # =====================================================

    if report.get("ai_analysis"):

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                "🤖 AI-АНАЛИЗ ДОКАЗАТЕЛЬСТВА\n\n"
                f"{report['ai_analysis']}"
            )
        )

    # =====================================================
    # ОТВЕТ ПОЛЬЗОВАТЕЛЮ
    # =====================================================

    reply_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✍️ Написать свой ответ",
                callback_data=f"ADMIN_REPLY:{report_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⏭️ Пропустить",
                callback_data=f"ADMIN_SKIP:{report_id}"
            )
        ],
    ])

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "💬 Ответ пользователю\n\n"
            "Хотите отправить пользователю "
            "дополнительное сообщение?"
        ),
        reply_markup=reply_keyboard
    )


# =========================================================
# АДМИН — ОТКЛОНИТЬ
# =========================================================

async def admin_reject(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ У вас нет доступа.",
            show_alert=True
        )

        return

    report_id = query.data.split(
        ":",
        1
    )[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    report = reports.get(report_id)

    if not report:

        await query.answer(
            "Заявка не найдена.",
            show_alert=True
        )

        return

    if report["status"] != "pending":

        await query.answer(
            "Эта заявка уже обработана.",
            show_alert=True
        )

        return

    await query.answer(
        "Заявка отклонена."
    )

    report["status"] = "rejected"

    status_text = (
        "❌ ЗАЯВКА ОТКЛОНЕНА\n\n"
        f"🆔 ID: {report_id}\n"
        f"Тип: {report['report_type']}\n\n"
        "Статус: отклонено."
    )

    try:

        if query.message.photo:

            await query.edit_message_caption(
                caption=status_text,
                reply_markup=None
            )

        elif query.message.document:

            await query.edit_message_caption(
                caption=status_text,
                reply_markup=None
            )

        else:

            await query.edit_message_text(
                text=status_text,
                reply_markup=None
            )

    except Exception as error:

        print(
            "EDIT ERROR:",
            repr(error)
        )

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

    except Exception as error:

        print(
            "USER MESSAGE ERROR:",
            repr(error)
        )


# =========================================================
# АДМИН — НАПИСАТЬ ОТВЕТ
# =========================================================

async def admin_reply_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ Нет доступа.",
            show_alert=True
        )

        return

    report_id = query.data.split(
        ":",
        1
    )[1]

    reports = context.application.bot_data.get(
        "reports",
        {}
    )

    if report_id not in reports:

        await query.answer(
            "Заявка не найдена.",
            show_alert=True
        )

        return

    context.user_data[
        "admin_reply_report"
    ] = report_id

    await query.answer()

    await query.edit_message_text(
        "✍️ Напишите сообщение пользователю.\n\n"
        "Ваш следующий текст будет отправлен "
        "этому заявителю."
    )


# =========================================================
# АДМИН — ПРОПУСТИТЬ
# =========================================================

async def admin_skip(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:

        await query.answer(
            "⛔ Нет доступа.",
            show_alert=True
        )

        return

    report_id = query.data.split(
        ":",
        1
    )[1]

    context.user_data.pop(
        "admin_reply_report",
        None
    )

    await query.answer(
        "Дополнительный ответ пропущен."
    )

    await query.edit_message_text(
        "⏭️ Дополнительный ответ пропущен.\n\n"
        f"Заявка: {report_id}"
    )


# =========================================================
# ОБРАБОТКА СООБЩЕНИЙ
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    message = update.message

    # =====================================================
    # АДМИН ОТПРАВЛЯЕТ ПРИЧИНУ ОТКАЗА В ОПЛАТЕ
    # =====================================================

    if (
        message.from_user
        and message.from_user.id == ADMIN_CHAT_ID
        and context.user_data.get("payment_no_report")
    ):

        report_id = context.user_data.get(
            "payment_no_report"
        )

        reports = context.application.bot_data.get(
            "reports",
            {}
        )

        report = reports.get(report_id)

        if not report:

            context.user_data.pop(
                "payment_no_report",
                None
            )

            await message.reply_text(
                "⚠️ Заявка не найдена."
            )

            return

        if not message.text:

            await message.reply_text(
                "Пожалуйста, напишите сообщение "
                "текстом."
            )

            return

        custom_text = message.text.strip()

        try:

            await context.bot.send_message(
                chat_id=report["user_id"],
                text=(
                    "❌ Оплата пока не подтверждена.\n\n"
                    f"{custom_text}"
                )
            )

            await message.reply_text(
                "✅ Сообщение отправлено пользователю."
            )

        except Exception:

            await message.reply_text(
                "⚠️ Не удалось отправить сообщение."
            )

        context.user_data.pop(
            "payment_no_report",
            None
        )

        return

    # =====================================================
    # АДМИН ПИШЕТ ОБЫЧНЫЙ ОТВЕТ
    # =====================================================

    admin_reply_report = (
        context.user_data.get(
            "admin_reply_report"
        )
        if message.from_user
        and message.from_user.id == ADMIN_CHAT_ID
        else None
    )

    if admin_reply_report:

        reports = context.application.bot_data.get(
            "reports",
            {}
        )

        report = reports.get(
            admin_reply_report
        )

        if not report:

            context.user_data.pop(
                "admin_reply_report",
                None
            )

            await message.reply_text(
                "⚠️ Заявка не найдена."
            )

            return

        if not message.text:

            await message.reply_text(
                "Пожалуйста, отправьте ответ текстом."
            )

            return

        custom_text = message.text.strip()

        try:

            await context.bot.send_message(
                chat_id=report["user_id"],
                text=(
                    "💬 Сообщение от модератора:\n\n"
                    f"{custom_text}"
                )
            )

            await message.reply_text(
                "✅ Ответ отправлен пользователю."
            )

        except Exception:

            await message.reply_text(
                "⚠️ Не удалось отправить сообщение "
                "пользователю."
            )

        context.user_data.pop(
            "admin_reply_report",
            None
        )

        return

    # =====================================================
    # ОБЫЧНЫЙ USER FLOW
    # =====================================================

    step = context.user_data.get(
        "step"
    )

    # =====================================================
    # TARGET
    # =====================================================

    if step == "target":

        if not message.text:

            await message.reply_text(
                "Пожалуйста, отправьте username "
                "или ссылку текстом."
            )

            return

        context.user_data["target"] = (
            message.text.strip()
        )

        context.user_data["step"] = "reason"

        await message.reply_text(
            "Шаг 2 из 3.\n"
            "Напишите причину жалобы."
        )

        return

    # =====================================================
    # REASON
    # =====================================================

    if step == "reason":

        if not message.text:

            await message.reply_text(
                "Пожалуйста, напишите причину текстом."
            )

            return

        context.user_data["reason"] = (
            message.text.strip()
        )

        context.user_data["step"] = "evidence"

        await message.reply_text(
            "Шаг 3 из 3.\n"
            "Отправьте доказательства.\n\n"
            "Можно отправить текст, фотографию "
            "или документ."
        )

        return

    # =====================================================
    # EVIDENCE
    # =====================================================

    if step == "evidence":

        if message.photo:

            context.user_data["evidence"] = (
                message.photo[-1].file_id
            )

            context.user_data["evidence_type"] = (
                "photo"
            )

        elif message.document:

            context.user_data["evidence"] = (
                message.document.file_id
            )

            context.user_data["evidence_type"] = (
                "document"
            )

        elif message.text:

            context.user_data["evidence"] = (
                message.text.strip()
            )

            context.user_data["evidence_type"] = (
                "text"
            )

        else:

            await message.reply_text(
                "Отправьте текст, фотографию "
                "или документ."
            )

            return

        price = context.user_data.get(
            "price",
            0
        )

        # =================================================
        # FREE
        # =================================================

        if price == 0:

            await create_free_report(
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

        # =================================================
        # VIP
        # =================================================

        await show_vip_payment(
            update,
            context
        )

        return


# =========================================================
# КНОПКИ ПОЛЬЗОВАТЕЛЯ
# =========================================================

async def user_buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    data = query.data

    await query.answer()

    # =====================================================
    # ЖАЛОБА
    # =====================================================

    if data == "report":

        await show_report_menu(
            query
        )

        return

    # =====================================================
    # VIP
    # =====================================================

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

    # =====================================================
    # АДМИН
    # =====================================================

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

    # =====================================================
    # НАЗАД
    # =====================================================

    if data == "back":

        await query.edit_message_text(
            "👋 Главное меню:",
            reply_markup=main_menu()
        )

        return

    # =====================================================
    # ТИП ЖАЛОБЫ
    # =====================================================

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

        context.user_data["report_type"] = (
            report_type
        )

        context.user_data["processing_time"] = (
            processing_time
        )

        context.user_data["price"] = price

        await query.message.reply_text(
            f"{report_type}\n\n"
            "Шаг 1 из 3.\n"
            "Отправьте username или ссылку на аккаунт."
        )

        return


# =========================================================
# ЗАПУСК
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

    # =====================================================
    # START
    # =====================================================

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # =====================================================
    # АДМИН — ОПЛАТА ДА
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            payment_yes,
            pattern=r"^PAYMENT_YES:"
        )
    )

    # =====================================================
    # АДМИН — ОПЛАТА НЕТ
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            payment_no,
            pattern=r"^PAYMENT_NO:"
        )
    )

    # =====================================================
    # USER — ПОДТВЕРДИЛ ОПЛАТУ
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            user_payment_confirmed,
            pattern=r"^USER_PAYMENT_CONFIRMED:"
        )
    )

    # =====================================================
    # ADMIN ACCEPT
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            admin_accept,
            pattern=r"^ADMIN_ACCEPT:"
        )
    )

    # =====================================================
    # ADMIN REJECT
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            admin_reject,
            pattern=r"^ADMIN_REJECT:"
        )
    )

    # =====================================================
    # ADMIN REPLY
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            admin_reply_button,
            pattern=r"^ADMIN_REPLY:"
        )
    )

    # =====================================================
    # ADMIN SKIP
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            admin_skip,
            pattern=r"^ADMIN_SKIP:"
        )
    )

    # =====================================================
    # USER BUTTONS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            user_buttons,
            pattern=(
                r"^(report|vip|admin|back|"
                r"free|vip_25|vip_50)$"
            )
        )
    )

    # =====================================================
    # ОСТАЛЬНЫЕ СООБЩЕНИЯ
    # =====================================================

    app.add_handler(
        MessageHandler(
            filters.ALL,
            message_handler
        )
    )

    print(
        "Бот запущен!"
    )

    app.run_polling()


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()