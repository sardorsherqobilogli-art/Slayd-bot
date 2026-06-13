#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  DEUTSCH MEISTER PRO - Mukammal Nemis Tili Telegram Bot
  TO'LIQ TUZATILGAN - ai_mentor.py (yangi versiya) bilan mos
============================================================
"""

import os
import random
import datetime
import logging

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
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

# ==================== AI MENTOR — TO'LIQ IMPORT (yangi versiyaga mos) ====================
from ai_mentor import (
    # ---- STATE RAQAMLARI ----
    AI_MENTOR_MENU,
    LEVEL_DETECT_Q1, LEVEL_DETECT_Q2, LEVEL_DETECT_Q3, LEVEL_DETECT_Q4, LEVEL_DETECT_Q5,
    LEVEL_DETECT_RESULT,
    VORSTELLEN_START, VORSTELLEN_FOLLOWUP, VORSTELLEN_RESULT,
    ERFAHRUNGEN_MENU, ERFAHRUNGEN_TOPIC, ERFAHRUNGEN_DIFFICULTY,
    ERFAHRUNGEN_CHAT, ERFAHRUNGEN_RESULT,
    MISTAKE_BANK_MENU, MISTAKE_REVIEW, MISTAKE_MINILESSON, MISTAKE_PRACTICE,
    VOICE_VOCAB_MENU, VOICE_VOCAB_LEVEL, VOICE_VOCAB_TOPIC, VOICE_VOCAB_WORDS,
    VOICE_VOCAB_TEST, VOICE_VOCAB_SPRECHEN,
    ROLEPLAY_MENU, ROLEPLAY_LEVEL, ROLEPLAY_TOPIC, ROLEPLAY_RULES,
    ROLEPLAY_CHAT, ROLEPLAY_RESULT,
    AI_MENTOR_SETTINGS,

    # ---- HANDLERLAR ----
    ai_mentor_menu_handler,

    # Level detection
    level_detect_start,
    level_detect_process,
    ld_show_section,
    ld_speak_handler,

    # Vorstellen
    vorstellen_start,
    vorstellen_process,
    vs_show_section,
    vs_speak_handler,

    # Erfahrungen
    erfahrungen_menu,
    erfahrungen_topic,
    erfahrungen_start_chat,
    erfahrungen_chat,
    erfahrungen_result,

    # Mistake bank
    mistake_bank_menu,
    mistake_list,
    mistake_mini_lesson,
    mistake_speak_handler,
    mistake_improve_handler,
    mistake_practice,
    mistake_practice_process,
    mistake_master,
    mistake_random,

    # Voice vocab (yangi nomlar)
    voice_vocab_menu,
    voice_vocab_level_select,
    voice_vocab_topic_select,
    vocab_test_start,
    vocab_test_process,
    vocab_sprechen,
    vocab_speak_story,
    vocab_sprechen_ready,
    vocab_sprechen_process,
    vocab_roleplay_from_vocab,

    # Roleplay (yangi nomlar)
    roleplay_menu,
    roleplay_level_select,
    roleplay_topic_select,
    roleplay_start_dialog,
    roleplay_chat,
    roleplay_result,

    # Groq helper (tarjimon uchun)
    groq_chat,
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
    # Onboarding
    REG_PHONE,
    REG_CHANNEL,
    # Admin
    ADMIN_STATE,
) = range(17)

# ==================== ADMIN CONFIG ====================
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "sprechenmitspass")
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME}"



# ==================== KEYBOARD & STATE HELPERS ====================
async def clear_last_keyboard(context, chat_id):
    """Eski inline keyboardni o'chirish (tugmachalar chalkashmasligi uchun)"""
    last_msg_id = context.user_data.get("last_inline_msg_id")
    if last_msg_id and chat_id:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=last_msg_id, reply_markup=None
            )
        except Exception:
            pass  # Xabar allaqachon o'chirilgan yoki keyboard yo'q


def save_message_id(context, message_id):
    """Oxirgi inline keyboard xabar ID sini saqlash"""
    if message_id:
        context.user_data["last_inline_msg_id"] = message_id


def set_user_state(context, state: int, state_name: str = ""):
    """Foydalanuvchi state'ini kuzatish (debug uchun)"""
    context.user_data["current_state"] = state
    if state_name:
        context.user_data["current_state_name"] = state_name

# ==================== CALLBACK CONSTANTS ====================
class CB:
    MAIN_MENU = "main_menu"
    LEVEL_SELECT = "level_select"
    LEVEL_A1 = "level_a1"
    LEVEL_A2 = "level_a2"
    LEVEL_B1 = "level_b1"
    LEVEL_B2 = "level_b2"
    LEVEL_C1 = "level_c1"
    B1_PREP = "b1_prep"
    B2_PREP = "b2_prep"
    C1_PREP = "c1_prep"
    TRANSLATOR = "translator"
    UZB_DEU = "uzb_deu"
    DEU_UZB = "deu_uzb"
    HELP = "help"
    QUIZ_KNOW = "quiz_know"
    QUIZ_DONTKNOW = "quiz_dontknow"
    QUIZ_REPEAT = "quiz_repeat"
    POMODORO_25 = "pomodoro_25"
    POMODORO_STOP = "pomodoro_stop"
    AI_MENTOR = "ai_mentor"
    AI_MENTOR_MENU = "ai_mentor_menu"
    AI_LEVEL_DETECT = "ai_level_detect"
    AI_VORSTELLEN = "ai_vorstellen"
    AI_ERFAHRUNGEN = "ai_erfahrungen"
    AI_MISTAKE_BANK = "ai_mistake_bank"
    AI_VOICE_VOCAB = "ai_voice_vocab"
    AI_ROLEPLAY = "ai_roleplay"
    PROGRESS = "progress"
    PROGRESS_MENU = "progress_menu"
    PROGRESS_CHARTS = "progress_charts"
    PROGRESS_MISSIONS = "progress_missions"
    PROGRESS_LEVELUP = "progress_levelup"
    SETTINGS = "settings"
    SETTINGS_MENU = "settings_menu"
    SETTINGS_LEVEL = "set_level"
    SETTINGS_VOICE = "set_voice"
    SETTINGS_SPEED = "set_speed"
    SETTINGS_MISTAKES = "set_mistakes"


# ==================== LEKTSIYA YUKLASH ====================
A1_MOTIVE_LEKTIONS = {}


def load_lessons():
    global A1_MOTIVE_LEKTIONS
    try:
        from lektion_data import A1_MOTIVE_LEKTIONS as loaded_lessons
        A1_MOTIVE_LEKTIONS = loaded_lessons
        logger.info(f"✅ {len(A1_MOTIVE_LEKTIONS)} lektsiya yuklandi")
    except ImportError:
        logger.warning("⚠️ lektion_data.py topilmadi.")
        A1_MOTIVE_LEKTIONS = {}


