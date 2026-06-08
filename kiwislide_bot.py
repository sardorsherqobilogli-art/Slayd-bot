#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deutsch Booster - Telegram Bot
python-telegram-bot v20+
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

# ==================== KONFIGURATSIYA ====================
TOKEN = "SIZNING_BOT_TOKENINGIZ"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== STATES ====================
(
    MAIN_MENU,
    LEVEL_SELECT,
    A1_MENU, A2_MENU, B1_MENU, B2_MENU, C1_MENU,
    BOOK_MENU,
    LEKTION_PAGE,
    TRANSLATOR,
) = range(10)

# ==================== CALLBACKS ====================
class CB:
    MAIN_MENU     = "main_menu"
    LEVEL_SELECT  = "level_select"
    LEVEL_A1      = "level_a1"
    LEVEL_A2      = "level_a2"
    LEVEL_B1      = "level_b1"
    LEVEL_B2      = "level_b2"
    LEVEL_C1      = "level_c1"
    B1_PREP       = "b1_prep"
    B2_PREP       = "b2_prep"
    C1_PREP       = "c1_prep"
    TRANSLATOR    = "translator"
    UZB_DEU       = "uzb_deu"
    DEU_UZB       = "deu_uzb"
    HELP          = "help"


# ==================== LEKTION RANGE CONFIG ====================
# format: (kitob_nomi, daraja, boshlang'ich_lektion, oxirgi_lektion)
BOOK_LEKTIONS = {
    "a1_motive":   (1, 8),
    "a1_schritte": (1, 14),
    "a1_menschen": (1, 24),

    "a2_motive":   (9, 18),
    "a2_schritte": (1, 14),
    "a2_menschen": (1, 24),

    "b1_motive":   (19, 30),
    "b1_schritte": (1, 14),
    "b1_menschen": (1, 24),

    "b2_sicher":      (1, 12),
    "b2_kompassdaf":  (1, 10),
    "b2_aspekte":     (1, 10),

    "c1_sicher":      (1, 12),
    "c1_kompassdaf":  (1, 10),
    "c1_aspekte":     (1, 10),
}

BOOK_LABELS = {
    "motive":    "📗 MOTIVE",
    "schritte":  "📙 SCHRITTE",
    "menschen":  "📕 MENSCHEN",
    "sicher":    "📗 Sicher",
    "kompassdaf":"📙 KompassDaF",
    "aspekte":   "📕 Aspekte",
}

LEVEL_BOOKS = {
    "a1": ["motive", "schritte", "menschen"],
    "a2": ["motive", "schritte", "menschen"],
    "b1": ["motive", "schritte", "menschen"],
    "b2": ["sicher", "kompassdaf", "aspekte"],
    "c1": ["sicher", "kompassdaf", "aspekte"],
}

LEVEL_LABELS = {
    "a1": "🟢 A1 \\- Beginner",
    "a2": "🟢 A2 \\- Elementary",
    "b1": "🟡 B1 \\- Intermediate",
    "b2": "🟡 B2 \\- Upper\\-Intermediate",
    "c1": "🔴 C1 \\- Advanced",
}


# ==================== KEYBOARD HELPERS ====================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Daraja tanlash", callback_data=CB.LEVEL_SELECT)],
        [
            InlineKeyboardButton("📗 B1 Vorbereitung", callback_data=CB.B1_PREP),
            InlineKeyboardButton("📙 B2 Vorbereitung", callback_data=CB.B2_PREP),
        ],
        [
            InlineKeyboardButton("📕 C1 Vorbereitung", callback_data=CB.C1_PREP),
            InlineKeyboardButton("🌐 Tarjimon",         callback_data=CB.TRANSLATOR),
        ],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data=CB.HELP)],
    ])


def level_select_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1 - Beginner",        callback_data=CB.LEVEL_A1),
            InlineKeyboardButton("🟢 A2 - Elementary",      callback_data=CB.LEVEL_A2),
        ],
        [
            InlineKeyboardButton("🟡 B1 - Intermediate",    callback_data=CB.LEVEL_B1),
            InlineKeyboardButton("🟡 B2 - Upper-Interm.",   callback_data=CB.LEVEL_B2),
        ],
        [InlineKeyboardButton("🔴 C1 - Advanced",           callback_data=CB.LEVEL_C1)],
        [InlineKeyboardButton("🏠 Asosiy menu",             callback_data=CB.MAIN_MENU)],
    ])


