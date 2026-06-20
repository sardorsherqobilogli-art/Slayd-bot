#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  DEUTSCH MEISTER PRO - Mukammal Nemis Tili Telegram Bot
  YANGILANGAN VERSION - Sardor tomonidan
============================================================
"""

import os
import random
import datetime
import logging

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, InputFile,
    WebAppInfo, MenuButtonWebApp,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ==================== MODULLAR ====================
from config import (
    logger, TOKEN, GROQ_API_KEY,
    BOOK_LABELS, LEVEL_LABELS, LEVEL_BOOKS, BOOK_LEKTIONS, XP_REWARDS,
)
from database import get_db
from voice_engine import speak_text, listen_to_voice

# AI Mentor moduli
from ai_mentor import (
    AI_MENTOR_MENU,
    ai_mentor_menu_handler,
    level_detect_start, level_detect_process, ld_show_section, ld_speak_handler,
    vorstellen_menu, vorstellen_rules, vorstellen_templates, vorstellen_template_show,
    vorstellen_start_new, vorstellen_process_new,
    vs_show_section_new, vs_improve_menu, vs_improve_show, vs_speak_new, vorstellen_pdf_new,
    erfahrungen_menu, erfahrungen_topic, erfahrungen_start_chat, erfahrungen_chat, erfahrungen_result,
    mistake_bank_menu, mistake_list, mistake_mini_lesson, mistake_speak_handler,
    mistake_improve_handler, mistake_practice, mistake_practice_process, mistake_master, mistake_random,
    voice_vocab_menu, voice_vocab_level_select, voice_vocab_topic_select,
    vocab_test_start, vocab_test_process, vocab_sprechen, vocab_speak_story,
    vocab_sprechen_ready, vocab_sprechen_process, vocab_roleplay_from_vocab,
    roleplay_menu, roleplay_level_select, roleplay_topic_select,
    roleplay_start_dialog, roleplay_chat, roleplay_result,
    VORSTELLEN_START, VORSTELLEN_RESULT, VORSTELLEN_IMPROVE,
    LEVEL_DETECT_Q1, LEVEL_DETECT_Q2, LEVEL_DETECT_Q3, LEVEL_DETECT_Q4, LEVEL_DETECT_Q5,
    ERFAHRUNGEN_MENU, ERFAHRUNGEN_DIFFICULTY, ERFAHRUNGEN_CHAT,
    MISTAKE_BANK_MENU, MISTAKE_MINILESSON, MISTAKE_PRACTICE,
    VOICE_VOCAB_LEVEL, VOICE_VOCAB_TOPIC, VOICE_VOCAB_WORDS, VOICE_VOCAB_TEST, VOICE_VOCAB_SPRECHEN,
    ROLEPLAY_LEVEL, ROLEPLAY_TOPIC, ROLEPLAY_RULES, ROLEPLAY_CHAT,
)

# Progress moduli
from progress import (
    progress_menu, progress_charts, progress_missions, progress_levelup,
)

# Settings moduli
from settings import (
    settings_menu, settings_level, settings_set_level,
    settings_voice, settings_set_voice,
    settings_speed, settings_set_speed, settings_mistakes,
)


# ==================== PASTKI DOIMIY MENYU ====================
REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📚 Menyu", "📖 Kunlik so'z"],
        ["🤖 AI Mentor", "📊 Progressim"],
        ["🌐 Tarjimon", "ℹ️ Yordam"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


# ==================== STATES ====================
(
    MAIN_MENU,
    LEVEL_SELECT,
    A1_MENU, A2_MENU, B1_MENU, B2_MENU, C1_MENU,
    BOOK_MENU,
    LEKTION_PAGE,
    TRANSLATOR,
    QUIZ_STATE,
    POMODORO_STATE,
    UZB_DEU_INPUT,
    DEU_UZB_INPUT,
    # Yangi: Lug'at
    LUGAT_MENU,
    LUGAT_LEVEL_SELECT,
    LUGAT_BOOK_SELECT,
    LUGAT_CHAPTER_SELECT,
    # Yangi: Sayfa
    SAYFA_MENU,
    SAYFA_BOOK_SELECT,
    SAYFA_AUDIO_SELECT,
    # Yangi: Kitob Materiallar
    KITOB_MENU,
    KITOB_LEVEL_SELECT,
    KITOB_BOOK_SELECT,
    KITOB_MATERIAL_VIEW,
    # Onboarding
    REG_PHONE,
    REG_CHANNEL,
    # Admin
    ADMIN_STATE,
) = range(28)

# ==================== ADMIN CONFIG ====================
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x.strip()]


# ==================== ASOSIY MENYU (📚 Menyu) ====================

def main_menu_keyboard():
    """Asosiy menyu tugmalari"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI Mentor", callback_data="menu_ai_mentor")],
        [InlineKeyboardButton("📖 Lug'at", callback_data="menu_lugat")],
        [InlineKeyboardButton("🌐 Tarjimon", callback_data="menu_tarjimon")],
        [InlineKeyboardButton("📚 Sayfa", callback_data="menu_sayfa")],
        [InlineKeyboardButton("📚 Kitob Materiallar", callback_data="menu_kitob")],
        [InlineKeyboardButton("📖 Kunlik so'z", callback_data="menu_kunlik")],
        [InlineKeyboardButton("📊 Progressim", callback_data="menu_progress")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="menu_settings")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start komandasi"""
    user = update.effective_user
    db = get_db()
    db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)

    text = (
        f"🇩🇪 *Deutsch Meister PRO*\n\n"
        f"Salom, {esc_md(user.first_name)}\! 👋\n\n"
        f"Bu bot nemis tilini o'rganish uchun yaratilgan\:\n\n"
        f"🤖 *AI Mentor* \- Shaxsiy yordamchi\n"
        f"📖 *Lug'at* \- Darajaga qarab so'zlar\n"
        f"🌐 *Tarjimon* \- UZB \<\-\> DEU\n"
        f"📚 *Sayfa* \- Kitob va audio\n"
        f"📚 *Kitob Materiallar* \- PDF, audio, video\n"
        f"📖 *Kunlik so'z* \- Har kuni yangi so'z\n\n"
        f"*Quyidagilardan birini tanlang\:*"
    )

    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asosiy menyu handler"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_ai_mentor" or data == "ai_mentor_menu":
        return await ai_mentor_menu_handler(update, context)

    elif data == "menu_lugat":
        return await lugat_menu(update, context)

    elif data == "menu_tarjimon":
        return await tarjimon_menu(update, context)

    elif data == "menu_sayfa":
        return await sayfa_menu(update, context)

    elif data == "menu_kitob":
        return await kitob_menu(update, context)

    elif data == "menu_kunlik":
        return await daily_word_handler(update, context)

    elif data == "menu_progress":
        return await progress_menu(update, context)

    elif data == "menu_settings":
        return await settings_menu(update, context)

    elif data == "main_menu":
        await query.edit_message_text(
            "🇩🇪 *Deutsch Meister PRO*\n\n*Asosiy menyu\:*",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    return MAIN_MENU


# ==================== 1. AI MENTOR (Hozirgi ai_mentor_work.py dan) ====================

# AI Mentor handlerlari ai_mentor_work.py dan import qilingan
# ConversationHandler orqali ulash kerak


# ==================== 2. LUG'AT ====================

# Lug'at ma'lumotlari - ADMIN tomonidan yuklanadi
# Bu yerda faqat struktura, ma'lumotlar DB dan olinadi

LUGAT_LEVELS = {
    "a1": "🟢 A1 - Beginner",
    "a2": "🟢 A2 - Elementary", 
    "b1": "🟡 B1 - Intermediate",
    "b2": "🟡 B2 - Upper-Intermediate",
    "c1": "🔵 C1 - Advanced",
}


def lugat_level_keyboard():
    """Lug'at daraja tanlash tugmalari"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1", callback_data="lugat_level_a1"),
            InlineKeyboardButton("🟢 A2", callback_data="lugat_level_a2"),
        ],
        [
            InlineKeyboardButton("🟡 B1", callback_data="lugat_level_b1"),
            InlineKeyboardButton("🟡 B2", callback_data="lugat_level_b2"),
        ],
        [
            InlineKeyboardButton("🔵 C1", callback_data="lugat_level_c1"),
        ],
        [InlineKeyboardButton("↩️ Asosiy menyu", callback_data="main_menu")],
    ])