def get_lektion_text(level: str, book: str, n: int) -> str:
    if level == "a1" and book == "motive" and n in A1_MOTIVE_LEKTIONS:
        return A1_MOTIVE_LEKTIONS[n]
    label = BOOK_LABELS.get(book, book)
    level_label = LEVEL_LABELS.get(level, level)
    return (
        f"{level_label} | {label}\n"
        f"📖 *Lektion {n}*\n\n"
        f"⏳ Bu lektion materiallari tez orada qo'shiladi\\!\n\n"
        f"📌 Hozircha A1 Motive lektsiyalari to'liq mavjud."
    )


def parse_words(level: str, book: str, n: int) -> list:
    if level == "a1" and book == "motive" and n in A1_MOTIVE_LEKTIONS:
        raw = A1_MOTIVE_LEKTIONS[n]
    else:
        return []
    words = []
    for line in raw.split("\n"):
        line = line.strip()
        for emoji in ["🔸", "🔹"]:
            line = line.replace(emoji, "").strip()
        if " - " in line:
            parts = line.split(" - ", 1)
            if len(parts) == 2:
                german = parts[0].strip()
                uzbek = parts[1].strip()
                if german and uzbek:
                    words.append((german, uzbek))
    return words


# ==================== KEYBOARD HELPERS ====================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI Mentor", callback_data=CB.AI_MENTOR_MENU)],
        [InlineKeyboardButton("📚 Daraja tanlash (A1-C1)", callback_data=CB.LEVEL_SELECT)],
        [
            InlineKeyboardButton("📗 B1 Vorbereitung", callback_data=CB.B1_PREP),
            InlineKeyboardButton("📙 B2 Vorbereitung", callback_data=CB.B2_PREP),
        ],
        [
            InlineKeyboardButton("📕 C1 Vorbereitung", callback_data=CB.C1_PREP),
            InlineKeyboardButton("🌐 Tarjimon", callback_data=CB.TRANSLATOR),
        ],
        [
            InlineKeyboardButton("📊 Mening progressim", callback_data=CB.PROGRESS_MENU),
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data=CB.SETTINGS_MENU),
        ],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data=CB.HELP)],
    ])


def level_select_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1 - Beginner", callback_data=CB.LEVEL_A1),
            InlineKeyboardButton("🟢 A2 - Elementary", callback_data=CB.LEVEL_A2),
        ],
        [
            InlineKeyboardButton("🟡 B1 - Intermediate", callback_data=CB.LEVEL_B1),
            InlineKeyboardButton("🟡 B2 - Upper-Interm.", callback_data=CB.LEVEL_B2),
        ],
        [InlineKeyboardButton("🔴 C1 - Advanced", callback_data=CB.LEVEL_C1)],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])


def books_keyboard(level: str):
    books = LEVEL_BOOKS.get(level, [])
    rows = []
    for book in books:
        rows.append([InlineKeyboardButton(
            BOOK_LABELS.get(book, book),
            callback_data=f"book_{level}_{book}"
        )])
    rows.append([InlineKeyboardButton("↩️ Darajaga qaytish", callback_data=CB.LEVEL_SELECT)])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def lektions_keyboard(level: str, book: str):
    key = f"{level}_{book}"
    start, end = BOOK_LEKTIONS.get(key, (1, 8))
    nums = list(range(start, end + 1))
    rows = []
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
    rows.append([InlineKeyboardButton("↩️ Kitobga qaytish", callback_data=f"back_book_{level}")])
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
        [InlineKeyboardButton("🤖 AI Tahlil", callback_data="translator_ai_analysis")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])


def quiz_card_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Bildim", callback_data=CB.QUIZ_KNOW),
            InlineKeyboardButton("❌ Bilmadim", callback_data=CB.QUIZ_DONTKNOW),
        ],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])


def quiz_result_keyboard(level: str, book: str, n: int, has_wrong: bool):
    rows = []
    if has_wrong:
        rows.append([InlineKeyboardButton("🔁 Bilmaganlarni takrorlash", callback_data=CB.QUIZ_REPEAT)])
    rows.append([InlineKeyboardButton("↩️ Lektsiyaga qaytish", callback_data=f"lekt_{level}_{book}_{n}")])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def esc_md(text: str) -> str:
    if not text:
        return ""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ==================== QUIZ HELPERS ====================

def get_quiz_state(context):
    return context.user_data.get("quiz", {})


def set_quiz_state(context, data: dict):
    context.user_data["quiz"] = data


async def show_quiz_card(query, context):
    q = get_quiz_state(context)
    words = q.get("words", [])
    idx = q.get("index", 0)

    if idx >= len(words):
        wrong = q.get("wrong", [])
        total = q.get("total", 0)
        correct = total - len(wrong)
        level = q.get("level", "a1")
        book = q.get("book", "motive")
        n = q.get("n", 1)

        wrong_text = ""
        if wrong:
            wrong_lines = "\n".join([f"• {esc_md(g)} — {esc_md(u)}" for g, u in wrong])
            wrong_text = f"\n\n❌ *Bilmaganlar:*\n{wrong_lines}"

        text = (
            f"🏁 *Test tugadi\\!*\n\n"
            f"✅ Bildim: {correct}/{total}\n"
            f"❌ Bilmadim: {len(wrong)}/{total}"
            + wrong_text
        )
        await query.edit_message_text(
            text, parse_mode="MarkdownV2",
            reply_markup=quiz_result_keyboard(level, book, n, bool(wrong))
        )
        user_id = query.from_user.id
        db = get_db()
        db.add_xp(user_id, XP_REWARDS["flashcard_correct"] * correct, "flashcard", f"{correct}/{total}")
        if len(wrong) == 0:
            db.add_xp(user_id, XP_REWARDS["quiz_perfect"], "quiz_perfect", f"Lektion {n}")
        return QUIZ_STATE

    german, uzbek = words[idx]
    total = q.get("total", 0)
    text = (
        f"🧠 *Yodlash testi* — {idx+1}/{total}\n\n"
        f"🇩🇪 *{esc_md(german)}*\n\n"
        f"O'zbekcha tarjimasi qanday?"
    )
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=quiz_card_keyboard())
    return QUIZ_STATE


# ==================== HANDLERS ====================

async def check_channel_membership(user_id: int, context) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id
        )
        return member.status not in ["left", "kicked", "banned"]
    except Exception:
        return False