def books_keyboard(level: str):
    """Daraja bo'yicha kitob tugmalari"""
    books = LEVEL_BOOKS[level]
    rows = []
    for book in books:
        rows.append([InlineKeyboardButton(
            BOOK_LABELS[book],
            callback_data=f"book_{level}_{book}"
        )])
    rows.append([InlineKeyboardButton("↩️ Darajaga qaytish", callback_data=CB.LEVEL_SELECT)])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu",      callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def lektions_keyboard(level: str, book: str):
    """Lektion raqamlari tugmalari — 2 ustunli"""
    key = f"{level}_{book}"
    start, end = BOOK_LEKTIONS[key]
    nums = list(range(start, end + 1))

    rows = []
    # 2 ta qator bo'yicha joylash
    for i in range(0, len(nums), 2):
        pair = nums[i:i+2]
        row = [
            InlineKeyboardButton(
                f"Lektion {n}",
                callback_data=f"lekt_{level}_{book}_{n}"
            )
            for n in pair
        ]
        rows.append(row)

    rows.append([InlineKeyboardButton(
        "↩️ Kitobga qaytish",
        callback_data=f"back_book_{level}"
    )])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def back_to_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)]
    ])


def translator_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 UZB ➡️ 🇩🇪 DEU", callback_data=CB.UZB_DEU),
            InlineKeyboardButton("🇩🇪 DEU ➡️ 🇺🇿 UZB", callback_data=CB.DEU_UZB),
        ],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])


# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "👋 *Deutsch Booster* ga xush kelibsiz\\!\n\n"
        "🇩🇪 Nemis tilini A1 dan C1 gacha o'rganing\\.\n"
        "📚 Bo'limni tanlang:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="MarkdownV2",
                                        reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2",
                                                      reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 *Asosiy Menu*\n\nBo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def level_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📚 *Daraja tanlash*\n\nO'z darajangizni tanlang:\n"
        "🟢 A1\\-A2: Boshlang'ich\n"
        "🟡 B1\\-B2: O'rta\n"
        "🔴 C1: Yuqori",
        parse_mode="MarkdownV2",
        reply_markup=level_select_keyboard(),
    )
    return LEVEL_SELECT


async def _show_books(query, level: str) -> int:
    """Daraja tanlanganda kitoblarni ko'rsatish"""
    label = LEVEL_LABELS[level]
    await query.edit_message_text(
        f"{label}\n\nO'qimoqchi bo'lgan kitobni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=books_keyboard(level),
    )
    state_map = {"a1": A1_MENU, "a2": A2_MENU, "b1": B1_MENU, "b2": B2_MENU, "c1": C1_MENU}
    return state_map[level]


async def level_a1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "a1")

async def level_a2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "a2")

async def level_b1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b1")

async def level_b2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b2")

async def level_c1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "c1")

# Asosiy menyudan B1/B2/C1 prep tugmalari
async def b1_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b1")

async def b2_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b2")

async def c1_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "c1")


async def book_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """book_{level}_{book} callback"""
    query = update.callback_query
    await query.answer()
    _, level, book = query.data.split("_", 2)

    key = f"{level}_{book}"
    start, end = BOOK_LEKTIONS[key]
    label = BOOK_LABELS[book]
    level_label = LEVEL_LABELS[level]

    await query.edit_message_text(
        f"{level_label} \\| {label}\n\nLektion tanlang \\({start}\\-{end}\\):",
        parse_mode="MarkdownV2",
        reply_markup=lektions_keyboard(level, book),
    )
    return BOOK_MENU


async def back_book_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """back_book_{level} — kitoblar ro'yxatiga qaytish"""
    query = update.callback_query
    await query.answer()
    # callback: back_book_a1, back_book_b2 etc
    level = query.data.split("_")[-1]
    return await _show_books(query, level)


async def lektion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """lekt_{level}_{book}_{n} callback"""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    # lekt_a1_motive_3  →  parts = ['lekt','a1','motive','3']
    # lekt_b2_kompassdaf_5 → ['lekt','b2','kompassdaf','5']
    level = parts[1]
    n     = parts[-1]
    book  = "_".join(parts[2:-1])   # kompassdaf yoki motive etc

    label       = BOOK_LABELS[book]
    level_label = LEVEL_LABELS[level]

    text = (
        f"{level_label} \\| {label}\n"
        f"📖 *Lektion {n}*\n\n"
        "Bu lektion materiallari tez orada qo'shiladi\\!\n\n"
        "📥 Yuklab olish: \\[Havola\\]\n"
        "📝 Mashqlar: Tez orada"
    )
    # Kitobga qaytish tugmasi
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "↩️ Kitobga qaytish",
            callback_data=f"back_book_{level}"
        )],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return BOOK_MENU


