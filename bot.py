import os
import uuid
import base64
import asyncio
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
# AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
# Администратор
ADMIN_CHAT_ID = 8945804459
ADMIN_USERNAME = "@mvcl12"
# =========================================================
# ПОДАРКИ TELEGRAM
# =========================================================
#
# В GitHub Secrets можно добавить:
#
# VIP_GIFT_ID=ID_ПОДАРКА_ДЛЯ_25
# GOLD_GIFT_ID=ID_ПОДАРКА_ДЛЯ_50
#
# Если оставить пустым — подарок автоматически
# отправляться не будет.
#
VIP_GIFT_ID = os.getenv("VIP_GIFT_ID")
GOLD_GIFT_ID = os.getenv("GOLD_GIFT_ID")
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
        # Импортируем только если AI действительно используется
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
    evidence_description = ""
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
# ОТПРАВКА ПОДАРКА АДМИНУ
# =========================================================
async def send_gift_to_admin(
    context: ContextTypes.DEFAULT_TYPE,
    gift_id: str | None,
    report_type: str
):
    if not gift_id:
        return False
    try:
        # python-telegram-bot может не иметь метода
        # send_gift в старой установленной версии.
        # Поэтому используем напрямую Bot API через HTTP.
        import aiohttp
        url = (
            f"https://api.telegram.org/bot"
            f"{TOKEN}/sendGift"
        )
        payload = {
            "user_id": ADMIN_CHAT_ID,
            "gift_id": gift_id,
            "text": (
                f"🎁 Подарок за {report_type}"
            ),
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=30
            ) as response:
                data = await response.json()
                print(
                    "GIFT RESPONSE:",
                    data
                )
                return bool(
                    data.get("ok")
                )
    except Exception as error:
        print(
            "GIFT ERROR:",
            repr(error)
        )
        return False
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
    # -----------------------------------------------------
    # ЖАЛОБА
    # -----------------------------------------------------
    if data == "report":
        await show_report_menu(query)
        return
    # -----------------------------------------------------
    # VIP
    # -----------------------------------------------------
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
    # -----------------------------------------------------
    # АДМИН
    # -----------------------------------------------------
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
    # -----------------------------------------------------
    # НАЗАД
    # -----------------------------------------------------
    if data == "back":
        await query.edit_message_text(
            "👋 Главное меню:",
            reply_markup=main_menu()
        )
        return
    # -----------------------------------------------------
    # ТИП ЖАЛОБЫ
    # -----------------------------------------------------
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
# ОБРАБОТКА СООБЩЕНИЙ
# =========================================================
async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return
    message = update.message
    # -----------------------------------------------------
    # АДМИН ПИШЕТ СОБСТВЕННЫЙ ОТВЕТ
    # -----------------------------------------------------
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
    # -----------------------------------------------------
    # ОБЫЧНЫЙ USER FLOW
    # -----------------------------------------------------
    step = context.user_data.get("step")
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
        # -------------------------------------------------
        # FREE
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
        # VIP PAYMENT
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
        return
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
        "ai_analysis": None,
        "payment_confirmed": (
            context.user_data.get(
                "price",
                0
            ) == 0
        ),
    }
    reports = context.application.bot_data.setdefault(
        "reports",
        {}
    )
    reports[report_id] = report
    # =====================================================
    # ADMIN BUTTONS
    # =====================================================
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ ПРИНЯТЬ ЗАЯВКУ",
                callback_data=(
                    f"ADMIN_ACCEPT:{report_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "❌ ОТКЛОНИТЬ ЗАЯВКУ",
                callback_data=(
                    f"ADMIN_REJECT:{report_id}"
                )
            )
        ],
    ])
    # =====================================================
    # ADMIN INFO
    # =====================================================
    admin_text = (
        "📥 НОВАЯ ЗАЯВКА\n\n"
        f"🆔 ID заявки: {report_id}\n\n"
        f"Тип: {report['report_type']}\n"
        f"Пользователь: {report['username']}\n"
        f"Chat ID пользователя: "
        f"{report['user_id']}\n\n"
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
    # =====================================================
    # EVIDENCE
    # =====================================================
    if report["evidence_type"] == "photo":
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=report["evidence"],
            caption=(
                f"📎 Доказательство заявки "
                f"{report_id}"
            ),
            reply_markup=admin_keyboard
        )
    elif report["evidence_type"] == "document":
        await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=report["evidence"],
            caption=(
                f"📎 Доказательство заявки "
                f"{report_id}"
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
# ПОСЛЕ ОПЛАТЫ
# =========================================================
async def successful_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    payment = update.message.successful_payment
    if payment.invoice_payload == "vip_25":
        expected_price = 25
        processing_time = (
            "примерно за 1 час"
        )
        report_type = "👑 VIP"
        gift_id = VIP_GIFT_ID
    elif payment.invoice_payload == "vip_50":
        expected_price = 50
        processing_time = (
            "примерно за 10–20 минут"
        )
        report_type = "💎 VIP Gold"
        gift_id = GOLD_GIFT_ID
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
    context.user_data["report_type"] = (
        report_type
    )
    context.user_data["processing_time"] = (
        processing_time
    )
    context.user_data["price"] = (
        expected_price
    )
    context.user_data["payment_confirmed"] = True
    # =====================================================
    # СОЗДАЁМ ЗАЯВКУ
    # =====================================================
    await create_report(
        update,
        context
    )
    # =====================================================
    # УВЕДОМЛЕНИЕ ПОЛЬЗОВАТЕЛЮ
    # =====================================================
    await update.message.reply_text(
        "✅ VIP-заявка принята.\n\n"
        f"Оплата {expected_price} ⭐ подтверждена.\n"
        f"Обработка: {processing_time}."
    )
    # =====================================================
    # УВЕДОМЛЕНИЕ АДМИНУ
    # =====================================================
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "💰 ПЛАТЁЖ ПОЛУЧЕН\n\n"
            f"Тариф: {report_type}\n"
            f"Сумма: {expected_price} ⭐\n"
            f"Пользователь: "
            f"{update.effective_user.id}\n\n"
            "Заявка уже отправлена выше."
        )
    )
    # =====================================================
    # ПОДАРОК
    # =====================================================
    if gift_id:
        success = await send_gift_to_admin(
            context,
            gift_id,
            report_type
        )
        if success:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    "🎁 Подарок автоматически "
                    "отправлен на аккаунт администратора."
                )
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    "⚠️ Платёж получен, но подарок "
                    "автоматически отправить не удалось."
                )
            )
    context.user_data.clear()