async def ask_channel_subscribe(update, context) -> int:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga o'tish →", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")],
    ])
    msg = (
        "🎯 *Bir qadam qoldi\\!*\n\n"
        "Kanalimizga a'zo bo'ling — u yerda har kuni:\n"
        "• 📖 Foydali materiallar\n"
        "• 🎧 Audio darslar\n"
        "• 💡 Nemis tili sirlari\n\n"
        "_A'zo bo'lgach, Obunani tekshirish ni bosing\\._"
    )
    if update.message:
        await update.message.reply_text(msg, parse_mode="MarkdownV2", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode="MarkdownV2", reply_markup=keyboard)
    return REG_CHANNEL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Botni boshlash. Har doim toza state bilan boshlaydi."""
    # Oldingi state va keyboardlarni tozalash
    context.user_data.clear()
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Do'stim"
    db = get_db()
    user = db.get_or_create_user(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=first_name,
        last_name=update.effective_user.last_name,
    )
    if not user.get("phone"):
        phone_btn = KeyboardButton("📱 Telefon raqamimni ulashish", request_contact=True)
        kb = ReplyKeyboardMarkup([[phone_btn]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            f"👋 Salom, *{esc_md(first_name)}\\!*\n\n"
            "Sprechen mit Spaß botiga xush kelibsiz\\! 🎉\n\n"
            "Birga nemis tilini o'rganamiz — qiziqarli va samarali\\! 🇩🇪\n\n"
            "Davom etish uchun telefon raqamingizni ulashing\\. 🔒",
            parse_mode="MarkdownV2",
            reply_markup=kb,
        )
        return REG_PHONE
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        return await ask_channel_subscribe(update, context)
    set_user_state(context, MAIN_MENU, "MAIN_MENU")
    return await _show_welcome(update, context, user, first_name)


async def reg_phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Iltimos, pastdagi tugmani bosing 👇")
        return REG_PHONE
    user_id = update.effective_user.id
    db = get_db()
    try:
        db.update_user_phone(user_id, contact.phone_number)
    except Exception:
        pass
    await update.message.reply_text("✅ *Rahmat\\!* Raqamingiz saqlandi 🙏", parse_mode="MarkdownV2")
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        return await ask_channel_subscribe(update, context)
    user = db.get_or_create_user(user_id)
    first_name = update.effective_user.first_name or "Do'stim"
    set_user_state(context, MAIN_MENU, "MAIN_MENU")
    return await _show_welcome(update, context, user, first_name)


# ==================== TUZATISH: check_sub_handler ====================
# Avvalgi versiyada bu handler ConversationHandler TASHQARISIDA edi,
# shuning uchun REG_CHANNEL state da ishlamay xato berardi.
# Endi bu funksiya ConversationHandler ichidagi REG_CHANNEL state ga qo'shildi.

async def check_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Davom etish tugmasi — tekshiruvsiz o'tkazadi"""
    query = update.callback_query
    await query.answer("✅ Xush kelibsiz!")
    db = get_db()
    user = db.get_or_create_user(user_id)
    db.generate_daily_missions(user_id)
    first_name = query.from_user.first_name or "Do'stim"
    text = (
        f"🎉 *Salom, {esc_md(first_name)}\\!* 🇩🇪\n\n"
        "Sprechen mit Spaß ga xush kelibsiz\\!\n\n"
        f"📊 Darajangiz: *{esc_md(LEVEL_LABELS.get(user.get('current_level', 'a1'), 'A1'))}*\n\n"
        "Qayerdan boshlaymiz\\? 👇"
    )
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=main_menu_keyboard())
    await query.message.reply_text("👇", reply_markup=REPLY_KEYBOARD)
    set_user_state(context, MAIN_MENU, "MAIN_MENU")
    return MAIN_MENU


async def _show_welcome(update, context, user, first_name) -> int:
    db = get_db()
    db.generate_daily_missions(update.effective_user.id)
    text = (
        f"🎉 *Salom, {esc_md(first_name)}\\!* 🇩🇪\n\n"
        "Sprechen mit Spaß ga xush kelibsiz\\!\n\n"
        f"📊 Darajangiz: *{esc_md(LEVEL_LABELS.get(user.get('current_level', 'a1'), 'A1'))}*\n\n"
        "Qayerdan boshlaymiz\\? 👇"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=main_menu_keyboard())
    await update.message.reply_text("👇", reply_markup=REPLY_KEYBOARD)
    set_user_state(context, MAIN_MENU, "MAIN_MENU")
    return MAIN_MENU


# ==================== KUNLIK SOZ ====================
DAILY_WORDS = [
    ("der Mut", "jasorat"), ("die Hoffnung", "umid"), ("das Glück", "baxt"),
    ("die Freiheit", "erkinlik"), ("der Traum", "orzu"), ("die Stärke", "kuch"),
    ("das Vertrauen", "ishonch"), ("die Geduld", "sabr"), ("der Erfolg", "muvaffaqiyat"),
    ("die Liebe", "sevgi"), ("das Wissen", "bilim"), ("die Zeit", "vaqt"),
    ("der Weg", "yo'l"), ("die Freundschaft", "do'stlik"), ("das Leben", "hayot"),
    ("der Sommer", "yoz"), ("die Musik", "musiqa"), ("das Herz", "yurak"),
    ("die Reise", "sayohat"), ("der Frieden", "tinchlik"),
]

async def daily_word_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    import datetime as dt
    today = dt.date.today().toordinal()
    word, meaning = DAILY_WORDS[today % len(DAILY_WORDS)]
    await update.message.reply_text(
        f"📖 *Bugungi so'z:*\n\n"
        f"🇩🇪 *{esc_md(word)}*\n"
        f"🇺🇿 _{esc_md(meaning)}_\n\n"
        "_Bugun 5 marta ishlatib ko'ring\\!_ 💪",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )
    set_user_state(context, MAIN_MENU, "MAIN_MENU")
    return MAIN_MENU


# ==================== ADMIN PANEL ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    kb = ReplyKeyboardMarkup(
        [["👥 Foydalanuvchilar", "🔍 Raqam izlash"], ["🏠 Asosiy menyu"]],
        resize_keyboard=True,
    )
    db = get_db()
    try:
        total = db.get_user_count()
    except Exception:
        total = "?"
    await update.message.reply_text(
        f"🔐 *Admin Panel*\n\n👥 Jami: *{total}* ta\n\nBo'limni tanlang:",
        parse_mode="MarkdownV2", reply_markup=kb,
    )

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    db = get_db()
    try:
        users = db.get_all_users_for_admin()
    except Exception:
        await update.message.reply_text("❌ Xato.")
        return
    if not users:
        await update.message.reply_text("Hali foydalanuvchilar yo'q.")
        return
    for i in range(0, len(users), 20):
        chunk = users[i:i+20]
        lines = [f"👥 *{i+1}\\-{min(i+20,len(users))} / {len(users)} ta*\n"]
        for j, u in enumerate(chunk, i+1):
            fname = esc_md(u.get("first_name") or "—")
            phone = esc_md(u.get("phone") or "—")
            tg = esc_md("@"+u["username"] if u.get("username") else "—")
            lines.append(f"{j}\\. {fname} | 📱{phone} | {tg}")
        await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")

async def admin_search_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text("🔍 Telefon raqamini yozing:")
    context.user_data["admin_search"] = True