async def lugat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at menyu - daraja tanlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📖 *Lug'at*\n\n"
        "Darajangizni tanlang\:\n\n"
        "🟢 *A1* \- Boshlang'ich\n"
        "🟢 *A2* \- Elementar\n"
        "🟡 *B1* \- O'rta\n"
        "🟡 *B2* \- Yuqori o'rta\n"
        "🔵 *C1* \- Yuqori\n\n"
        "*Har bir darajada o'z bo'limlari mavjud\.*",
        parse_mode="MarkdownV2",
        reply_markup=lugat_level_keyboard(),
    )
    return LUGAT_MENU


async def lugat_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja tanlandi - kitoblar/bo'limlar ro'yxati"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("lugat_level_", "")
    context.user_data["lugat_level"] = level

    # DB dan bu darajadagi kitoblar/bo'limlarni olish
    db = get_db()
    books = db.get_lugat_books(level)

    if not books:
        await query.edit_message_text(
            f"📖 *{LUGAT_LEVELS.get(level, level.upper())}*\n\n"
            f"⚠️ Bu darajada hali lug'atlar mavjud emas\!\n\n"
            f"Admin tomonidan qo'shiladi\.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Lug'atga qaytish", callback_data="menu_lugat")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return LUGAT_MENU

    # Kitoblar tugmalari
    keyboard_rows = []
    for book in books:
        keyboard_rows.append([
            InlineKeyboardButton(
                f"📗 {esc_md(book['name'])}",
                callback_data=f"lugat_book_{book['id']}"
            )
        ])

    keyboard_rows.append([InlineKeyboardButton("↩️ Darajalar", callback_data="menu_lugat")])
    keyboard_rows.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")])

    await query.edit_message_text(
        f"📖 *{LUGAT_LEVELS.get(level, level.upper())}*\n\n"
        f"Kitob/bo'limni tanlang\:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return LUGAT_BOOK_SELECT


async def lugat_book_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kitob tanlandi - bo'limlar/boblar ro'yxati"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.replace("lugat_book_", ""))
    context.user_data["lugat_book_id"] = book_id

    db = get_db()
    chapters = db.get_lugat_chapters(book_id)
    book = db.get_lugat_book_by_id(book_id)

    if not chapters:
        await query.edit_message_text(
            f"📖 *{esc_md(book.get('name', 'Kitob'))}*\n\n"
            f"⚠️ Bu kitobda hali bo'limlar mavjud emas\!",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Kitoblar", callback_data=f"lugat_level_{context.user_data.get('lugat_level', 'a1')}")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return LUGAT_BOOK_SELECT

    keyboard_rows = []
    for ch in chapters:
        keyboard_rows.append([
            InlineKeyboardButton(
                f"📄 {esc_md(ch['name'])}",
                callback_data=f"lugat_chapter_{ch['id']}"
            )
        ])

    keyboard_rows.append([InlineKeyboardButton("↩️ Kitoblar", callback_data=f"lugat_level_{context.user_data.get('lugat_level', 'a1')}")])
    keyboard_rows.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")])

    await query.edit_message_text(
        f"📖 *{esc_md(book.get('name', 'Kitob'))}*\n\n"
        f"Bo'limni tanlang\:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return LUGAT_CHAPTER_SELECT


async def lugat_chapter_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bo'lim ochildi - lug'at so'zlari ko'rsatiladi"""
    query = update.callback_query
    await query.answer()

    chapter_id = int(query.data.replace("lugat_chapter_", ""))
    context.user_data["lugat_chapter_id"] = chapter_id

    db = get_db()
    words = db.get_lugat_words(chapter_id)
    chapter = db.get_lugat_chapter_by_id(chapter_id)

    if not words:
        await query.edit_message_text(
            f"📖 *{esc_md(chapter.get('name', 'Bo\'lim'))}*\n\n"
            f"⚠️ Bu bo'limda hali so'zlar mavjud emas\!",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Bo'limlar", callback_data=f"lugat_book_{context.user_data.get('lugat_book_id', 1)}")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return LUGAT_CHAPTER_SELECT

    # So'zlarni ko'rsatish (25 ta gacha)
    text = f"📖 *{esc_md(chapter.get('name', 'Bo\'lim'))}*\n\n"
    for i, w in enumerate(words[:25], 1):
        de = w.get('german', '')
        uz = w.get('uzbek', '')
        izoh = w.get('izoh', '')
        text += f"*{i}\.* {esc_md(de)} \- {esc_md(uz)}\n"
        if izoh:
            text += f"   📝 _{esc_md(izoh)}_\n"
        text += "\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="lugat_speak")],
        [InlineKeyboardButton("✏️ Test qilish", callback_data="lugat_test")],
        [InlineKeyboardButton("↩️ Bo'limlar", callback_data=f"lugat_book_{context.user_data.get('lugat_book_id', 1)}")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    # Agar matn juda uzun bo'lsa, bo'laklash
    if len(text) > 4000:
        parts = []
        current = ""
        for line in text.split("\n"):
            if len(current) + len(line) > 3800:
                parts.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            parts.append(current)

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                await query.message.reply_text(part, parse_mode="MarkdownV2", reply_markup=keyboard)
            else:
                await query.message.reply_text(part, parse_mode="MarkdownV2")
    else:
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return LUGAT_CHAPTER_SELECT


# ==================== 3. TARJIMON ====================

async def tarjimon_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tarjimon menyu"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🌐 *Tarjimon*\n\n"
        "Qaysi yo'nalishda tarjima qilmoqchisiz\?\n\n"
        "🇺🇿 *UZB* \-\> 🇩🇪 *DEU* \- O'zbekchadan nemischaga\n"
        "🇩🇪 *DEU* \-\> 🇺🇿 *UZB* \- Nemisdan o'zbekchaga\n\n"
        "*AI sifatli tarjima qiladi va tushuntirish beradi\.*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🇺🇿 UZB → 🇩🇪 DEU", callback_data="tarjima_uzb_deu")],
            [InlineKeyboardButton("🇩🇪 DEU → 🇺🇿 UZB", callback_data="tarjima_deu_uzb")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    return TRANSLATOR


async def tarjima_uzb_deu_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """UZB -> DEU tarjima boshlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🇺🇿 *UZB* \-\> 🇩🇪 *DEU*\n\n"
        "O'zbekcha matnni yuboring\:\n\n"
        "_AI tarjima qiladi, grammatika tushuntirish beradi\_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Tarjimon", callback_data="menu_tarjimon")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    context.user_data["translator_direction"] = "uzb_deu"
    return UZB_DEU_INPUT


async def tarjima_deu_uzb_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """DEU -> UZB tarjima boshlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🇩🇪 *DEU* \-\> 🇺🇿 *UZB*\n\n"
        "Nemischa matnni yuboring\:\n\n"
        "_AI tarjima qiladi va tushuntirish beradi\_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Tarjimon", callback_data="menu_tarjimon")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    context.user_data["translator_direction"] = "deu_uzb"
    return DEU_UZB_INPUT


async def translator_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tarjima qilish - AI orqali"""
    direction = context.user_data.get("translator_direction", "uzb_deu")
    user_text = update.message.text.strip()

    if not user_text:
        await update.message.reply_text("❌ Matn bo'sh. Qayta yuboring.")
        return UZB_DEU_INPUT if direction == "uzb_deu" else DEU_UZB_INPUT

    loading = await update.message.reply_text("🔄 *Tarjima qilinmoqda...*", parse_mode="MarkdownV2")

    # AI tarjima
    from ai_mentor_work import groq_json

    if direction == "uzb_deu":
        system_msg = (
            "Siz professional nemis tili tarjimonsiz. "
            "O'zbek tilidan nemis tiliga tarjima qiling. "
            "JSON formatida: {\"tarjima\": \"nemischa matn\", \"tushuntirish\": \"grammatik tushuntirish o'zbek tilida\", \"maslahat\": \"qo'llash maslahati\"}"
        )
    else:
        system_msg = (
            "Siz professional nemis tili tarjimonsiz. "
            "Nemis tilidan o'zbek tiliga tarjima qiling. "
            "JSON formatida: {\"tarjima\": \"o'zbekcha matn\", \"tushuntirish\": \"grammatik tushuntirish o'zbek tilida\", \"maslahat\": \"qo'llash maslahati\"}"
        )

    result = await groq_json([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_text},
    ], max_tokens=1024)

    await loading.delete()

    tarjima = result.get("tarjima", "Tarjima qilinmadi")
    tushuntirish = result.get("tushuntirish", "")
    maslahat = result.get("maslahat", "")

    text = (
        f"🌐 *Tarjima natijasi*\n\n"
        f"🇺🇿 *Asl matn:*\n`{esc_md(user_text[:200])}`\n\n"
        f"🇩🇪 *Tarjima:*\n`{esc_md(tarjima[:500])}`\n\n"
    )
    if tushuntirish:
        text += f"📝 *Tushuntirish:*\n{esc_md(tushuntirish[:300])}\n\n"
    if maslahat:
        text += f"💡 *Maslahat:*\n{esc_md(maslahat[:200])}"

    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="translator_speak")],
            [InlineKeyboardButton("🔄 Boshqa tarjima", callback_data=f"tarjima_{direction}")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )

    # Ovoz uchun saqlash
    context.user_data["translator_text"] = tarjima
    return UZB_DEU_INPUT if direction == "uzb_deu" else DEU_UZB_INPUT