# =========================================================
# АДМИН — ПРИНЯТЬ
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
    report = reports.get(
        report_id
    )
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
        report["evidence_type"]
        == "photo"
        and OPENAI_API_KEY
    ):
        try:
            file = await context.bot.get_file(
                report["evidence"]
            )
            photo_bytes = await file.download_as_bytearray()
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
    # СТАТУС
    # =====================================================
    status_text = (
        f"✅ ЗАЯВКА ПРИНЯТА\n\n"
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
    # КНОПКИ ОТВЕТА
    # =====================================================
    reply_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✍️ Написать свой ответ",
                callback_data=(
                    f"ADMIN_REPLY:{report_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "⏭️ Пропустить",
                callback_data=(
                    f"ADMIN_SKIP:{report_id}"
                )
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
    report = reports.get(
        report_id
    )
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
        f"❌ ЗАЯВКА ОТКЛОНЕНА\n\n"
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
    # =====================================================
    # ПОЛЬЗОВАТЕЛЮ
    # =====================================================
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
    # =====================================================
    # ОПЦИОНАЛЬНЫЙ ОТВЕТ
    # =====================================================
    reply_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✍️ Написать свой ответ",
                callback_data=(
                    f"ADMIN_REPLY:{report_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "⏭️ Пропустить",
                callback_data=(
                    f"ADMIN_SKIP:{report_id}"
                )
            )
        ],
    ])
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "💬 Ответ пользователю\n\n"
            "Хотите отправить дополнительное "
            "сообщение?"
        ),
        reply_markup=reply_keyboard
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
        f"⏭️ Дополнительный ответ пропущен.\n\n"
        f"Заявка: {report_id}"
    )
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
    await query.answer(
        ok=True
    )
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
    # -----------------------------------------------------
    # START
    # -----------------------------------------------------
    app.add_handler(
        CommandHandler(
            "start",
            start
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
    # -----------------------------------------------------
    # ADMIN ACCEPT
    # -----------------------------------------------------
    app.add_handler(
        CallbackQueryHandler(
            admin_accept,
            pattern=r"^ADMIN_ACCEPT:"
        )
    )
    # -----------------------------------------------------
    # ADMIN REJECT
    # -----------------------------------------------------
    app.add_handler(
        CallbackQueryHandler(
            admin_reject,
            pattern=r"^ADMIN_REJECT:"
        )
    )
    # -----------------------------------------------------
    # ADMIN REPLY
    # -----------------------------------------------------
    app.add_handler(
        CallbackQueryHandler(
            admin_reply_button,
            pattern=r"^ADMIN_REPLY:"
        )
    )
    # -----------------------------------------------------
    # ADMIN SKIP
    # -----------------------------------------------------
    app.add_handler(
        CallbackQueryHandler(
            admin_skip,
            pattern=r"^ADMIN_SKIP:"
        )
    )
    # -----------------------------------------------------
    # USER BUTTONS
    # -----------------------------------------------------
    app.add_handler(
        CallbackQueryHandler(
            user_buttons,
            pattern=(
                r"^(report|vip|admin|back|"
                r"free|vip_25|vip_50)$"
            )
        )
    )
    # -----------------------------------------------------
    # SUCCESSFUL PAYMENT
    # -----------------------------------------------------
    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment
        )
    )
    # -----------------------------------------------------
    # ОСТАЛЬНЫЕ СООБЩЕНИЯ
    # -----------------------------------------------------
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