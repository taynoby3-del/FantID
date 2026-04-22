# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from collections import defaultdict, deque
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ================== КОНФИГ ==================
TOKEN = "8791632400:AAGr7NZceT_713LS_28omSU7lhhKd0yUSxE"
CHANNEL_LINK = "https://t.me/Fant1kKanal"
PHOTO_PATH = "start.jpg"
STICKER_ID = "CAACAgIAAxkBAAEW-Zhp6PvpjVww_OSp-qPxRnb_sZl4IQACKT4AAu_rwUpFGYItDzsqSTsE"  # замени на свой file_id анимированного стикера

# ================== ЛОГИРОВАНИЕ ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ================== ХРАНИЛИЩА ==================
user_stats = defaultdict(lambda: defaultdict(int))
user_history = defaultdict(lambda: deque(maxlen=10))

def update_stats(user_id, cmd):
    user_stats[user_id][cmd] += 1

def add_history(user_id, obj_type, obj_id, obj_name=""):
    user_history[user_id].append((obj_type, obj_name or str(obj_id), obj_id))

def get_stats_text(user_id):
    stats = user_stats.get(user_id, {})
    if not stats:
        return "📊 Статистика пуста."
    text = "<b>📊 Статистика:</b>\n"
    for cmd, cnt in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        text += f"• {cmd}: {cnt}\n"
    return text

def get_history_text(user_id):
    history = user_history.get(user_id, [])
    if not history:
        return "📭 История пуста."
    text = "<b>📜 Последние 10 ID:</b>\n"
    for typ, name, oid in reversed(history):
        text += f"• {typ}: <code>{name}</code> → <code>{oid}</code>\n"
    return text