async def admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or not context.user_data.get("admin_search"):
        return
    context.user_data["admin_search"] = False
    q = update.message.text.strip()
    db = get_db()
    try:
        users = db.search_by_phone(q)
    except Exception:
        users = []
    if not users:
        await update.message.reply_text(f"❌ '{q}' topilmadi.")
        return
    for u in users:
        await update.message.reply_text(
            f"✅ Topildi!\n👤 {u.get('first_name') or '—'}\n"
            f"📱 {u.get('phone') or '—'}\n"
            f"TG: {'@'+u['username'] if u.get('username') else '—'}"
        )


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = get_db()
    user = db.get_or_create_user(user_id)
    await clear_last_keyboard(context, query.message.chat_id if query.message else None)
    await query.edit_message_text(
        "🏠 *Asosiy Menu*\n\n"
        f"📊 Daraja: {esc_md(LEVEL_LABELS.get(user.get('current_level', 'a1'), 'A1'))}\n"
        f"⭐ XP: {esc_md(str(user.get('total_xp', 0)))}\n\n"
        "Bo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def level_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await clear_last_keyboard(context, query.message.chat_id if query.message else None)
    await query.edit_message_text(
        "📚 *Daraja tanlash*\n\n"
        "O'z darajangizni tanlang:\n"
        "🟢 A1\\-A2: Boshlang'ich\n"
        "🟡 B1\\-B2: O'rta\n"
        "🔴 C1: Yuqori",
        parse_mode="MarkdownV2",
        reply_markup=level_select_keyboard(),
    )
    return LEVEL_SELECT


async def _show_books(query, level: str, context):
    label = LEVEL_LABELS.get(level, level)
    await clear_last_keyboard(context, query.message.chat_id if query.message else None)
    await query.edit_message_text(
        f"{esc_md(label)}\n\nKitob tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=books_keyboard(level),
    )
    state_map = {"a1": A1_MENU, "a2": A2_MENU, "b1": B1_MENU, "b2": B2_MENU, "c1": C1_MENU}
    set_user_state(context, state_map.get(level, A1_MENU), f"{level.upper()}_MENU")
    return state_map.get(level, A1_MENU)


async def level_a1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "a1", context)


async def level_a2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "a2", context)


async def level_b1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b1", context)


async def level_b2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b2", context)


async def level_c1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "c1", context)


async def b1_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b1", context)


async def b2_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b2", context)


async def c1_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "c1", context)


async def book_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await clear_last_keyboard(context, query.message.chat_id if query.message else None)
    parts = query.data.split("_", 2)
    if len(parts) < 3:
        return MAIN_MENU
    level, book = parts[1], parts[2]
    key = f"{level}_{book}"
    start, end = BOOK_LEKTIONS.get(key, (1, 8))
    label = BOOK_LABELS.get(book, book)
    level_label = LEVEL_LABELS.get(level, level)
    await query.edit_message_text(
        f"{esc_md(level_label)} \\| {esc_md(label)}\n\n"
        f"Lektion tanlang \\({esc_md(str(start))}\\-{esc_md(str(end))}\\):",
        parse_mode="MarkdownV2",
        reply_markup=lektions_keyboard(level, book),
    )
    return BOOK_MENU


async def back_book_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = query.data.split("_")[-1]
    return await _show_books(query, level, context)


async def lektion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await clear_last_keyboard(context, query.message.chat_id if query.message else None)
    parts = query.data.split("_")
    if len(parts) < 4:
        return MAIN_MENU
    level = parts[1]
    n = int(parts[-1])
    book = "_".join(parts[2:-1])
    label = BOOK_LABELS.get(book, book)
    level_label = LEVEL_LABELS.get(level, level)
    content = get_lektion_text(level, book, n)

    if content.startswith("🇩🇪"):
        text = content
    else:
        text = f"{esc_md(level_label)} \\| {esc_md(label)}\n📖 *Lektion {n}*\n\n{content}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧠 Yodlash", callback_data=f"quiz_start_{level}_{book}_{n}"),
            InlineKeyboardButton("🍅 Pomodoro", callback_data=f"pomodoro_start_{level}_{book}_{n}"),
        ],
        [InlineKeyboardButton("🎙️ Ovozda o'qish", callback_data=f"tts_lekt_{level}_{book}_{n}")],
        [InlineKeyboardButton("↩️ Lektsiyalarga qaytish", callback_data=f"book_{level}_{book}")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    set_user_state(context, BOOK_MENU, "BOOK_MENU")
    return BOOK_MENU


# ==================== QUIZ ====================

async def quiz_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    level = parts[2]
    n = int(parts[-1])
    book = "_".join(parts[3:-1])
    words = parse_words(level, book, n)
    if not words:
        await query.edit_message_text("⏳ Bu lektion uchun test hali mavjud emas.", reply_markup=back_to_main_keyboard())
        return BOOK_MENU
    random.shuffle(words)
    set_quiz_state(context, {"words": words, "index": 0, "wrong": [], "total": len(words), "level": level, "book": book, "n": n})
    set_user_state(context, QUIZ_STATE, "QUIZ_STATE")
    return await show_quiz_card(query, context)


async def quiz_know_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("✅ Zo'r!")
    q = get_quiz_state(context)
    q["index"] += 1
    set_quiz_state(context, q)
    set_user_state(context, QUIZ_STATE, "QUIZ_STATE")
    return await show_quiz_card(query, context)


async def quiz_dontknow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    q = get_quiz_state(context)
    words = q.get("words", [])
    idx = q.get("index", 0)
    if idx < len(words):
        german, uzbek = words[idx]
        await query.answer(f"❌ {uzbek}", show_alert=True)
        q["wrong"].append((german, uzbek))
    q["index"] += 1
    set_quiz_state(context, q)
    set_user_state(context, QUIZ_STATE, "QUIZ_STATE")
    return await show_quiz_card(query, context)


async def quiz_repeat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    q = get_quiz_state(context)
    wrong = q.get("wrong", [])
    if wrong:
        random.shuffle(wrong)
        set_quiz_state(context, {
            "words": wrong, "index": 0, "wrong": [],
            "total": len(wrong), "level": q.get("level", "a1"),
            "book": q.get("book", "motive"), "n": q.get("n", 1),
        })
    set_user_state(context, QUIZ_STATE, "QUIZ_STATE")
    return await show_quiz_card(query, context)


# ==================== POMODORO ====================

async def pomodoro_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    level = parts[2]
    n = int(parts[-1])
    book = "_".join(parts[3:-1])
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=25)
    end_str = end_time.strftime("%H:%M")
    context.user_data["pomodoro"] = {"level": level, "book": book, "n": n, "end": end_str}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏹️ To'xtatish", callback_data=CB.POMODORO_STOP)],
        [InlineKeyboardButton("↩️ Lektsiyaga qaytish", callback_data=f"lekt_{level}_{book}_{n}")],
    ])
    await query.edit_message_text(
        f"🍅 *Pomodoro boshlandi\\!*\n\n"
        f"⏱ 25 daqiqa o'qish vaqti\n"
        f"🏁 Tugash: *{end_str}*\n\n"
        f"Diqqatni jamlang va o'rganing\\! 💪",
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    return POMODORO_STATE


async def pomodoro_stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    p = context.user_data.get("pomodoro", {})
    level = p.get("level", "a1")
    book = p.get("book", "motive")
    n = p.get("n", 1)
    user_id = query.from_user.id
    db = get_db()
    db.add_xp(user_id, XP_REWARDS["pomodoro_25min"], "pomodoro", f"Lektion {n}")
    db.update_user(user_id, total_pomodoro_minutes=25)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Lektsiyaga qaytish", callback_data=f"lekt_{level}_{book}_{n}")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])
    await query.edit_message_text(
        f"⏹️ *Pomodoro to'xtatildi*\n\n"
        f"🎁 *\\+{esc_md(str(XP_REWARDS['pomodoro_25min']))} XP*\n\n"
        f"Yaxshi harakat\\! Davom eting 💪",
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    set_user_state(context, MAIN_MENU, "MAIN_MENU")
    return MAIN_MENU


# ==================== TTS LEKTION ====================

async def tts_lektion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    level = parts[2]
    n = int(parts[-1])
    book = "_".join(parts[3:-1])
    words = parse_words(level, book, n)
    if not words:
        await query.answer("Bu lektsiya uchun so'zlar yo'q!")
        return BOOK_MENU
    sample = random.sample(words, min(10, len(words)))
    text_to_speak = ". ".join([g for g, u in sample])
    await query.edit_message_text(
        f"🔊 *Lektion {n} \\- Ovozli o'qish*\n\n10 ta tasodifiy so'z eshiting\\.\\.\\.",
        parse_mode="MarkdownV2",
    )
    await speak_text(query, text_to_speak, voice="female", speed=0.9)
    await query.message.reply_text(
        "🔊 Ovozli o'qish tugadi\\!\n\nYana tinglashni xohlaysizmi?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Yana", callback_data=f"tts_lekt_{level}_{book}_{n}")],
            [InlineKeyboardButton("↩️ Lektsiyaga qaytish", callback_data=f"lekt_{level}_{book}_{n}")],
        ])
    )
    return BOOK_MENU