async def translator_speak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tarjima ovozda"""
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")

    text = context.user_data.get("translator_text", "")
    if text:
        await speak_text(query, text, voice="female", speed=0.9)

    return UZB_DEU_INPUT


# ==================== 4. SAYFA ====================

async def sayfa_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sayfa menyu"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📚 *Sayfa*\n\n"
        "Kitob va audio materiallar\n\n"
        "*Mavjud kitoblar\:*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📗 B1 Sayfa", callback_data="sayfa_b1")],
            [InlineKeyboardButton("📙 B2 Sayfa", callback_data="sayfa_b2")],
            [InlineKeyboardButton("📕 C1 Sayfa", callback_data="sayfa_c1")],
            [InlineKeyboardButton("↩️ Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    return SAYFA_MENU


async def sayfa_book_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sayfa kitobi tanlandi - bo'limlar"""
    query = update.callback_query
    await query.answer()

    book_key = query.data.replace("sayfa_", "")
    context.user_data["sayfa_book"] = book_key

    db = get_db()
    materials = db.get_sayfa_materials(book_key)

    if not materials:
        await query.edit_message_text(
            f"📚 *Sayfa {book_key.upper()}*\n\n"
            f"⚠️ Hali materiallar mavjud emas\!\n\n"
            f"Admin tomonidan qo'shiladi\.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Sayfa", callback_data="menu_sayfa")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return SAYFA_MENU

    keyboard_rows = []
    for mat in materials:
        has_audio = "🎵" if mat.get('audio_path') else ""
        has_pdf = "📄" if mat.get('pdf_path') else ""
        keyboard_rows.append([
            InlineKeyboardButton(
                f"{has_pdf}{has_audio} {esc_md(mat['name'])}",
                callback_data=f"sayfa_mat_{mat['id']}"
            )
        ])

    keyboard_rows.append([InlineKeyboardButton("↩️ Sayfa", callback_data="menu_sayfa")])
    keyboard_rows.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")])

    await query.edit_message_text(
        f"📚 *Sayfa {book_key.upper()}*\n\n"
        f"Bo'limni tanlang\:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return SAYFA_BOOK_SELECT


async def sayfa_material_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Material ko'rish - PDF + Audio"""
    query = update.callback_query
    await query.answer()

    mat_id = int(query.data.replace("sayfa_mat_", ""))
    db = get_db()
    mat = db.get_sayfa_material_by_id(mat_id)

    if not mat:
        await query.edit_message_text("❌ Material topilmadi.")
        return SAYFA_BOOK_SELECT

    text = (
        f"📚 *{esc_md(mat.get('name', 'Material'))}*\n\n"
        f"{esc_md(mat.get('description', ''))}\n\n"
    )

    keyboard = []
    if mat.get('pdf_path'):
        keyboard.append([InlineKeyboardButton("📄 PDF ko'rish", callback_data=f"sayfa_pdf_{mat_id}")])
    if mat.get('audio_path'):
        keyboard.append([InlineKeyboardButton("🎵 Audio eshitish", callback_data=f"sayfa_audio_{mat_id}")])
    keyboard.append([InlineKeyboardButton("↩️ Bo'limlar", callback_data=f"sayfa_{context.user_data.get('sayfa_book', 'b1')}")])
    keyboard.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")])

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SAYFA_AUDIO_SELECT


async def sayfa_send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """PDF faylni yuborish"""
    query = update.callback_query
    await query.answer()

    mat_id = int(query.data.replace("sayfa_pdf_", ""))
    db = get_db()
    mat = db.get_sayfa_material_by_id(mat_id)

    if mat and mat.get('pdf_path') and os.path.exists(mat['pdf_path']):
        await query.message.reply_document(
            document=open(mat['pdf_path'], 'rb'),
            caption=f"📄 {esc_md(mat.get('name', 'PDF'))}",
            parse_mode="MarkdownV2",
        )
    else:
        await query.edit_message_text("❌ PDF fayl topilmadi.")

    return SAYFA_AUDIO_SELECT


async def sayfa_send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Audio faylni yuborish"""
    query = update.callback_query
    await query.answer()

    mat_id = int(query.data.replace("sayfa_audio_", ""))
    db = get_db()
    mat = db.get_sayfa_material_by_id(mat_id)

    if mat and mat.get('audio_path') and os.path.exists(mat['audio_path']):
        await query.message.reply_audio(
            audio=open(mat['audio_path'], 'rb'),
            caption=f"🎵 {esc_md(mat.get('name', 'Audio'))}",
            parse_mode="MarkdownV2",
        )
    else:
        await query.edit_message_text("❌ Audio fayl topilmadi.")

    return SAYFA_AUDIO_SELECT


# ==================== 5. KITOB MATERIALLAR ====================

KITOB_LEVELS = {
    "a1": "🟢 A1",
    "a2": "🟢 A2",
    "b1": "🟡 B1",
    "b2": "🟡 B2",
    "c1": "🔵 C1",
    "c2": "🔴 C2",
}


def kitob_level_keyboard():
    """Kitob daraja tanlash tugmalari"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1", callback_data="kitob_level_a1"),
            InlineKeyboardButton("🟢 A2", callback_data="kitob_level_a2"),
        ],
        [
            InlineKeyboardButton("🟡 B1", callback_data="kitob_level_b1"),
            InlineKeyboardButton("🟡 B2", callback_data="kitob_level_b2"),
        ],
        [
            InlineKeyboardButton("🔵 C1", callback_data="kitob_level_c1"),
            InlineKeyboardButton("🔴 C2", callback_data="kitob_level_c2"),
        ],
        [InlineKeyboardButton("↩️ Asosiy menyu", callback_data="main_menu")],
    ])