async def safe_edit_or_send(message, text, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    kb = [
        [InlineKeyboardButton("🆔 Узнать айди", callback_data="get_id_menu")],
        [InlineKeyboardButton("📊 Статистика", callback_data="show_stats")],
        [InlineKeyboardButton("📜 История", callback_data="show_history")],
        [InlineKeyboardButton("📢 Наш канал", callback_data="channel_info")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(kb)

def id_type_menu():
    kb = [
        [InlineKeyboardButton("👤 Юзер", callback_data="id_user")],
        [InlineKeyboardButton("🤖 Бот", callback_data="id_bot")],
        [InlineKeyboardButton("📢 Канал", callback_data="id_channel")],
        [InlineKeyboardButton("🎨 Стикер", callback_data="id_sticker")],
        [InlineKeyboardButton("🔢 ID чата", callback_data="get_chat_id")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(kb)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]])

# ================== СТАРТ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_stats(user.id, "/start")
    caption = (
        f"🆄 Привет, {user.first_name}!\n\n"
        "<b>Fant ID</b> – показываю ID любых объектов.\n\n"
        "🔹 Нажми «Узнать айди» → выбери тип.\n"
        "🔹 Перешли сообщение от нужного пользователя/бота/канала.\n"
        "🔹 Отправь стикер – получу file_id.\n"
        "🔹 /id – ID этого чата.\n\n"
        "👇 Начни:"
    )
    if os.path.exists(PHOTO_PATH):
        with open(PHOTO_PATH, "rb") as f:
            await update.message.reply_photo(photo=InputFile(f), caption=caption, parse_mode="HTML", reply_markup=main_menu())
    else:
        await update.message.reply_html(caption, reply_markup=main_menu())
    if STICKER_ID:
        try:
            await update.message.reply_sticker(sticker=STICKER_ID)
        except:
            pass

# ================== НАВИГАЦИЯ ==================
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    caption = f"🆄 Привет, {user.first_name}!\nГлавное меню:"
    if os.path.exists(PHOTO_PATH):
        with open(PHOTO_PATH, "rb") as f:
            await query.message.reply_photo(photo=InputFile(f), caption=caption, parse_mode="HTML", reply_markup=main_menu())
            await query.message.delete()
    else:
        await safe_edit_or_send(query.message, caption, reply_markup=main_menu())

async def get_id_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await safe_edit_or_send(query.message, "🔍 <b>Выбери тип объекта:</b>", reply_markup=id_type_menu())

# ================== ВЫБОР ТИПА ==================
async def id_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_type"] = "user"
    await safe_edit_or_send(query.message, "👤 Перешли любое сообщение от пользователя.", reply_markup=back_button())

async def id_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_type"] = "bot"
    await safe_edit_or_send(query.message, "🤖 Перешли любое сообщение от бота.", reply_markup=back_button())

async def id_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_type"] = "channel"
    await safe_edit_or_send(query.message, "📢 Перешли сообщение из канала (бот должен быть участником).", reply_markup=back_button())

async def id_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_sticker"] = True
    await safe_edit_or_send(query.message, "🎨 Отправь стикер.", reply_markup=back_button())

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    update_stats(user_id, "ID чата (кнопка)")
    add_history(user_id, "Чат", chat_id, "текущий чат")
    await safe_edit_or_send(query.message, f"🔢 <b>ID этого чата:</b> <code>{chat_id}</code>", reply_markup=back_button())

# ================== ОСНОВНОЙ ОБРАБОТЧИК ПЕРЕСЛАННЫХ СООБЩЕНИЙ ==================
async def handle_forwarded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_type" not in context.user_data:
        return
    obj_type = context.user_data.pop("awaiting_type")
    msg = update.message
    user_id = update.effective_user.id

    # Получаем информацию об оригинальном отправителе через forward_origin
    origin = msg.forward_origin
    if origin is None:
        await update.message.reply_text("❌ Не удалось определить отправителя (возможно, переслано без сохранения оригинала).")
        return

    original_id = None
    original_name = None
    is_bot = False

    if origin.type == "user":
        original_id = origin.user.id
        original_name = origin.user.first_name
        is_bot = origin.user.is_bot
    elif origin.type == "chat":
        original_id = origin.chat.id
        original_name = origin.chat.title
    elif origin.type == "channel":
        original_id = origin.chat.id
        original_name = origin.chat.title
    else:
        await update.message.reply_text("❌ Неподдерживаемый тип пересылки.")
        return

    if original_id is None:
        await update.message.reply_text("❌ Не удалось извлечь ID.")
        return

    # Проверка соответствия типа
    success = False
    if obj_type == "user":
        if not is_bot and origin.type == "user":
            await update.message.reply_html(f"👤 <b>Пользователь:</b> {original_name}\n🆔 <code>{original_id}</code>")
            update_stats(user_id, "ID пользователя")
            add_history(user_id, "Пользователь", original_id, original_name)
            success = True
        else:
            await update.message.reply_text("❌ Это не пользователь (или бот). Выберите правильный тип.")
    elif obj_type == "bot":
        if is_bot:
            await update.message.reply_html(f"🤖 <b>Бот:</b> {original_name}\n🆔 <code>{original_id}</code>")
            update_stats(user_id, "ID бота")
            add_history(user_id, "Бот", original_id, original_name)
            success = True
        else:
            await update.message.reply_text("❌ Это не бот.")
    elif obj_type == "channel":
        if origin.type in ("chat", "channel"):
            await update.message.reply_html(f"📢 <b>Канал:</b> {original_name}\n🆔 <code>{original_id}</code>")
            update_stats(user_id, "ID канала")
            add_history(user_id, "Канал", original_id, original_name)
            success = True
        else:
            await update.message.reply_text("❌ Это не канал.")

    if not success:
        await update.message.reply_text("❌ Не удалось определить ID. Попробуйте ещё раз.")
    await update.message.reply_html("🏠 /start – вернуться в меню")

# ================== СТИКЕРЫ ==================
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sticker = update.message.sticker
    if context.user_data.get("awaiting_sticker"):
        context.user_data["awaiting_sticker"] = False
        await update.message.reply_html(
            f"🎨 <b>Стикер (по запросу)</b>\n"
            f"<code>file_id</code>: <code>{sticker.file_id}</code>\n"
            f"<code>file_unique_id</code>: <code>{sticker.file_unique_id}</code>\n"
            f"😀 Эмодзи: {sticker.emoji or '?'}"
        )
        update_stats(user_id, "Стикер (запрос)")
        add_history(user_id, "Стикер", sticker.file_id[:20] + "...", sticker.emoji)
    else:
        await update.message.reply_html(f"🎨 <b>Стикер</b>\n<code>file_id</code>: <code>{sticker.file_id}</code>")
        update_stats(user_id, "Стикер (отправка)")
        add_history(user_id, "Стикер", sticker.file_id[:20] + "...", sticker.emoji)

# ================== МЕДИА ==================
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message
    text = f"🆔 <b>Ваш ID:</b> <code>{update.effective_user.id}</code>\n<b>ID чата:</b> <code>{update.effective_chat.id}</code>\n<b>ID сообщения:</b> <code>{msg.message_id}</code>"
    if msg.photo:
        fid = msg.photo[-1].file_id
        text += f"\n\n🖼️ <b>Фото</b>\n<code>file_id</code>: <code>{fid}</code>"
        update_stats(user_id, "Фото")
    elif msg.video:
        text += f"\n\n🎬 <b>Видео</b>\n<code>file_id</code>: <code>{msg.video.file_id}</code>"
        update_stats(user_id, "Видео")
    elif msg.audio:
        text += f"\n\n🎵 <b>Аудио</b>\n<code>file_id</code>: <code>{msg.audio.file_id}</code>"
        update_stats(user_id, "Аудио")
    elif msg.voice:
        text += f"\n\n🎤 <b>Голосовое</b>\n<code>file_id</code>: <code>{msg.voice.file_id}</code>"
        update_stats(user_id, "Голосовое")
    elif msg.document:
        text += f"\n\n📄 <b>Документ</b>\n<code>file_id</code>: <code>{msg.document.file_id}</code>"
        update_stats(user_id, "Документ")
    else:
        return
    await update.message.reply_html(text)

# ================== КОМАНДА /id ==================
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    update_stats(user_id, "/id")
    add_history(user_id, "Чат", chat_id, "текущий чат")
    await update.message.reply_html(f"🆔 ID этого чата: <code>{chat_id}</code>")

# ================== СТАТИСТИКА / ИСТОРИЯ ==================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_stats_text(query.from_user.id)
    await safe_edit_or_send(query.message, text, reply_markup=back_button())

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = get_history_text(query.from_user.id)
    await safe_edit_or_send(query.message, text, reply_markup=back_button())

# ================== КАНАЛ И ПОМОЩЬ ==================
async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await safe_edit_or_send(query.message, f"📢 <b>Наш канал:</b> {CHANNEL_LINK}", reply_markup=back_button())

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "<b>❓ Помощь</b>\n\n"
        "1. Нажми «Узнать айди» → выбери тип.\n"
        "2. Перешли сообщение от нужного объекта.\n"
        "3. Получи ID.\n\n"
        "• Отправь стикер – покажу file_id.\n"
        "• Отправь фото/видео – покажу file_id.\n"
        "• /id – ID текущего чата.\n\n"
        f"📢 Канал: {CHANNEL_LINK}"
    )
    await safe_edit_or_send(query.message, text, reply_markup=back_button())

# ================== ВЕБ-СЕРВЕР ДЛЯ RENDER (ЗЕЛЁНЫЙ КРУЖОК) ==================
async def health(request):
    return web.Response(text="OK")

async def start_web():
    app_web = web.Application()
    app_web.router.add_get('/health', health)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"✅ Веб-сервер на порту {port}")
    while True:
        await asyncio.sleep(3600)

# ================== ЗАПУСК ==================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(get_id_menu, pattern="^get_id_menu$"))
    app.add_handler(CallbackQueryHandler(id_user, pattern="^id_user$"))
    app.add_handler(CallbackQueryHandler(id_bot, pattern="^id_bot$"))
    app.add_handler(CallbackQueryHandler(id_channel, pattern="^id_channel$"))
    app.add_handler(CallbackQueryHandler(id_sticker, pattern="^id_sticker$"))
    app.add_handler(CallbackQueryHandler(get_chat_id, pattern="^get_chat_id$"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="^show_stats$"))
    app.add_handler(CallbackQueryHandler(show_history, pattern="^show_history$"))
    app.add_handler(CallbackQueryHandler(channel_info, pattern="^channel_info$"))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.Document.ALL, handle_media))
    logger.info("🚀 Fant ID бот запущен (исправлена ошибка forward_origin)")
    loop = asyncio.get_event_loop()
    loop.create_task(start_web())
    app.run_polling()

if __name__ == "__main__":
    main()