# ==================== TARJIMON ====================

async def translator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌐 *Tarjimon*\n\n*Kontekst Tarjimon 2\\.0*\n\n"
        "Qaysi yo'nalishda tarjima qilmoqchisiz?\n\n"
        "🇺🇿➡️🇩🇪 O'zbek \\- Nemis\n"
        "🇩🇪➡️🇺🇿 Nemis \\- O'zbek\n\n"
        "AI grammatika tahlili bilan\\!",
        parse_mode="MarkdownV2",
        reply_markup=translator_keyboard(),
    )
    return TRANSLATOR


async def uzb_deu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["translator_dir"] = "uzb_deu"
    await query.edit_message_text(
        "🇺🇿➡️🇩🇪 *O'zbekcha \\-\\> Nemischa*\n\n"
        "So'z, gap yoki matn yuboring\\!\n\n"
        "✨ AI grammatika tahlili bilan tarjima\n\n"
        "*Misol:* `Men 25 yoshdaman`",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return UZB_DEU_INPUT


async def deu_uzb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["translator_dir"] = "deu_uzb"
    await query.edit_message_text(
        "🇩🇪➡️🇺🇿 *Nemischa \\-\\> O'zbekcha*\n\n"
        "So'z, gap yoki matn yuboring\\!\n\n"
        "✨ AI grammatika tahlili bilan tarjima\n\n"
        "*Misol:* `Ich bin 25 Jahre alt`",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return DEU_UZB_INPUT


async def translation_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    word = update.message.text.strip()
    if not word:
        await update.message.reply_text("❗ Iltimos matn yuboring.")
        return context.user_data.get("translator_state", UZB_DEU_INPUT)

    direction = context.user_data.get("translator_dir", "uzb_deu")
    loading_msg = await update.message.reply_text("⏳ Tarjima qilinmoqda...")

    if direction == "uzb_deu":
        flag_from, flag_to = "🇺🇿", "🇩🇪"
        prompt = (
            f"O'zbek tilidan nemis tiliga tarjima qil va grammatika tahlili ber:\n\"{word}\"\n\n"
            f"Faqat JSON: {{\"translation\": \"nemischa\", \"grammar_analysis\": \"tahlil o'zbek tilida\", "
            f"\"tips\": \"maslahat\", \"level\": \"A1/A2/B1/B2/C1\"}}"
        )
    else:
        flag_from, flag_to = "🇩🇪", "🇺🇿"
        prompt = (
            f"Nemis tilidan o'zbek tiliga tarjima qil va grammatika tahlili ber:\n\"{word}\"\n\n"
            f"Faqat JSON: {{\"translation\": \"o'zbekcha\", \"grammar_analysis\": \"tahlil o'zbek tilida\", "
            f"\"tips\": \"maslahat\", \"level\": \"A1/A2/B1/B2/C1\"}}"
        )

    result = await groq_chat([
        {"role": "system", "content": "Siz professional tarjimon va grammatika o'qituvchisisiz. JSON formatida javob bering."},
        {"role": "user", "content": prompt},
    ])

    await loading_msg.delete()

    try:
        import json
        clean = result.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        translation = data.get("translation", result)
        grammar = data.get("grammar_analysis", "")
        tips = data.get("tips", "")
        level_hint = data.get("level", "")
    except Exception:
        translation = result
        grammar = ""
        tips = ""
        level_hint = ""

    text = f"{flag_from}➡️{flag_to} *Tarjima*\n\n"
    text += f"📝 *Asl matn:* {esc_md(word)}\n\n"
    text += f"✅ *Tarjima:* {esc_md(translation)}\n"
    if level_hint:
        text += f"📊 *Daraja:* {esc_md(level_hint)}\n"
    text += "\n"
    if grammar:
        text += f"🧠 *Grammatika tahlili:*\n{esc_md(grammar)}\n\n"
    if tips:
        text += f"💡 *Maslahat:* {esc_md(tips)}\n\n"

    context.user_data["last_translation"] = translation
    context.user_data["last_translation_dir"] = direction

    await update.message.reply_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yana tarjima", callback_data=CB.UZB_DEU if direction == "uzb_deu" else CB.DEU_UZB)],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="tts_translate_last")],
            [InlineKeyboardButton("🌐 Tarjimon", callback_data=CB.TRANSLATOR)],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
        ])
    )
    next_state = UZB_DEU_INPUT if direction == "uzb_deu" else DEU_UZB_INPUT
    set_user_state(context, next_state, "TRANSLATOR_INPUT")
    return next_state


async def tts_translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")
    translation = context.user_data.get("last_translation", "Hallo")
    direction = context.user_data.get("last_translation_dir", "uzb_deu")
    await speak_text(query, translation, voice="female", speed=0.9)
    return TRANSLATOR