async def kitob_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kitob materiallar menyu"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📚 *Kitob Materiallar*\n\n"
        "Darajangizni tanlang\:\n\n"
        "🟢 *A1* \| *A2* \- Boshlang'ich\n"
        "🟡 *B1* \| *B2* \- O'rta\n"
        "🔵 *C1* \- Yuqori\n"
        "🔴 *C2* \- Mukammal\n\n"
        "*Har bir darajada kitoblar, PDF, audio va videolar\.*",
        parse_mode="MarkdownV2",
        reply_markup=kitob_level_keyboard(),
    )
    return KITOB_MENU


async def kitob_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja tanlandi - kitoblar ro'yxati"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("kitob_level_", "")
    context.user_data["kitob_level"] = level

    db = get_db()
    books = db.get_kitob_books(level)

    if not books:
        await query.edit_message_text(
            f"📚 *{KITOB_LEVELS.get(level, level.upper())}*\n\n"
            f"⚠️ Bu darajada hali kitoblar mavjud emas\!\n\n"
            f"Admin tomonidan qo'shiladi\.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Darajalar", callback_data="menu_kitob")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return KITOB_MENU

    keyboard_rows = []
    for book in books:
        emoji = "📗" if book.get('type') == 'pdf' else "🎵" if book.get('type') == 'audio' else "📹" if book.get('type') == 'video' else "📚"
        keyboard_rows.append([
            InlineKeyboardButton(
                f"{emoji} {esc_md(book['name'])}",
                callback_data=f"kitob_book_{book['id']}"
            )
        ])

    keyboard_rows.append([InlineKeyboardButton("↩️ Darajalar", callback_data="menu_kitob")])
    keyboard_rows.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")])

    await query.edit_message_text(
        f"📚 *{KITOB_LEVELS.get(level, level.upper())} \- Kitoblar*\n\n"
        f"Kitobni tanlang\:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return KITOB_BOOK_SELECT


async def kitob_book_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kitob ochildi - materiallar ko'rsatiladi"""
    query = update.callback_query
    await query.answer()

    book_id = int(query.data.replace("kitob_book_", ""))
    context.user_data["kitob_book_id"] = book_id

    db = get_db()
    book = db.get_kitob_book_by_id(book_id)
    materials = db.get_kitob_materials(book_id)

    if not book:
        await query.edit_message_text("❌ Kitob topilmadi.")
        return KITOB_BOOK_SELECT

    text = (
        f"📚 *{esc_md(book.get('name', 'Kitob'))}*\n\n"
        f"{esc_md(book.get('description', ''))}\n\n"
        f"*Materiallar\:*\n"
    )

    keyboard_rows = []
    for mat in materials:
        emoji = "📄" if mat.get('type') == 'pdf' else "🎵" if mat.get('type') == 'audio' else "📹" if mat.get('type') == 'video' else "📎"
        keyboard_rows.append([
            InlineKeyboardButton(
                f"{emoji} {esc_md(mat['name'])}",
                callback_data=f"kitob_mat_{mat['id']}"
            )
        ])

    keyboard_rows.append([InlineKeyboardButton("↩️ Kitoblar", callback_data=f"kitob_level_{context.user_data.get('kitob_level', 'a1')}")])
    keyboard_rows.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")])

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
    )
    return KITOB_MATERIAL_VIEW