# ==================== TARJIMON ====================

async def translator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌐 *Tarjimon*\n\nQaysi yo'nalishda tarjima qilmoqchisiz?",
        parse_mode="MarkdownV2",
        reply_markup=translator_keyboard(),
    )
    return TRANSLATOR

async def uzb_deu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🇺🇿➡️🇩🇪 *O'zbekcha → Nemischa*\n\nTarjima qilmoqchi bo'lgan so'zni yuboring:",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return MAIN_MENU

async def deu_uzb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🇩🇪➡️🇺🇿 *Nemischa → O'zbekcha*\n\nTarjima qilmoqchi bo'lgan so'zni yuboring:",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return MAIN_MENU


# ==================== YORDAM ====================

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "ℹ️ *Yordam*\n\n"
        "/start \\— Botni ishga tushirish\n"
        "/menu \\— Asosiy menyu\n\n"
        "📚 *Darajalar:* A1, A2, B1, B2, C1\n"
        "📗 A1/A2/B1 \\— Motive, Schritte, Menschen\n"
        "📙 B2/C1 \\— Sicher, KompassDaF, Aspekte\n"
        "🌐 Tarjimon \\— UZB↔DEU",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return MAIN_MENU

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🏠 *Asosiy Menu*\n\nBo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n/start \\— Boshlash\n/menu \\— Menyu",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )


# ==================== MAIN ====================

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Shared handlers — barcha state larda ishlaydi
    common_handlers = [
        CallbackQueryHandler(main_menu_handler,   pattern=f"^{CB.MAIN_MENU}$"),
        CallbackQueryHandler(level_select_handler, pattern=f"^{CB.LEVEL_SELECT}$"),
        CallbackQueryHandler(level_a1_handler,    pattern=f"^{CB.LEVEL_A1}$"),
        CallbackQueryHandler(level_a2_handler,    pattern=f"^{CB.LEVEL_A2}$"),
        CallbackQueryHandler(level_b1_handler,    pattern=f"^{CB.LEVEL_B1}$"),
        CallbackQueryHandler(level_b2_handler,    pattern=f"^{CB.LEVEL_B2}$"),
        CallbackQueryHandler(level_c1_handler,    pattern=f"^{CB.LEVEL_C1}$"),
        CallbackQueryHandler(b1_prep_handler,     pattern=f"^{CB.B1_PREP}$"),
        CallbackQueryHandler(b2_prep_handler,     pattern=f"^{CB.B2_PREP}$"),
        CallbackQueryHandler(c1_prep_handler,     pattern=f"^{CB.C1_PREP}$"),
        CallbackQueryHandler(translator_handler,  pattern=f"^{CB.TRANSLATOR}$"),
        CallbackQueryHandler(uzb_deu_handler,     pattern=f"^{CB.UZB_DEU}$"),
        CallbackQueryHandler(deu_uzb_handler,     pattern=f"^{CB.DEU_UZB}$"),
        CallbackQueryHandler(help_handler,        pattern=f"^{CB.HELP}$"),
        # Kitob tanlash: book_a1_motive, book_b2_sicher, etc.
        CallbackQueryHandler(book_select_handler, pattern=r"^book_(a1|a2|b1|b2|c1)_\w+$"),
        # Kitobga qaytish: back_book_a1, etc.
        CallbackQueryHandler(back_book_handler,   pattern=r"^back_book_(a1|a2|b1|b2|c1)$"),
        # Lektion: lekt_a1_motive_3, lekt_b2_kompassdaf_5, etc.
        CallbackQueryHandler(lektion_handler,     pattern=r"^lekt_(a1|a2|b1|b2|c1)_\w+_\d+$"),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU:    common_handlers,
            LEVEL_SELECT: common_handlers,
            A1_MENU:      common_handlers,
            A2_MENU:      common_handlers,
            B1_MENU:      common_handlers,
            B2_MENU:      common_handlers,
            C1_MENU:      common_handlers,
            BOOK_MENU:    common_handlers,
            TRANSLATOR:   common_handlers,
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu",  menu_command),
            CommandHandler("help",  help_command),
        ],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))

    print("🤖 Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