# ==================== YORDAM ====================

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "ℹ️ *Yordam \\- Deutsch Meister Pro*\n\n"
        "*Buyruqlar:*\n"
        "/start \\— Botni ishga tushirish\n"
        "/menu \\— Asosiy menyu\n\n"
        "*Bo'limlar:*\n"
        "🤖 *AI Mentor* \\— Daraja, suhbat, xatolar, ovozli lug'at, rolplay\n"
        "📚 *Lektsiyalar* \\— A1\\-C1 kitoblar va lektsiyalar\n"
        "🧠 *Flashcard* \\— Vizual yodlash testi\n"
        "🍅 *Pomodoro* \\— 25 daqiqali fokus taymeri\n"
        "🌐 *Tarjimon* \\— UZB↔DEU \\+ AI grammatika tahlili\n"
        "📊 *Progress* \\— XP tizimi, grafiklar, kunlik vazifalar\n"
        "⚙️ *Sozlamalar* \\— Ovoz, tezlik, daraja\n\n"
        "*Ovozli funksiyalar:*\n"
        "🎙️ *TTS* \\— Matnni ovozga aylantirish \\(Edge TTS, German\\)\n"
        "🎤 *STT* \\— Ovozni matnga o'girish \\(Groq Whisper\\)\n\n"
        "*XP tizimi:*\n"
        "• Flashcard: \\+10 XP\n"
        "• AI suhbat: \\+50 XP\n"
        "• Xatoni tuzatish: \\+20 XP\n"
        "• Pomodoro 25 min: \\+30 XP\n"
        "• Level Up: \\+100 XP",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return MAIN_MENU


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    db = get_db()
    user = db.get_or_create_user(user_id)
    await update.message.reply_text(
        "🏠 *Asosiy Menu*\n\n"
        f"📊 Daraja: {esc_md(LEVEL_LABELS.get(user.get('current_level', 'a1'), 'A1'))}\n"
        f"⭐ XP: {esc_md(str(user.get('total_xp', 0)))}\n\n"
        "Bo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "/start \\— Boshlash\n"
        "/menu \\— Menyu\n"
        "/help \\— Yordam\n\n"
        "🤖 AI Mentor \\- Shaxsiy AI yordamchi\n"
        "📚 Lektsiyalar \\- Daraja bo'yicha\n"
        "🌐 Tarjimon \\- UZB↔DEU\n"
        "📊 Progress \\- XP va grafiklar",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )


async def reply_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pastki menyu tugmalari — ConversationHandler ichida ishlashi uchun state qaytaradi"""
    await clear_last_keyboard(context, update.message.chat_id if update.message else None)
    await update.message.reply_text(
        "📋 *Tez buyruqlar:*\n\n"
        "/start \\— Botni qayta boshlash\n"
        "/menu \\— Asosiy menyu\n"
        "/help \\— Yordam\n\n"
        "*Bo'limlar:*\n"
        "🤖 AI Mentor \\- Daraja aniqlash, suhbat\n"
        "📚 Lektsiyalar \\- A1\\-C1 kitoblar\n"
        "🧠 Flashcard \\- Yodlash testlari\n"
        "🍅 Pomodoro \\- Fokus taymeri\n"
        "🌐 Tarjimon \\- UZB↔DEU\n"
        "📊 Progress \\- XP va grafiklar",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )


# ==================== OVOZLI XABAR — UNIVERSAL HANDLER ====================

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    loading = await update.message.reply_text("🎙️ *Ovoz tahlil qilinmoqda...*", parse_mode="MarkdownV2")
    text = await listen_to_voice(update)
    await loading.delete()

    if text.startswith("❌"):
        await update.message.reply_text(
            f"❌ Ovozni tanishda xato:\n{text}\n\nQayta urinib ko'ring.",
            reply_markup=back_to_main_keyboard(),
        )
        return

    db = get_db()
    user = db.get_or_create_user(user_id)
    level = user.get("current_level", "a1")

    ai_response = await groq_chat([
        {"role": "system", "content": (
            f"Siz nemis tili o'qituvchisisiz. Foydalanuvchi darajasi: {level.upper()}. "
            f"Qisqa, qulay javob bering. Xatolar bo'lsa muloyim tuzating."
        )},
        {"role": "user", "content": f"[Ovozli xabar] {text}"},
    ])

    db.add_xp(user_id, XP_REWARDS.get("voice_practice", 15), "voice_message", text[:50])

    await update.message.reply_text(
        f"🎤 *Siz:* _{esc_md(text)}_\n\n"
        f"🤖 *AI Mentor:*\n{esc_md(ai_response)}\n\n"
        f"🎁 *\\+{XP_REWARDS.get('voice_practice', 15)} XP*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 AI Mentor", callback_data=CB.AI_MENTOR_MENU)],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
        ])
    )

    await speak_text(update, ai_response, voice="female", speed=0.95)


# ==================== MAIN ====================

def main() -> None:
    if not TOKEN or TOKEN == "SIZNING_BOT_TOKENINGIZ":
        logger.error("❌ BOT_TOKEN topilmadi!")
        return

    db = get_db()
    logger.info("✅ Ma'lumotlar bazasi tayyor!")
    load_lessons()

    application = Application.builder().token(TOKEN).build()

        # Reply keyboard tugmalari (har bir state'da birinchi tekshiriladi)
    reply_keyboard_handlers = [
        MessageHandler(filters.TEXT & filters.Regex("^📚 Menyu$"), reply_menu_handler),
        MessageHandler(filters.TEXT & filters.Regex("^📖 Kunlik so\'z$"), daily_word_handler),
        MessageHandler(filters.TEXT & filters.Regex("^🤖 AI Mentor$"), reply_menu_handler),
        MessageHandler(filters.TEXT & filters.Regex("^📊 Progressim$"), reply_menu_handler),
        MessageHandler(filters.TEXT & filters.Regex("^🌐 Tarjimon$"), reply_menu_handler),
        MessageHandler(filters.TEXT & filters.Regex("^ℹ️ Yordam$"), reply_menu_handler),
    ]

# ==================== COMMON HANDLERS ====================
    common_handlers = [
        # Asosiy navigatsiya
        CallbackQueryHandler(main_menu_handler,    pattern=f"^{CB.MAIN_MENU}$"),
        CallbackQueryHandler(level_select_handler, pattern=f"^{CB.LEVEL_SELECT}$"),
        CallbackQueryHandler(level_a1_handler,     pattern=f"^{CB.LEVEL_A1}$"),
        CallbackQueryHandler(level_a2_handler,     pattern=f"^{CB.LEVEL_A2}$"),
        CallbackQueryHandler(level_b1_handler,     pattern=f"^{CB.LEVEL_B1}$"),
        CallbackQueryHandler(level_b2_handler,     pattern=f"^{CB.LEVEL_B2}$"),
        CallbackQueryHandler(level_c1_handler,     pattern=f"^{CB.LEVEL_C1}$"),
        CallbackQueryHandler(b1_prep_handler,      pattern=f"^{CB.B1_PREP}$"),
        CallbackQueryHandler(b2_prep_handler,      pattern=f"^{CB.B2_PREP}$"),
        CallbackQueryHandler(c1_prep_handler,      pattern=f"^{CB.C1_PREP}$"),
        CallbackQueryHandler(book_select_handler,  pattern=r"^book_(a1|a2|b1|b2|c1)_\w+$"),
        CallbackQueryHandler(back_book_handler,    pattern=r"^back_book_(a1|a2|b1|b2|c1)$"),
        CallbackQueryHandler(lektion_handler,      pattern=r"^lekt_(a1|a2|b1|b2|c1)_\w+_\d+$"),

        # Quiz
        CallbackQueryHandler(quiz_start_handler,   pattern=r"^quiz_start_(a1|a2|b1|b2|c1)_\w+_\d+$"),
        CallbackQueryHandler(quiz_know_handler,    pattern=f"^{CB.QUIZ_KNOW}$"),
        CallbackQueryHandler(quiz_dontknow_handler,pattern=f"^{CB.QUIZ_DONTKNOW}$"),
        CallbackQueryHandler(quiz_repeat_handler,  pattern=f"^{CB.QUIZ_REPEAT}$"),

        # Pomodoro
        CallbackQueryHandler(pomodoro_start_handler, pattern=r"^pomodoro_start_(a1|a2|b1|b2|c1)_\w+_\d+$"),
        CallbackQueryHandler(pomodoro_stop_handler,  pattern=f"^{CB.POMODORO_STOP}$"),

        # TTS Lektsiya
        CallbackQueryHandler(tts_lektion_handler,  pattern=r"^tts_lekt_(a1|a2|b1|b2|c1)_\w+_\d+$"),

        # Tarjimon
        CallbackQueryHandler(translator_handler,   pattern=f"^{CB.TRANSLATOR}$"),
        CallbackQueryHandler(uzb_deu_handler,      pattern=f"^{CB.UZB_DEU}$"),
        CallbackQueryHandler(deu_uzb_handler,      pattern=f"^{CB.DEU_UZB}$"),
        CallbackQueryHandler(tts_translate_handler,pattern=r"^tts_translate_"),

        # Yordam
        CallbackQueryHandler(help_handler,         pattern=f"^{CB.HELP}$"),

        # ========== AI MENTOR ==========
        CallbackQueryHandler(ai_mentor_menu_handler, pattern=f"^{CB.AI_MENTOR_MENU}$"),

        # Level detection
        CallbackQueryHandler(level_detect_start,   pattern=f"^{CB.AI_LEVEL_DETECT}$"),
        CallbackQueryHandler(level_detect_process, pattern=r"^level_skip_\d+$"),
        CallbackQueryHandler(ld_show_section,      pattern=r"^ld_show_(tushuntirish|tarjima|yaxshilash)$"),
        CallbackQueryHandler(ld_speak_handler,     pattern=r"^ld_speak$"),

        # Vorstellen
        CallbackQueryHandler(vorstellen_start,     pattern=f"^{CB.AI_VORSTELLEN}$"),
        CallbackQueryHandler(vorstellen_process,   pattern=r"^vorstellen_"),
        CallbackQueryHandler(vs_show_section,      pattern=r"^vs_show_(tushuntirish|tarjima|yaxshilash)$"),
        CallbackQueryHandler(vs_speak_handler,     pattern=r"^vs_speak$"),

        # Erfahrungen
        CallbackQueryHandler(erfahrungen_menu,       pattern=f"^{CB.AI_ERFAHRUNGEN}$"),
        CallbackQueryHandler(erfahrungen_topic,      pattern=r"^erf_topic_\w+$"),
        CallbackQueryHandler(erfahrungen_start_chat, pattern=r"^erf_diff_\w+_(easy|medium|hard)$"),
        CallbackQueryHandler(erfahrungen_chat,       pattern=r"^erf_finish$"),

        # Mistake bank
        CallbackQueryHandler(mistake_bank_menu,      pattern=f"^{CB.AI_MISTAKE_BANK}$"),
        CallbackQueryHandler(mistake_list,           pattern=r"^mistake_list$"),
        CallbackQueryHandler(mistake_mini_lesson,    pattern=r"^mistake_lesson_\d+$"),
        CallbackQueryHandler(mistake_speak_handler,  pattern=r"^mistake_speak_\d+$"),
        CallbackQueryHandler(mistake_improve_handler,pattern=r"^mistake_improve_\d+$"),
        CallbackQueryHandler(mistake_practice,       pattern=r"^mistake_practice_\d+$"),
        CallbackQueryHandler(mistake_master,         pattern=r"^mistake_master_\d+$"),
        CallbackQueryHandler(mistake_random,         pattern=r"^mistake_random$"),

        # Voice vocab (YANGI nomlar)
        CallbackQueryHandler(voice_vocab_menu,         pattern=f"^{CB.AI_VOICE_VOCAB}$"),
        CallbackQueryHandler(voice_vocab_level_select, pattern=r"^vocab_level_(a1|a2|b1|b2)$"),
        CallbackQueryHandler(voice_vocab_topic_select, pattern=r"^vocab_topic_(a1|a2|b1|b2)_\d+$"),
        CallbackQueryHandler(vocab_test_start,         pattern=r"^vocab_test_start$"),
        CallbackQueryHandler(vocab_test_process,       pattern=r"^(vocab_skip|vocab_test_finish)$"),
        CallbackQueryHandler(vocab_sprechen,           pattern=r"^vocab_sprechen$"),
        CallbackQueryHandler(vocab_speak_story,        pattern=r"^vocab_speak_story$"),
        CallbackQueryHandler(vocab_sprechen_ready,     pattern=r"^vocab_sprechen_ready$"),
        CallbackQueryHandler(vocab_roleplay_from_vocab,pattern=r"^vocab_roleplay$"),

        # Roleplay (YANGI nomlar)
        CallbackQueryHandler(roleplay_menu,          pattern=f"^{CB.AI_ROLEPLAY}$"),
        CallbackQueryHandler(roleplay_level_select,  pattern=r"^rp_level_(a1|a2|b1|b2)$"),
        CallbackQueryHandler(roleplay_topic_select,  pattern=r"^rp_topic_(a1|a2|b1|b2)_\d+$"),
        CallbackQueryHandler(roleplay_start_dialog,  pattern=r"^rp_start_dialog$"),
        CallbackQueryHandler(roleplay_chat,          pattern=r"^rp_finish$"),

        # ========== PROGRESS ==========
        CallbackQueryHandler(progress_menu,     pattern=f"^{CB.PROGRESS_MENU}$"),
        CallbackQueryHandler(progress_charts,   pattern=f"^{CB.PROGRESS_CHARTS}$"),
        CallbackQueryHandler(progress_missions, pattern=f"^{CB.PROGRESS_MISSIONS}$"),
        CallbackQueryHandler(progress_levelup,  pattern=f"^{CB.PROGRESS_LEVELUP}$"),

        # Tarjimon AI tahlil
        CallbackQueryHandler(translator_handler, pattern=r"^translator_ai_analysis$"),

        # ========== SETTINGS ==========
        CallbackQueryHandler(settings_menu,      pattern=f"^{CB.SETTINGS_MENU}$"),
        CallbackQueryHandler(settings_level,     pattern=f"^{CB.SETTINGS_LEVEL}$"),
        CallbackQueryHandler(settings_set_level, pattern=r"^set_level_(a1|a2|b1|b2|c1)$"),
        CallbackQueryHandler(settings_voice,     pattern=f"^{CB.SETTINGS_VOICE}$"),
        CallbackQueryHandler(settings_set_voice, pattern=r"^set_voice_(female|male)$"),
        CallbackQueryHandler(settings_speed,     pattern=f"^{CB.SETTINGS_SPEED}$"),
        CallbackQueryHandler(settings_set_speed, pattern=r"^set_speed_[\d.]+$"),
        CallbackQueryHandler(settings_mistakes,  pattern=f"^{CB.SETTINGS_MISTAKES}$"),
    ]

    voice_filter = filters.VOICE | filters.AUDIO

    # ==================== CONVERSATION HANDLER ====================
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # ===== ONBOARDING STATES — TUZATISH ASOSIY JOYI =====
            # Avval bu ikki handler ConversationHandler TASHQARISIDA edi,
            # shuning uchun REG_CHANNEL state da "check_sub" bosilganda
            # ConversationHandler uni tutib ololmas va xato berardi.
            # Endi to'g'ri joyda — state ichida.
            REG_PHONE: [
                MessageHandler(filters.CONTACT, reg_phone_handler),
            ],
            REG_CHANNEL: [
                CallbackQueryHandler(check_sub_handler, pattern="^check_sub$"),
            ],

            # ===== ASOSIY STATLAR =====
            MAIN_MENU:      reply_keyboard_handlers + common_handlers,
            LEVEL_SELECT:   reply_keyboard_handlers + common_handlers,
            A1_MENU:        reply_keyboard_handlers + common_handlers,
            A2_MENU:        reply_keyboard_handlers + common_handlers,
            B1_MENU:        reply_keyboard_handlers + common_handlers,
            B2_MENU:        reply_keyboard_handlers + common_handlers,
            C1_MENU:        reply_keyboard_handlers + common_handlers,
            BOOK_MENU:      reply_keyboard_handlers + common_handlers,
            LEKTION_PAGE:   reply_keyboard_handlers + common_handlers,
            TRANSLATOR:     reply_keyboard_handlers + common_handlers,
            QUIZ_STATE:     reply_keyboard_handlers + common_handlers,
            POMODORO_STATE: reply_keyboard_handlers + common_handlers,

            # Tarjimon matn kiritish
            UZB_DEU_INPUT: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translation_input_handler),
            ],
            DEU_UZB_INPUT: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translation_input_handler),
            ],

            # ===== AI MENTOR STATES =====
            AI_MENTOR_MENU: reply_keyboard_handlers + common_handlers,

            # Level detection — matn VA ovoz
            LEVEL_DETECT_Q1: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, level_detect_process),
                MessageHandler(voice_filter, level_detect_process),
            ],
            LEVEL_DETECT_Q2: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, level_detect_process),
                MessageHandler(voice_filter, level_detect_process),
            ],
            LEVEL_DETECT_Q3: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, level_detect_process),
                MessageHandler(voice_filter, level_detect_process),
            ],
            LEVEL_DETECT_Q4: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, level_detect_process),
                MessageHandler(voice_filter, level_detect_process),
            ],
            LEVEL_DETECT_Q5: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, level_detect_process),
                MessageHandler(voice_filter, level_detect_process),
            ],
            LEVEL_DETECT_RESULT: reply_keyboard_handlers + common_handlers,

            # Vorstellen — matn VA ovoz
            VORSTELLEN_START: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vorstellen_process),
                MessageHandler(voice_filter, vorstellen_process),
            ],
            VORSTELLEN_FOLLOWUP: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vorstellen_process),
                MessageHandler(voice_filter, vorstellen_process),
            ],
            VORSTELLEN_RESULT: reply_keyboard_handlers + common_handlers,

            # Erfahrungen — matn VA ovoz
            ERFAHRUNGEN_MENU:       reply_keyboard_handlers + common_handlers,
            ERFAHRUNGEN_TOPIC:      reply_keyboard_handlers + common_handlers,
            ERFAHRUNGEN_DIFFICULTY: reply_keyboard_handlers + common_handlers,
            ERFAHRUNGEN_CHAT: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, erfahrungen_chat),
                MessageHandler(voice_filter, erfahrungen_chat),
            ],
            ERFAHRUNGEN_RESULT: reply_keyboard_handlers + common_handlers,

            # Mistake bank
            MISTAKE_BANK_MENU:  reply_keyboard_handlers + common_handlers,
            MISTAKE_REVIEW:     reply_keyboard_handlers + common_handlers,
            MISTAKE_MINILESSON: reply_keyboard_handlers + common_handlers,
            MISTAKE_PRACTICE: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mistake_practice_process),
            ],

            # Voice vocab
            VOICE_VOCAB_MENU:  reply_keyboard_handlers + common_handlers,
            VOICE_VOCAB_LEVEL: reply_keyboard_handlers + common_handlers,
            VOICE_VOCAB_TOPIC: reply_keyboard_handlers + common_handlers,
            VOICE_VOCAB_WORDS: reply_keyboard_handlers + common_handlers,
            VOICE_VOCAB_TEST: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, vocab_test_process),
                MessageHandler(voice_filter, vocab_test_process),
            ],
            VOICE_VOCAB_SPRECHEN: reply_keyboard_handlers + common_handlers + [
                MessageHandler(voice_filter, vocab_sprechen_process),
            ],

            # Roleplay — matn VA ovoz
            ROLEPLAY_MENU:  reply_keyboard_handlers + common_handlers,
            ROLEPLAY_LEVEL: reply_keyboard_handlers + common_handlers,
            ROLEPLAY_TOPIC: reply_keyboard_handlers + common_handlers,
            ROLEPLAY_RULES: reply_keyboard_handlers + common_handlers,
            ROLEPLAY_CHAT: reply_keyboard_handlers + common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, roleplay_chat),
                MessageHandler(voice_filter, roleplay_chat),
            ],
            ROLEPLAY_RESULT:    reply_keyboard_handlers + common_handlers,
            AI_MENTOR_SETTINGS: reply_keyboard_handlers + common_handlers,
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu", menu_command),
            CommandHandler("help", help_command),
        ],
        per_message=False,
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    # Qo'shimcha buyruqlar
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_panel))

    # Pastki ReplyKeyboard tugmalari
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📚 Menyu$"), reply_menu_handler
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📖 Kunlik so'z$"), daily_word_handler
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🤖 AI Mentor$"), reply_menu_handler
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^📊 Progressim$"), reply_menu_handler
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🌐 Tarjimon$"), reply_menu_handler
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^ℹ️ Yordam$"), reply_menu_handler
    ))

    # Admin panel tugmalari
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^👥 Foydalanuvchilar$"), admin_users_list
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🔍 Raqam izlash$"), admin_search_phone
    ))

    # Admin qidiruv natijasi (faqat admin_search flag True bo'lganda ishlaydi)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), admin_search_result
    ), group=10)

    # Ovozli xabarlar fallback (ConversationHandler tashqarisida)
    application.add_handler(MessageHandler(voice_filter, voice_message_handler))

    print("🤖 ==========================================")
    print("🤖   DEUTSCH MEISTER PRO ishga tushdi!")
    print("🤖 ==========================================")
    print(f"🤖 Token: {TOKEN[:10]}...")
    print(f"🤖 Groq API: {'✅ Mavjud' if GROQ_API_KEY else '❌ Mavjud emas!'}")
    print("🤖 ==========================================")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