async def kitob_material_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Material faylni yuborish"""
    query = update.callback_query
    await query.answer()

    mat_id = int(query.data.replace("kitob_mat_", ""))
    db = get_db()
    mat = db.get_kitob_material_by_id(mat_id)

    if not mat or not mat.get('file_path') or not os.path.exists(mat['file_path']):
        await query.edit_message_text("❌ Fayl topilmadi.")
        return KITOB_MATERIAL_VIEW

    file_path = mat['file_path']
    file_type = mat.get('type', 'document')

    try:
        if file_type == 'pdf':
            await query.message.reply_document(
                document=open(file_path, 'rb'),
                caption=f"📄 {esc_md(mat.get('name', 'PDF'))}",
                parse_mode="MarkdownV2",
            )
        elif file_type == 'audio':
            await query.message.reply_audio(
                audio=open(file_path, 'rb'),
                caption=f"🎵 {esc_md(mat.get('name', 'Audio'))}",
                parse_mode="MarkdownV2",
            )
        elif file_type == 'video':
            await query.message.reply_video(
                video=open(file_path, 'rb'),
                caption=f"📹 {esc_md(mat.get('name', 'Video'))}",
                parse_mode="MarkdownV2",
            )
        else:
            await query.message.reply_document(
                document=open(file_path, 'rb'),
                caption=f"📎 {esc_md(mat.get('name', 'Fayl'))}",
                parse_mode="MarkdownV2",
            )
    except Exception as e:
        logger.error(f"Fayl yuborishda xato: {e}")
        await query.edit_message_text(f"❌ Fayl yuborishda xato: {esc_md(str(e))}")

    return KITOB_MATERIAL_VIEW


# ==================== 6. KUNLIK SO'Z ====================

async def daily_word_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kunlik so'z"""
    db = get_db()
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    word = db.get_daily_word(user_id)

    if not word:
        # AI dan yangi so'z olish
        from ai_mentor_work import groq_json
        result = await groq_json([
            {"role": "system", "content": "Nemis tili o'qituvchisi. Har kuni yangi so'z bering. JSON: {\"german\": \"so'z\", \"uzbek\": \"tarjima\", \"izoh\": \"izoh o'zbek tilida\", \"misol\": \"nemischa misol\", \"sinonimlar\": [\"...\"]}"},
            {"role": "user", "content": "Bugungi kunlik so'zni ber. A2 darajasi."},
        ])

        word = {
            "german": result.get("german", "das Wort"),
            "uzbek": result.get("uzbek", "so'z"),
            "izoh": result.get("izoh", ""),
            "misol": result.get("misol", ""),
            "sinonimlar": result.get("sinonimlar", []),
        }
        db.save_daily_word(user_id, word)

    sinonimlar = ", ".join(word.get("sinonimlar", []))

    text = (
        f"📖 *Kunlik so'z*\n\n"
        f"🇩🇪 *{esc_md(word.get('german', ''))}*\n"
        f"🇺🇿 {esc_md(word.get('uzbek', ''))}\n\n"
    )
    if word.get('izoh'):
        text += f"📝 *Izoh:*\n{esc_md(word['izoh'])}\n\n"
    if word.get('misol'):
        text += f"📌 *Misol:*\n_{esc_md(word['misol'])}_\n\n"
    if sinonimlar:
        text += f"🔁 *Sinonimlar:* {esc_md(sinonimlar)}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="daily_speak")],
        [InlineKeyboardButton("📝 Yodlash", callback_data="daily_learn")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return MAIN_MENU


async def daily_speak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kunlik so'zni ovozda"""
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")

    db = get_db()
    word = db.get_daily_word(query.from_user.id)
    if word:
        text = f"{word.get('german', '')}. {word.get('misol', '')}"
        await speak_text(query, text, voice="female", speed=0.9)

    return MAIN_MENU


# ==================== YORDAM ====================

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Yordam"""
    text = (
        "ℹ️ *Yordam*\n\n"
        "*Bot imkoniyatlari\:*\n\n"
        "🤖 *AI Mentor* \- Daraja aniqlash, Vorstellen, suhbatlashish, xato banki, ovozli lug'at, rolli o'yinlar\n\n"
        "📖 *Lug'at* \- Darajaga qarab so'zlar (A1\-C1)\n\n"
        "🌐 *Tarjimon* \- UZB va DEU o'rtasida tarjima\n\n"
        "📚 *Sayfa* \- Kitob va audio materiallar\n\n"
        "📚 *Kitob Materiallar* \- PDF, audio, video (A1\-C2)\n\n"
        "📖 *Kunlik so'z* \- Har kuni yangi so'z\n\n"
        "📊 *Progressim* \- XP, daraja, grafiklar\n\n"
        "⚙️ *Sozlamalar* \- Ovoz, tezlik, daraja\n\n"
        "*Savollaringiz bo'lsa\:* @Muminov\_Abdullokh"
    )

    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
        ]),
    )
    return MAIN_MENU


# ==================== PASTKI TUGMA HANDLERLARI ====================

async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pastki doimiy tugmalarni qayta ishlash"""
    text = update.message.text

    if text == "📚 Menyu":
        await update.message.reply_text(
            "🇩🇪 *Deutsch Meister PRO*\n\n*Asosiy menyu\:*",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    elif text == "📖 Kunlik so'z":
        return await daily_word_handler(update, context)

    elif text == "🤖 AI Mentor":
        # AI Mentor menyusini ko'rsatish
        await update.message.reply_text(
            "🤖 *AI Mentor*\n\n"
            "*Imkoniyatlar\:*\n\n"
            "🎯 *Darajani aniqlash* \- 5 ta savol bilan darajangizni bilib oling\n"
            "🎤 *Vorstellen* \- O'zingizni taqdim etish mashqi\n"
            "💬 *Erfahrungen* \- B2/C1 mavzularida suhbatlashish\n"
            "🔧 *Xato banki* \- Xatolaringizni saqlash va mini\-darslar\n"
            "📚 *Ovozli lug'at* \- A1/A2/B1/B2, 20 mavzu, 25 so'z\n"
            "🎭 *Rolli o'yinlar* \- TELC/Goethe uslubi, 20 mavzu\n\n"
            "*Bo'limni tanlang\:*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Darajani aniqlash", callback_data="ai_level_detect")],
                [InlineKeyboardButton("🎤 Vorstellen", callback_data="ai_vorstellen")],
                [InlineKeyboardButton("💬 Erfahrungen", callback_data="ai_erfahrungen")],
                [InlineKeyboardButton("🔧 Xato banki", callback_data="ai_mistake_bank")],
                [InlineKeyboardButton("📚 Ovozli lug'at", callback_data="ai_voice_vocab")],
                [InlineKeyboardButton("🎭 Rolli o'yinlar", callback_data="ai_roleplay")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return MAIN_MENU

    elif text == "📊 Progressim":
        return await progress_menu(update, context)

    elif text == "🌐 Tarjimon":
        await update.message.reply_text(
            "🌐 *Tarjimon*\n\n"
            "Qaysi yo'nalishda tarjima qilmoqchisiz\?",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🇺🇿 UZB → 🇩🇪 DEU", callback_data="tarjima_uzb_deu")],
                [InlineKeyboardButton("🇩🇪 DEU → 🇺🇿 UZB", callback_data="tarjima_deu_uzb")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")],
            ]),
        )
        return TRANSLATOR

    elif text == "ℹ️ Yordam":
        return await help_handler(update, context)

    return MAIN_MENU


# ==================== ESCAPE HELPER ====================

def esc_md(text: str) -> str:
    """MarkdownV2 escape"""
    if not text:
        return ""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ==================== MAIN ====================

# ==================== MINI APP ====================
MINI_APP_URL = os.environ.get(
    "MINI_APP_URL",
    "https://deutsch-meister-miniapp-production.up.railway.app",
)


async def setup_menu_button(application: Application) -> None:
    """Bot ishga tushganda, xabar yozish maydonchasi yonidagi
    doimiy 'Menu' tugmasini Mini App ochadigan qilib sozlaydi."""
    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📱 Mini App",
                web_app=WebAppInfo(url=MINI_APP_URL),
            )
        )
        logger.info(f"✅ Mini App tugmasi sozlandi: {MINI_APP_URL}")
    except Exception as e:
        logger.error(f"❌ Mini App tugmasini sozlashda xato: {e}")


async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mini App'dan sendData() orqali kelgan ma'lumotni qabul qiladi.
    Hozircha faqat qabul qilib, tasdiq beradi — kelajakda har bir
    action turi uchun alohida ishlov qo'shiladi."""
    raw = update.effective_message.web_app_data.data
    logger.info(f"📲 Mini App'dan ma'lumot: {raw}")
    await update.effective_message.reply_text(
        "✅ Mini App'dan ma'lumot qabul qilindi!",
        reply_markup=REPLY_KEYBOARD,
    )


def main() -> None:
    """Asosiy ishga tushirish funksiyasi"""
    application = Application.builder().token(TOKEN).post_init(setup_menu_button).build()

    # ==================== CONVERSATION HANDLERS ====================

    # 1. AI Mentor ConversationHandler
    ai_mentor_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            CallbackQueryHandler(level_detect_start, pattern="^ai_level_detect$"),
            CallbackQueryHandler(vorstellen_menu, pattern="^ai_vorstellen$"),
            CallbackQueryHandler(erfahrungen_menu, pattern="^ai_erfahrungen$"),
            CallbackQueryHandler(mistake_bank_menu, pattern="^ai_mistake_bank$"),
            CallbackQueryHandler(voice_vocab_menu, pattern="^ai_voice_vocab$"),
            CallbackQueryHandler(roleplay_menu, pattern="^ai_roleplay$"),
        ],
        states={
            AI_MENTOR_MENU: [
                CallbackQueryHandler(level_detect_start, pattern="^ai_level_detect$"),
                CallbackQueryHandler(vorstellen_menu, pattern="^ai_vorstellen$"),
                CallbackQueryHandler(erfahrungen_menu, pattern="^ai_erfahrungen$"),
                CallbackQueryHandler(mistake_bank_menu, pattern="^ai_mistake_bank$"),
                CallbackQueryHandler(voice_vocab_menu, pattern="^ai_voice_vocab$"),
                CallbackQueryHandler(roleplay_menu, pattern="^ai_roleplay$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            LEVEL_DETECT_Q1: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, level_detect_process),
                CallbackQueryHandler(level_detect_process, pattern="^level_skip_"),
                CallbackQueryHandler(ld_show_section, pattern="^ld_show_"),
                CallbackQueryHandler(ld_speak_handler, pattern="^ld_speak$"),
            ],
            LEVEL_DETECT_Q2: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, level_detect_process),
                CallbackQueryHandler(level_detect_process, pattern="^level_skip_"),
                CallbackQueryHandler(ld_show_section, pattern="^ld_show_"),
                CallbackQueryHandler(ld_speak_handler, pattern="^ld_speak$"),
            ],
            LEVEL_DETECT_Q3: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, level_detect_process),
                CallbackQueryHandler(level_detect_process, pattern="^level_skip_"),
                CallbackQueryHandler(ld_show_section, pattern="^ld_show_"),
                CallbackQueryHandler(ld_speak_handler, pattern="^ld_speak$"),
            ],
            LEVEL_DETECT_Q4: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, level_detect_process),
                CallbackQueryHandler(level_detect_process, pattern="^level_skip_"),
                CallbackQueryHandler(ld_show_section, pattern="^ld_show_"),
                CallbackQueryHandler(ld_speak_handler, pattern="^ld_speak$"),
            ],
            LEVEL_DETECT_Q5: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, level_detect_process),
                CallbackQueryHandler(level_detect_process, pattern="^level_skip_"),
                CallbackQueryHandler(ld_show_section, pattern="^ld_show_"),
                CallbackQueryHandler(ld_speak_handler, pattern="^ld_speak$"),
            ],
            VORSTELLEN_START: [
                CallbackQueryHandler(vorstellen_start_new, pattern="^vorstellen_start$"),
                CallbackQueryHandler(vorstellen_rules, pattern="^vorstellen_rules$"),
                CallbackQueryHandler(vorstellen_templates, pattern="^vorstellen_templates$"),
                CallbackQueryHandler(vorstellen_template_show, pattern="^vorstellen_template_"),
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new),
                CallbackQueryHandler(vorstellen_process_new, pattern="^vorstellen_skip_"),
                CallbackQueryHandler(vorstellen_process_new, pattern="^vorstellen_next_"),
                CallbackQueryHandler(vorstellen_process_new, pattern="^vorstellen_finish$"),
            ],
            VORSTELLEN_RESULT: [
                CallbackQueryHandler(vs_show_section_new, pattern="^vs_show_"),
                CallbackQueryHandler(vs_improve_menu, pattern="^vs_show_yaxshilash$"),
                CallbackQueryHandler(vs_improve_show, pattern="^vorstellen_level_"),
                CallbackQueryHandler(vs_speak_new, pattern="^vs_speak$"),
                CallbackQueryHandler(vorstellen_pdf_new, pattern="^vorstellen_pdf$"),
                CallbackQueryHandler(vorstellen_start_new, pattern="^ai_vorstellen$"),
            ],
            VORSTELLEN_IMPROVE: [
                CallbackQueryHandler(vs_improve_show, pattern="^vorstellen_level_"),
                CallbackQueryHandler(vs_speak_new, pattern="^vs_speak$"),
                CallbackQueryHandler(vorstellen_pdf_new, pattern="^vorstellen_pdf$"),
                CallbackQueryHandler(vs_show_section_new, pattern="^vs_show_yaxshilash$"),
                CallbackQueryHandler(vorstellen_start_new, pattern="^ai_vorstellen$"),
            ],
            ERFAHRUNGEN_MENU: [
                CallbackQueryHandler(erfahrungen_topic, pattern="^erf_topic_"),
                CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            ],
            ERFAHRUNGEN_DIFFICULTY: [
                CallbackQueryHandler(erfahrungen_start_chat, pattern="^erf_diff_"),
                CallbackQueryHandler(erfahrungen_menu, pattern="^ai_erfahrungen$"),
            ],
            ERFAHRUNGEN_CHAT: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, erfahrungen_chat),
                CallbackQueryHandler(erfahrungen_result, pattern="^erf_finish$"),
            ],
            MISTAKE_BANK_MENU: [
                CallbackQueryHandler(mistake_list, pattern="^mistake_list$"),
                CallbackQueryHandler(mistake_random, pattern="^mistake_random$"),
                CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            ],
            MISTAKE_MINILESSON: [
                CallbackQueryHandler(mistake_speak_handler, pattern="^mistake_speak_"),
                CallbackQueryHandler(mistake_improve_handler, pattern="^mistake_improve_"),
                CallbackQueryHandler(mistake_practice, pattern="^mistake_practice_"),
                CallbackQueryHandler(mistake_master, pattern="^mistake_master_"),
                CallbackQueryHandler(mistake_list, pattern="^mistake_list$"),
            ],
            MISTAKE_PRACTICE: [
                MessageHandler(filters.TEXT, mistake_practice_process),
            ],
            VOICE_VOCAB_LEVEL: [
                CallbackQueryHandler(voice_vocab_level_select, pattern="^vocab_level_"),
                CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            ],
            VOICE_VOCAB_TOPIC: [
                CallbackQueryHandler(voice_vocab_topic_select, pattern="^vocab_topic_"),
                CallbackQueryHandler(voice_vocab_menu, pattern="^ai_voice_vocab$"),
            ],
            VOICE_VOCAB_WORDS: [
                CallbackQueryHandler(vocab_test_start, pattern="^vocab_test_start$"),
                CallbackQueryHandler(vocab_sprechen, pattern="^vocab_sprechen$"),
                CallbackQueryHandler(vocab_roleplay_from_vocab, pattern="^vocab_roleplay$"),
                CallbackQueryHandler(voice_vocab_level_select, pattern="^vocab_level_"),
                CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            ],
            VOICE_VOCAB_TEST: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vocab_test_process),
                CallbackQueryHandler(vocab_test_process, pattern="^vocab_skip$"),
                CallbackQueryHandler(vocab_test_process, pattern="^vocab_test_finish$"),
            ],
            VOICE_VOCAB_SPRECHEN: [
                CallbackQueryHandler(vocab_speak_story, pattern="^vocab_speak_story$"),
                CallbackQueryHandler(vocab_sprechen_ready, pattern="^vocab_sprechen_ready$"),
                MessageHandler(filters.VOICE | filters.AUDIO, vocab_sprechen_process),
                CallbackQueryHandler(voice_vocab_level_select, pattern="^ai_voice_vocab$"),
            ],
            ROLEPLAY_LEVEL: [
                CallbackQueryHandler(roleplay_level_select, pattern="^rp_level_"),
                CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            ],
            ROLEPLAY_TOPIC: [
                CallbackQueryHandler(roleplay_topic_select, pattern="^rp_topic_"),
                CallbackQueryHandler(roleplay_menu, pattern="^ai_roleplay$"),
            ],
            ROLEPLAY_RULES: [
                CallbackQueryHandler(roleplay_start_dialog, pattern="^rp_start_dialog$"),
                CallbackQueryHandler(roleplay_level_select, pattern="^rp_level_"),
            ],
            ROLEPLAY_CHAT: [
                MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, roleplay_chat),
                CallbackQueryHandler(roleplay_result, pattern="^rp_finish$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
            CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
        ],
        map_to_parent={
            AI_MENTOR_MENU: MAIN_MENU,
        },
    )

    # 2. Asosiy ConversationHandler
    main_conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler),
            ],
            TRANSLATOR: [
                CallbackQueryHandler(tarjima_uzb_deu_start, pattern="^tarjima_uzb_deu$"),
                CallbackQueryHandler(tarjima_deu_uzb_start, pattern="^tarjima_deu_uzb$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
                CallbackQueryHandler(translator_speak, pattern="^translator_speak$"),
            ],
            UZB_DEU_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translator_process),
                CallbackQueryHandler(tarjimon_menu, pattern="^menu_tarjimon$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
                CallbackQueryHandler(translator_speak, pattern="^translator_speak$"),
            ],
            DEU_UZB_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translator_process),
                CallbackQueryHandler(tarjimon_menu, pattern="^menu_tarjimon$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
                CallbackQueryHandler(translator_speak, pattern="^translator_speak$"),
            ],
            LUGAT_MENU: [
                CallbackQueryHandler(lugat_level_select, pattern="^lugat_level_"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            LUGAT_BOOK_SELECT: [
                CallbackQueryHandler(lugat_book_select, pattern="^lugat_book_"),
                CallbackQueryHandler(lugat_menu, pattern="^menu_lugat$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            LUGAT_CHAPTER_SELECT: [
                CallbackQueryHandler(lugat_chapter_view, pattern="^lugat_chapter_"),
                CallbackQueryHandler(lugat_book_select, pattern="^lugat_book_"),
                CallbackQueryHandler(lugat_menu, pattern="^menu_lugat$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SAYFA_MENU: [
                CallbackQueryHandler(sayfa_book_select, pattern="^sayfa_"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SAYFA_BOOK_SELECT: [
                CallbackQueryHandler(sayfa_material_view, pattern="^sayfa_mat_"),
                CallbackQueryHandler(sayfa_menu, pattern="^menu_sayfa$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SAYFA_AUDIO_SELECT: [
                CallbackQueryHandler(sayfa_send_pdf, pattern="^sayfa_pdf_"),
                CallbackQueryHandler(sayfa_send_audio, pattern="^sayfa_audio_"),
                CallbackQueryHandler(sayfa_book_select, pattern="^sayfa_"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            KITOB_MENU: [
                CallbackQueryHandler(kitob_level_select, pattern="^kitob_level_"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            KITOB_BOOK_SELECT: [
                CallbackQueryHandler(kitob_book_view, pattern="^kitob_book_"),
                CallbackQueryHandler(kitob_menu, pattern="^menu_kitob$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            KITOB_MATERIAL_VIEW: [
                CallbackQueryHandler(kitob_material_send, pattern="^kitob_mat_"),
                CallbackQueryHandler(kitob_book_view, pattern="^kitob_book_"),
                CallbackQueryHandler(kitob_menu, pattern="^menu_kitob$"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, reply_keyboard_handler),
        ],
    )

    # Handlerlarni qo'shish
    application.add_handler(main_conv)
    application.add_handler(ai_mentor_conv)

    # Mini App'dan kelgan ma'lumot (sendData orqali)
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

    # Pastki tugmalar handleri (conversation tashqarisida)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_keyboard_handler))

    # Kunlik so'z callback
    application.add_handler(CallbackQueryHandler(daily_speak, pattern="^daily_speak$"))
    application.add_handler(CallbackQueryHandler(daily_word_handler, pattern="^menu_kunlik$"))

    logger.info("Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
