#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  DEUTSCH MEISTER PRO - AI Mentor moduli
  To'liq ai_mentor.py — barcha state va handlerlar
============================================================
"""

import os
import json
import random
import logging
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ==================== GROQ API ====================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama3-70b-8192"


async def groq_chat(messages: list, max_tokens: int = 800) -> str:
    """Groq API orqali AI javob olish"""
    if not GROQ_API_KEY:
        return "❌ Groq API kaliti topilmadi. Iltimos .env faylini tekshiring."
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
            )
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Groq xato: {e}")
        return f"❌ AI javob berishda xato: {e}"


def esc_md(text: str) -> str:
    """MarkdownV2 uchun maxsus belgilarni escape qilish"""
    if not text:
        return ""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ==================== STATE RAQAMLARI ====================
# AI Mentor asosiy state
AI_MENTOR_MENU = 100

# Level Detection
LEVEL_DETECT_Q1 = 110
LEVEL_DETECT_Q2 = 111
LEVEL_DETECT_Q3 = 112
LEVEL_DETECT_Q4 = 113
LEVEL_DETECT_Q5 = 114
LEVEL_DETECT_RESULT = 115

# Vorstellen (O'zini tanishtirish)
VORSTELLEN_START = 120
VORSTELLEN_RESULT = 123
VORSTELLEN_IMPROVE = 124

# Erfahrungen (Tajriba suhbati)
ERFAHRUNGEN_MENU = 130
ERFAHRUNGEN_TOPIC = 131
ERFAHRUNGEN_DIFFICULTY = 132
ERFAHRUNGEN_CHAT = 133
ERFAHRUNGEN_RESULT = 134

# Mistake Bank
MISTAKE_BANK_MENU = 140
MISTAKE_REVIEW = 141
MISTAKE_MINILESSON = 142
MISTAKE_PRACTICE = 143

# Voice Vocab
VOICE_VOCAB_MENU = 150
VOICE_VOCAB_LEVEL = 151
VOICE_VOCAB_TOPIC = 152
VOICE_VOCAB_WORDS = 153
VOICE_VOCAB_TEST = 154
VOICE_VOCAB_SPRECHEN = 155

# Roleplay
ROLEPLAY_MENU = 160
ROLEPLAY_LEVEL = 161
ROLEPLAY_TOPIC = 162
ROLEPLAY_RULES = 163
ROLEPLAY_CHAT = 164
ROLEPLAY_RESULT = 165

# Settings
AI_MENTOR_SETTINGS = 170


# ==================== AI MENTOR MENYU ====================

def ai_mentor_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Daraja aniqlash", callback_data="ai_level_detect")],
        [InlineKeyboardButton("👤 O'zini tanishtirish (Vorstellen)", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("💬 Tajriba suhbati (Erfahrungen)", callback_data="ai_erfahrungen")],
        [InlineKeyboardButton("❌ Xatolar banki", callback_data="ai_mistake_bank")],
        [InlineKeyboardButton("🔊 Ovozli lug'at", callback_data="ai_voice_vocab")],
        [InlineKeyboardButton("🎭 Rol o'yini (Roleplay)", callback_data="ai_roleplay")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])


async def ai_mentor_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🤖 *AI Mentor — Shaxsiy Nemis Tili Yordamchingiz*\n\n"
        "Qaysi bo'limdan boshlaysiz?",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_keyboard(),
    )
    return AI_MENTOR_MENU


# ==================== LEVEL DETECTION ====================

LEVEL_QUESTIONS = [
    {
        "q": "🇩🇪 *1/5 — Savol:*\n\nNemis tilida quyidagi gapni tarjima qiling:\n\n*'Ich heiße Anna und komme aus Usbekistan.'*",
        "hint": "Bu gap haqida nima bilasiz?",
    },
    {
        "q": "🇩🇪 *2/5 — Savol:*\n\nQaysi variant to'g'ri?\n\n*'Ich ___ ein Student.'*",
        "hint": "bin / bist / ist / sind",
    },
    {
        "q": "🇩🇪 *3/5 — Savol:*\n\nNemis tilida 'Men kechqurun kitob o'qiyman' ni yozing:",
        "hint": "Vaqt, fe'l, ot tartibiga e'tibor bering.",
    },
    {
        "q": "🇩🇪 *4/5 — Savol:*\n\nQuyidagi gapni to'ldiring:\n\n*'Gestern ___ ich ins Kino gegangen.'*",
        "hint": "war / bin / habe / ist",
    },
    {
        "q": "🇩🇪 *5/5 — Savol:*\n\nKonjunktiv II shaklida gap tuzing:\n\n*'Agar vaqtim bo'lsa, Germaniyaga borardim.'*",
        "hint": "Wenn ich Zeit hätte...",
    },
]


async def level_detect_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["ld_answers"] = []
    context.user_data["ld_q_index"] = 0

    await query.edit_message_text(
        "🎯 *Daraja Aniqlash Testi*\n\n"
        "5 ta savol orqali nemis tili darajangizni aniqlaymiz.\n\n"
        "Har bir savolga o'z bilimingizcha javob bering — bu sizga eng mos dars materialini topishga yordam beradi! 💪\n\n"
        "Tayyor bo'lsangiz, birinchi savolga javob bering:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Boshlash", callback_data="level_skip_0")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")],
        ]),
    )
    return LEVEL_DETECT_Q1


async def level_detect_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Savolga javob qayta ishlash — matn yoki skip tugmasi"""
    answers = context.user_data.get("ld_answers", [])
    idx = context.user_data.get("ld_q_index", 0)

    # Skip tugmasi yoki matn javob
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        # "level_skip_N" — N-savol ko'rsatish
        parts = query.data.split("_")
        idx = int(parts[-1]) if parts[-1].isdigit() else idx
        context.user_data["ld_q_index"] = idx

        if idx >= len(LEVEL_QUESTIONS):
            return await _level_detect_finish(query, context, answers)

        q = LEVEL_QUESTIONS[idx]
        await query.edit_message_text(
            q["q"] + f"\n\n💡 _{esc_md(q['hint'])}_",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"level_skip_{idx + 1}")],
                [InlineKeyboardButton("🔙 Mentor menyu", callback_data="ai_mentor_menu")],
            ]),
        )
        states = [LEVEL_DETECT_Q1, LEVEL_DETECT_Q2, LEVEL_DETECT_Q3, LEVEL_DETECT_Q4, LEVEL_DETECT_Q5]
        return states[idx] if idx < len(states) else LEVEL_DETECT_RESULT

    elif update.message:
        answer = update.message.text.strip()
        answers.append(answer)
        context.user_data["ld_answers"] = answers
        idx += 1
        context.user_data["ld_q_index"] = idx

        if idx >= len(LEVEL_QUESTIONS):
            # Fake query object uchun message dan foydalanish
            return await _level_detect_finish_msg(update.message, context, answers)

        q = LEVEL_QUESTIONS[idx]
        await update.message.reply_text(
            q["q"] + f"\n\n💡 _{esc_md(q['hint'])}_",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"level_skip_{idx + 1}")],
            ]),
        )
        states = [LEVEL_DETECT_Q1, LEVEL_DETECT_Q2, LEVEL_DETECT_Q3, LEVEL_DETECT_Q4, LEVEL_DETECT_Q5]
        return states[idx] if idx < len(states) else LEVEL_DETECT_RESULT

    return LEVEL_DETECT_Q1


async def _level_detect_finish(query, context, answers):
    """Natijalarni AI bilan tahlil qilish (query orqali)"""
    loading = await query.edit_message_text("⏳ *AI darajangizni tahlil qilmoqda...*", parse_mode="MarkdownV2")

    answers_text = "\n".join([f"{i+1}. {a}" for i, a in enumerate(answers)]) if answers else "Javoblar berilmadi"

    ai_result = await groq_chat([
        {"role": "system", "content": (
            "Siz nemis tili darajasini aniqlovchi mutaxassississiz. "
            "Foydalanuvchi javoblarini tahlil qilib, A1/A2/B1/B2/C1 darajasini aniqlang. "
            "O'zbek tilida qisqa va aniq javob bering. "
            "Format: DARAJA: [daraja]\nTAHLIL: [2-3 jumla]\nMASLAHAT: [keyingi qadam]"
        )},
        {"role": "user", "content": f"Talaba javoblari:\n{answers_text}"},
    ])

    context.user_data["detected_level"] = ai_result

    await query.edit_message_text(
        f"🎯 *Daraja Aniqlash Natijasi*\n\n{esc_md(ai_result)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Lektsiyalarga o'tish", callback_data="level_select")],
            [InlineKeyboardButton("🔄 Qayta boshlash", callback_data="ai_level_detect")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ]),
    )
    return LEVEL_DETECT_RESULT


async def _level_detect_finish_msg(message, context, answers):
    """Natijalarni AI bilan tahlil qilish (message orqali)"""
    loading = await message.reply_text("⏳ *AI darajangizni tahlil qilmoqda...*", parse_mode="MarkdownV2")

    answers_text = "\n".join([f"{i+1}. {a}" for i, a in enumerate(answers)]) if answers else "Javoblar berilmadi"

    ai_result = await groq_chat([
        {"role": "system", "content": (
            "Siz nemis tili darajasini aniqlovchi mutaxassississiz. "
            "Foydalanuvchi javoblarini tahlil qilib, A1/A2/B1/B2/C1 darajasini aniqlang. "
            "O'zbek tilida qisqa va aniq javob bering. "
            "Format: DARAJA: [daraja]\nTAHLIL: [2-3 jumla]\nMASLAHAT: [keyingi qadam]"
        )},
        {"role": "user", "content": f"Talaba javoblari:\n{answers_text}"},
    ])

    try:
        await loading.delete()
    except Exception:
        pass

    await message.reply_text(
        f"🎯 *Daraja Aniqlash Natijasi*\n\n{esc_md(ai_result)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Lektsiyalarga o'tish", callback_data="level_select")],
            [InlineKeyboardButton("🔄 Qayta boshlash", callback_data="ai_level_detect")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ]),
    )
    return LEVEL_DETECT_RESULT


async def ld_show_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    section = query.data.replace("ld_show_", "")
    result = context.user_data.get("detected_level", "")
    await query.answer(f"📄 {section}: {result[:50]}...", show_alert=True)
    return LEVEL_DETECT_RESULT


async def ld_speak_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("🔊 Ovoz funksiyasi ishlamoqda...", show_alert=True)
    return LEVEL_DETECT_RESULT


# ==================== VORSTELLEN (O'ZINI TANISHTIRISH) ====================
# 7 ta Goethe/TELC uslubidagi savol | Matn + Ovoz | AI tahlil | PDF natija
# Dizayn: Sprechen mit Spass logo + nemis bayrog'i ramkasi (qora/qizil/sariq)

VORSTELLEN_SAVOLLAR = [
    {
        "id": 1,
        "nemis": "Stellen Sie sich vor! Wie heißen Sie und wie alt sind Sie?",
        "uzbek": "O'zingizni taqdim eting! Ismingiz va yoshingiz?",
        "mavzu": "Name und Alter",
    },
    {
        "id": 2,
        "nemis": "Woher kommen Sie? Erzählen Sie von Ihrem Heimatland.",
        "uzbek": "Qayerdansiz? Vataningiz haqida gapiring.",
        "mavzu": "Herkunft / Heimatland",
    },
    {
        "id": 3,
        "nemis": "Wo wohnen Sie? Beschreiben Sie Ihre Wohnung/Ihr Haus.",
        "uzbek": "Qayerda yashaysiz? Uy/apartamentingizni tavsiflang.",
        "mavzu": "Wohnort und Wohnung",
    },
    {
        "id": 4,
        "nemis": "Erzählen Sie von Ihrer Familie.",
        "uzbek": "Oilangiz haqida gapiring.",
        "mavzu": "Familie",
    },
    {
        "id": 5,
        "nemis": "Wo haben Sie Deutsch gelernt? Wie lange lernen Sie schon?",
        "uzbek": "Qayerda nemis tilini o'rgandingiz? Qancha vaqtdan beri o'rganasiz?",
        "mavzu": "Deutsch lernen",
    },
    {
        "id": 6,
        "nemis": "Was machen Sie? (Studium, Beruf, Schule...)",
        "uzbek": "Nima ish qilasiz? (O'qish, ish, ta'lim...)",
        "mavzu": "Studium und Arbeit",
    },
    {
        "id": 7,
        "nemis": "Welche Sprachen sprechen Sie? Warum lernen Sie Deutsch?",
        "uzbek": "Qaysi tillarni bilasiz? Nima uchun nemis tilini o'rganasiz?",
        "mavzu": "Sprachen",
    },
]

VORSTELLEN_EXAMPLES = {
    "a1": "Ich heiße [Ism]. Ich bin [yosh] Jahre alt. Ich komme aus Usbekistan.",
    "a2": "Ich heiße [Ism], ich bin [yosh] Jahre alt und komme aus Usbekistan. Ich arbeite als [kasb].",
    "b1": "Mein Name ist [Ism]. Ich bin [yosh] Jahre alt und stamme aus Usbekistan. Beruflich bin ich [kasb] und interessiere mich für [qiziqish].",
    "b2": "Gestatten Sie mir, mich kurz vorzustellen: Ich heiße [Ism], bin [yosh] Jahre alt und komme ursprünglich aus Usbekistan...",
}

VORSTELLEN_RULES_TEXT = (
    "📋 *Vorstellen — qoidalar*\n\n"
    "Goethe / TELC imtihon uslubida 7 ta savolga javob berasiz:\n\n"
    "1\\. Ism va yosh\n"
    "2\\. Qayerdansiz\n"
    "3\\. Yashash joyingiz\n"
    "4\\. Oilangiz\n"
    "5\\. Nemis tilini qayerda o'rgandingiz\n"
    "6\\. Nima ish qilasiz\n"
    "7\\. Qaysi tillarni bilasiz\n\n"
    "⚠️ *Imtihonda 15 soniya tayyorlanish vaqti bor\\!*\n"
    "Biz sizga shoshilmasdan javob berish imkonini beramiz\\.\n\n"
    "📝 Matn yozing YOKI 🎙️ ovozli xabar yuboring\\."
)


def _vorstellen_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎤 Boshlash", callback_data="vorstellen_start")],
        [InlineKeyboardButton("📋 Qoidalar", callback_data="vorstellen_rules")],
        [InlineKeyboardButton("📑 Shablonlar", callback_data="vorstellen_templates")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")],
    ])


async def vorstellen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen bo'limi — asosiy menyu"""
    query = update.callback_query
    await query.answer()

    try:
        from database import get_db
        db = get_db()
        user = db.get_or_create_user(query.from_user.id)
        level = user.get("current_level", "a1")
    except Exception:
        level = "a1"

    context.user_data["vs_level"] = level

    await query.edit_message_text(
        f"👤 *O'zini Tanishtirish — Vorstellen*\n\n"
        f"📊 Darajangiz: *{level.upper()}*\n\n"
        f"🎯 *Goethe/TELC imtihon uslubida 7 ta savol\\.*\n"
        f"Har biriga matn yoki ovoz bilan javob berasiz\\.\n"
        f"Oxirida AI sizni tahlil qilib, mukammal PDF tayyorlaydi\\!\n\n"
        f"Quyidagilardan birini tanlang\\:",
        parse_mode="MarkdownV2",
        reply_markup=_vorstellen_main_keyboard(),
    )
    return VORSTELLEN_START


async def vorstellen_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen qoidalarini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        VORSTELLEN_RULES_TEXT,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 Boshlash", callback_data="vorstellen_start")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_vorstellen")],
        ]),
    )
    return VORSTELLEN_START


async def vorstellen_templates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja bo'yicha shablonlar ro'yxati"""
    query = update.callback_query
    await query.answer()

    buttons = [
        [InlineKeyboardButton(level.upper(), callback_data=f"vorstellen_template_{level}")]
        for level in VORSTELLEN_EXAMPLES.keys()
    ]
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ai_vorstellen")])

    await query.edit_message_text(
        "📑 *Shablonlar*\n\nQaysi daraja shabloni kerak\\?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return VORSTELLEN_START


async def vorstellen_template_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tanlangan daraja uchun shablonni ko'rsatish"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("vorstellen_template_", "")
    example = VORSTELLEN_EXAMPLES.get(level, VORSTELLEN_EXAMPLES["a1"])

    await query.edit_message_text(
        f"📑 *Shablon \\({level.upper()}\\)*\n\n_{esc_md(example)}_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📑 Boshqa shablon", callback_data="vorstellen_templates")],
            [InlineKeyboardButton("🎤 Boshlash", callback_data="vorstellen_start")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_vorstellen")],
        ]),
    )
    return VORSTELLEN_START


async def vorstellen_start_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen mashqini boshlash — 1-savoldan boshlaydi"""
    query = update.callback_query
    if query:
        await query.answer()

    level = context.user_data.get("vs_level", "a1")

    # Holatni butunlay tozalash
    context.user_data["vs_answers"] = {}        # {1: {"text":..., "voice": bool}, ...}
    context.user_data["vs_voice_parts"] = {}     # {1: ["...", "..."], ...} — qisman ovoz qismlari
    context.user_data["vs_voice_count"] = {}     # {1: 2, ...}
    context.user_data["vs_current_q"] = 1
    context.user_data["vs_analysis"] = None
    context.user_data["vs_level"] = level

    await _show_vorstellen_question(query or update.message, context, 1)
    return VORSTELLEN_START


async def _show_vorstellen_question(obj, context, q_num: int):
    """q_num — 1..7 savolni ko'rsatadi"""
    savol = VORSTELLEN_SAVOLLAR[q_num - 1]
    text = (
        f"🎤 *Vorstellen — Savol {q_num}/7*\n\n"
        f"🇩🇪 *{esc_md(savol['nemis'])}*\n\n"
        f"🇺🇿 _{esc_md(savol['uzbek'])}_\n\n"
        f"📝 Matn yozing YOKI 🎙️ ovozli xabar yuboring\n"
        f"_\\(bitta savolga 3 martagacha ovoz yuborishingiz mumkin\\)_"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"vorstellen_skip_{q_num}")],
        [InlineKeyboardButton("🏁 Yakunlash va tahlil", callback_data="vorstellen_finish")],
    ])

    if hasattr(obj, "edit_message_text"):
        try:
            await obj.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        except Exception:
            # Agar edit qilib bo'lmasa (masalan ovoz xabaridan keyin) — yangi xabar
            chat = obj.message if hasattr(obj, "message") else obj
            await chat.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await obj.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)


def _merge_voice_parts(context, q_num: int):
    """Bitta savol uchun to'plangan barcha ovoz qismlarini birlashtiradi"""
    parts_map = context.user_data.get("vs_voice_parts", {})
    parts = parts_map.get(q_num, [])
    if not parts:
        return
    full_text = " ".join(parts)
    answers = context.user_data.setdefault("vs_answers", {})
    if q_num in answers and answers[q_num].get("text"):
        answers[q_num]["text"] = answers[q_num]["text"] + " " + full_text
    else:
        answers[q_num] = {"text": full_text, "voice": True}
    parts_map[q_num] = []


async def vorstellen_process_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Vorstellen jarayonini boshqarish:
    — Matnli javob (har bir savol uchun)
    — Ovozli javob (har bir savolga 3 martagacha)
    — Boshqaruv tugmalari: skip, next, finish
    """
    current_q = context.user_data.get("vs_current_q", 1)

    # ── CALLBACK TUGMALAR ──────────────────────────────────────────────
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data.startswith("vorstellen_skip_"):
            q_num = int(data.split("_")[-1])
            # Agar shu savol uchun ovoz qismlari bo'lsa — birlashtiramiz, aks holda bo'sh deb belgilaymiz
            _merge_voice_parts(context, q_num)
            answers = context.user_data.setdefault("vs_answers", {})
            if q_num not in answers:
                answers[q_num] = {"text": "", "voice": False}

            next_q = q_num + 1
            context.user_data["vs_current_q"] = next_q
            if next_q > 7:
                return await _vorstellen_final_result(query, context)
            await _show_vorstellen_question(query, context, next_q)
            return VORSTELLEN_START

        if data.startswith("vorstellen_next_"):
            q_num = int(data.split("_")[-1])
            _merge_voice_parts(context, q_num)
            next_q = q_num + 1
            context.user_data["vs_current_q"] = next_q
            if next_q > 7:
                return await _vorstellen_final_result(query, context)
            await _show_vorstellen_question(query, context, next_q)
            return VORSTELLEN_START

        if data == "vorstellen_finish":
            _merge_voice_parts(context, current_q)
            return await _vorstellen_final_result(query, context)

        return VORSTELLEN_START

    # ── MATNLI JAVOB ─────────────────────────────────────────────────────
    if update.message and update.message.text:
        user_text = update.message.text.strip()
        if not user_text:
            return VORSTELLEN_START

        answers = context.user_data.setdefault("vs_answers", {})
        answers[current_q] = {"text": user_text, "voice": False}

        next_q = current_q + 1
        context.user_data["vs_current_q"] = next_q

        if next_q > 7:
            return await _vorstellen_final_result(update.message, context)

        await _show_vorstellen_question(update.message, context, next_q)
        return VORSTELLEN_START

    # ── OVOZLI JAVOB ─────────────────────────────────────────────────────
    if update.message and (update.message.voice or update.message.audio):
        loading = await update.message.reply_text(
            "🎙️ *Ovoz tahlil qilinmoqda\\.\\.\\.*", parse_mode="MarkdownV2"
        )

        recognized = await listen_to_voice(update, context, language="de")

        try:
            await loading.delete()
        except Exception:
            pass

        if not recognized or recognized.startswith("❌"):
            await update.message.reply_text(
                "⚠️ Ovozni tushuna olmadim\\. Yana urinib ko'ring yoki matn yozing\\.",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"vorstellen_skip_{current_q}")],
                    [InlineKeyboardButton("🏁 Yakunlash", callback_data="vorstellen_finish")],
                ]),
            )
            return VORSTELLEN_START

        # Ovoz sanog'i va qismlarini saqlash
        vc = context.user_data.setdefault("vs_voice_count", {})
        count = vc.get(current_q, 0) + 1
        vc[current_q] = count

        parts_map = context.user_data.setdefault("vs_voice_parts", {})
        parts_map.setdefault(current_q, []).append(recognized)

        remaining = max(0, 3 - count)
        preview = recognized[:120] + ("…" if len(recognized) > 120 else "")
        hint = (
            f"🎙️ Yana {remaining} marta ovoz yuborishingiz mumkin, "
            f"yoki pastdagi tugma bilan davom eting\\."
            if remaining > 0 else
            "🎙️ 3 ta ovoz to'ldi\\. Endi davom eting\\."
        )

        # Mavjud main.py pattern'lariga mos: faqat skip_/next_/finish ishlatiladi
        await update.message.reply_text(
            f"✅ *Ovoz qabul qilindi\\! \\({count}/3\\)*\n\n"
            f"_{esc_md(preview)}_\n\n"
            f"{hint}",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"vorstellen_next_{current_q}")],
                [InlineKeyboardButton("🏁 Yakunlash", callback_data="vorstellen_finish")],
            ]),
        )
        return VORSTELLEN_START

    return VORSTELLEN_START


async def _vorstellen_final_result(obj, context):
    """
    Barcha javoblarni AI orqali tahlil qiladi va natija sahifasini ko'rsatadi.
    obj — CallbackQuery yoki Message bo'lishi mumkin.
    """
    # Qolgan ovoz qismlarini ham birlashtirib qo'yamiz
    for q in range(1, 8):
        _merge_voice_parts(context, q)

    answers = context.user_data.get("vs_answers", {})
    level = context.user_data.get("vs_level", "a1")

    answered_nums = [q for q, a in answers.items() if a.get("text", "").strip()]
    missed = [q for q in range(1, 8) if q not in answered_nums]
    score = len(answered_nums)

    loading_text = (
        "🧠 *AI tahlil qilmoqda\\.\\.\\.*\n\n"
        "• Grammatika tekshirilmoqda\n"
        "• So'z boyligi baholanmoqda\n"
        "• Daraja aniqlanmoqda\n\n"
        "_10\\-15 soniya kuting\\.\\.\\._"
    )

    is_query = hasattr(obj, "edit_message_text")
    if is_query:
        await obj.edit_message_text(loading_text, parse_mode="MarkdownV2")
    else:
        await obj.reply_text(loading_text, parse_mode="MarkdownV2")

    all_text = "\n".join([
        f"{q}. {VORSTELLEN_SAVOLLAR[q-1]['mavzu']}: {answers[q]['text']}"
        for q in sorted(answered_nums)
    ]) or "Foydalanuvchi hech qanday javob bermadi."

    analysis = await _groq_json_vorstellen(all_text, missed, level)
    context.user_data["vs_analysis"] = analysis
    context.user_data["vs_missed"] = missed
    context.user_data["vs_score"] = score
    context.user_data["vs_answers_text"] = all_text

    # XP va xatolarni saqlash
    try:
        from database import get_db
        db = get_db()
        user_id = obj.from_user.id if is_query else context._user_id_workaround if False else None
    except Exception:
        db = None

    try:
        from database import get_db
        db = get_db()
        user_id = (obj.from_user.id if is_query else obj.chat.id)
        xp = XP_REWARDS.get("vorstellen", 30) + score * 5
        db.add_xp(user_id, xp, "vorstellen", f"Ball: {score}/7")
        for err in analysis.get("grammar_errors", [])[:5]:
            if err.get("xato") and err.get("togri"):
                db.add_mistake(
                    user_id=user_id,
                    user_input=err["xato"],
                    correct_form=err["togri"],
                    mistake_type="vorstellen_grammar",
                )
    except Exception as e:
        logger.warning(f"Vorstellen DB xatosi: {e}")

    if is_query:
        return await _show_vorstellen_result_page(obj, context)
    else:
        return await _show_vorstellen_result_page(obj, context, as_message=True)


async def _groq_json_vorstellen(all_text: str, missed: list, level: str) -> dict:
    """Groq orqali JSON formatda Vorstellen tahlili oladi"""
    if not GROQ_API_KEY:
        return {"error": "AI xizmati mavjud emas"}

    system_prompt = (
        "Siz nemis tili mutaxassisisiz. Foydalanuvchi Vorstellen (o'zini taqdim etish) "
        "savollariga javob berdi. Javoblarni tahlil qiling va FAQAT quyidagi JSON "
        "formatida javob bering — boshqa hech narsa yozmang:\n"
        "{\n"
        '  "grammar_score": 1-10,\n'
        '  "vocabulary_score": 1-10,\n'
        '  "fluency_score": 1-10,\n'
        '  "detected_level": "A1 yoki A2 yoki B1 yoki B2",\n'
        '  "tushuntirish": "Xatolar va grammatika haqida o\'zbek tilida tushuntirish (3-5 gap)",\n'
        '  "tarjima": "Foydalanuvchi javoblarining to\'g\'ri nemischa varianti (hammasi birlashtirilgan, ravon matn)",\n'
        '  "yaxshilash_a1": "A1 darajasida to\'liq mukammal Vorstellen matni (7 mavzu yoritilgan)",\n'
        '  "yaxshilash_a2": "A2 darajasida to\'liq mukammal variant",\n'
        '  "yaxshilash_b1": "B1 darajasida to\'liq mukammal variant",\n'
        '  "yaxshilash_b2": "B2 darajasida to\'liq mukammal variant",\n'
        '  "grammar_errors": [{"xato": "...", "togri": "..."}],\n'
        '  "good_points": ["...", "...", "..."]\n'
        "}"
    )
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "max_tokens": 3000,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": (
                            f"Foydalanuvchi javoblari:\n{all_text}\n\n"
                            f"Qoldirilgan savollar: {missed if missed else 'yo\u02bbq'}\n"
                            f"Foydalanuvchining hozirgi darajasi: {level.upper()}"
                        )},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            return json.loads(raw)
    except Exception as e:
        logger.error(f"Vorstellen Groq JSON xatosi: {e}")
        return {"error": str(e)}


VORSTELLEN_YULDUZ_IZOH = {
    7: "Mukammal! Barcha bo'limlar yoritilgan.",
    6: "Yaxshi! 1 ta bo'lim yetishmayapti.",
    5: "O'rta. 2 ta bo'lim qoldirilgan.",
    4: "Qoniqarli. 3 ta bo'lim yetishmayapti.",
    3: "Kam. 4 ta bo'lim qoldirilgan.",
    2: "Juda kam. 5 ta bo'lim yetishmayapti.",
    1: "Juda zaif. 6 ta bo'lim qoldirilgan.",
    0: "Hech qanday javob yo'q.",
}


async def _show_vorstellen_result_page(obj, context, as_message: bool = False):
    """Natija sahifasini ko'rsatadi (yulduz, ball, tugmalar)"""
    analysis = context.user_data.get("vs_analysis", {}) or {}
    score = context.user_data.get("vs_score", 0)
    missed = context.user_data.get("vs_missed", [])

    stars = "⭐" * score + "☆" * (7 - score)
    izoh = VORSTELLEN_YULDUZ_IZOH.get(score, "")
    level_detected = analysis.get("detected_level", "?")

    text = (
        f"🎉 *Vorstellen Natijasi*\n\n"
        f"{esc_md(stars)}\n"
        f"_{esc_md(izoh)}_\n\n"
        f"📊 *Ball: {score}/7*\n"
        f"📚 Grammatika: {analysis.get('grammar_score', '?')}/10\n"
        f"🗣️ So'z boyligi: {analysis.get('vocabulary_score', '?')}/10\n"
        f"💬 Ravonlik: {analysis.get('fluency_score', '?')}/10\n\n"
        f"🎯 *Aniqlangan daraja: {esc_md(str(level_detected))}*\n\n"
    )

    if missed:
        missed_str = ", ".join(map(str, missed))
        text += f"⚠️ *Qoldirilgan savollar: {esc_md(missed_str)}*\n\n"

    good = analysis.get("good_points", [])
    if good:
        text += "✅ *Yaxshi jihatlar:*\n"
        for g in good[:3]:
            text += f"• {esc_md(g)}\n"
        text += "\n"

    text += "🎁 *XP qo'shildi\\!*\n\nQuyidagi tugmalardan birini tanlang\\:"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💡 Tushuntirish", callback_data="vs_show_tushuntirish"),
            InlineKeyboardButton("🌐 Tarjima", callback_data="vs_show_tarjima"),
        ],
        [InlineKeyboardButton("✨ Yaxshilash", callback_data="vs_show_yaxshilash")],
        [InlineKeyboardButton("📑 PDF yuklash", callback_data="vorstellen_pdf")],
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
        [InlineKeyboardButton("🔄 Qayta boshlash", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])

    if as_message:
        await obj.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await obj.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return VORSTELLEN_RESULT


async def vs_show_section_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tushuntirish / Tarjima bo'limlarini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    analysis = context.user_data.get("vs_analysis", {}) or {}
    data = query.data

    if data == "vs_show_tushuntirish":
        title = "💡 *Tushuntirish*"
        content = analysis.get("tushuntirish", "Ma'lumot yo'q.")
        errors = analysis.get("grammar_errors", [])
        extra = ""
        if errors:
            extra = "\n\n📋 *Xatolar:*\n"
            for e in errors[:5]:
                extra += f"❌ {esc_md(e.get('xato',''))}  →  ✅ {esc_md(e.get('togri',''))}\n"
        body = f"{title}\n\n{esc_md(content)}{extra}"

    elif data == "vs_show_tarjima":
        title = "🌐 *To'g'ri nemischa variant*"
        content = analysis.get("tarjima", "Ma'lumot yo'q.")
        body = f"{title}\n\n{esc_md(content)}"

    elif data == "vs_show_back":
        # "Natijaga qaytish" — vs_show_ patterni orqali ushlanadi
        return await _show_vorstellen_result_page(query, context)

    else:
        return await vs_improve_menu(update, context)

    await query.edit_message_text(
        body,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💡 Tushuntirish", callback_data="vs_show_tushuntirish"),
                InlineKeyboardButton("🌐 Tarjima", callback_data="vs_show_tarjima"),
            ],
            [InlineKeyboardButton("✨ Yaxshilash", callback_data="vs_show_yaxshilash")],
            [InlineKeyboardButton("📑 PDF yuklash", callback_data="vorstellen_pdf")],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
            [InlineKeyboardButton("↩️ Natijaga qaytish", callback_data="vs_show_back")],
        ]),
    )
    return VORSTELLEN_RESULT


async def vs_back_to_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Natija sahifasiga qaytish"""
    query = update.callback_query
    await query.answer()
    return await _show_vorstellen_result_page(query, context)


async def vs_improve_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Yaxshilash uchun daraja tanlash menyusi"""
    query = update.callback_query
    await query.answer()

    buttons = [
        [InlineKeyboardButton(level.upper(), callback_data=f"vorstellen_level_{level}")]
        for level in VORSTELLEN_EXAMPLES.keys()
    ]
    buttons.append([InlineKeyboardButton("↩️ Natijaga qaytish", callback_data="vs_show_back")])

    await query.edit_message_text(
        "✨ *Yaxshilash — daraja tanlang*\n\n"
        "AI sizning javoblaringizni tanlangan darajada mukammallashtiradi:\n\n"
        "🟢 *A1* — Oddiy, qisqa gaplar\n"
        "🟢 *A2* — O'rta, birikmalar bilan\n"
        "🟡 *B1* — Murakkab, tushuntirishlar\n"
        "🟡 *B2* — Professional, to'liq variant\n\n"
        "*Darajangizni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return VORSTELLEN_IMPROVE


async def vs_improve_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tanlangan darajada mukammal variantni ko'rsatish (AI dan oldindan kelgan yoki yangi so'raladi)"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("vorstellen_level_", "")
    analysis = context.user_data.get("vs_analysis", {}) or {}
    improved = analysis.get(f"yaxshilash_{level}", "")

    if not improved:
        all_text = context.user_data.get("vs_answers_text", "")
        await query.edit_message_text(
            f"✨ *{level.upper()} darajasida mukammallashtirilyapti\\.\\.\\.*",
            parse_mode="MarkdownV2",
        )
        improved = await groq_chat([
            {"role": "system", "content": (
                f"Siz nemis tili o'qituvchisisiz. Foydalanuvchi javoblarini {level.upper()} "
                f"darajasida mukammallashtiring. FAQAT ravon nemischa Vorstellen matni yozing "
                f"(name/alter, herkunft, wohnort, familie, deutsch lernen, studium/arbeit, "
                f"sprachen mavzularini yoritib bering)."
            )},
            {"role": "user", "content": f"Javoblarni {level.upper()} darajasida mukammallashtir:\n{all_text}"},
        ], max_tokens=1200)
        analysis[f"yaxshilash_{level}"] = improved
        context.user_data["vs_analysis"] = analysis

    context.user_data["vs_improved_text"] = improved
    context.user_data["vs_improved_level"] = level

    await query.edit_message_text(
        f"✨ *{level.upper()} darajasida mukammal variant:*\n\n"
        f"{esc_md(improved)}\n\n"
        f"💡 _Bu matnni yodlang va ovozda mashq qiling\\!_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📑 PDF yuklash", callback_data="vorstellen_pdf")],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
            [InlineKeyboardButton("🔄 Boshqa daraja", callback_data="vs_show_yaxshilash")],
            [InlineKeyboardButton("↩️ Natijaga qaytish", callback_data="vs_show_back")],
            [InlineKeyboardButton("🔄 Yana mashq qilish", callback_data="ai_vorstellen")],
        ]),
    )
    return VORSTELLEN_IMPROVE


async def vs_speak_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Natijani ovozli o'qish (Edge TTS orqali) — yaxshilangan matn ustuvor"""
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")

    text = (
        context.user_data.get("vs_improved_text")
        or (context.user_data.get("vs_analysis", {}) or {}).get("tarjima")
        or ""
    )

    if not text:
        await query.answer(
            "⚠️ O'qiladigan matn yo'q. Avval 'Yaxshilash' yoki 'Tarjima' ni bosing.",
            show_alert=True,
        )
        return VORSTELLEN_RESULT

    try:
        await speak_text(update, text[:600])
    except Exception as e:
        logger.error(f"vs_speak_new xato: {e}")
        await query.answer("🔊 Ovoz funksiyasida xato yuz berdi.", show_alert=True)

    return VORSTELLEN_RESULT


async def vorstellen_pdf_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    PDF eksport — Sprechen mit Spass dizaynida (qora/qizil/sariq ramka + logo)
    Yaxshilangan matn bo'lsa o'shani, bo'lmasa to'g'ri tarjimani PDF qiladi.
    """
    query = update.callback_query
    await query.answer("📑 PDF tayyorlanmoqda...")

    analysis = context.user_data.get("vs_analysis", {}) or {}
    score = context.user_data.get("vs_score", 0)
    answers_text = context.user_data.get("vs_answers_text", "")

    level = context.user_data.get("vs_improved_level") or analysis.get("detected_level", "A1")
    level = str(level).lower()[:2] if level else "a1"

    improved_text = (
        context.user_data.get("vs_improved_text")
        or analysis.get(f"yaxshilash_{level}")
        or analysis.get("tarjima")
        or "Mukammal variant mavjud emas."
    )

    try:
        pdf_bytes = build_vorstellen_pdf(
            level=level.upper(),
            score=score,
            grammar_score=analysis.get("grammar_score", "?"),
            vocab_score=analysis.get("vocabulary_score", "?"),
            fluency_score=analysis.get("fluency_score", "?"),
            detected_level=analysis.get("detected_level", "?"),
            user_answers=answers_text,
            improved_text=improved_text,
        )
    except Exception as e:
        logger.error(f"PDF yaratishda xato: {e}")
        pdf_bytes = None

    if not pdf_bytes:
        await query.message.reply_text(
            "❌ PDF yaratishda xato yuz berdi\\. Iltimos qayta urinib ko'ring\\.",
            parse_mode="MarkdownV2",
        )
        return VORSTELLEN_RESULT

    from io import BytesIO
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    user_id = query.from_user.id
    filename = f"Vorstellen_{level.upper()}_{user_id}.pdf"

    await query.message.reply_document(
        document=buf,
        filename=filename,
        caption=(
            f"✅ *Vorstellen — {esc_md(level.upper())} daraja*\n\n"
            f"📑 PDF fayl tayyor\\!\n"
            f"⭐ Ball: {score}/7\n\n"
            f"💡 Bu matnni yodlang va har kuni mashq qiling\\!\n\n"
            f"📚 @sprechenmitspass"
        ),
        parse_mode="MarkdownV2",
    )
    return VORSTELLEN_RESULT


def build_vorstellen_pdf(level, score, grammar_score, vocab_score, fluency_score,
                          detected_level, user_answers, improved_text) -> bytes | None:
    """
    Sprechen mit Spass dizaynidagi PDF:
    — Nemis bayrog'i ramkasi (qora/qizil/sariq)
    — Logo yuqorida markazda
    — Barcha matn ramka ichida, A4 format
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import (
            Paragraph, Spacer, Table, TableStyle, HRFlowable,
            Frame, BaseDocTemplate, PageTemplate as PT,
        )
        from reportlab.pdfgen import canvas as rl_canvas
        import io
        import os

        BLACK = colors.HexColor("#000000")
        RED   = colors.HexColor("#CC0000")
        GOLD  = colors.HexColor("#E8A33D")
        DARK  = colors.HexColor("#1a1a1a")
        LGRAY = colors.HexColor("#F7F7F7")
        IVORY = colors.HexColor("#FAF9F6")

        PAGE_W, PAGE_H = A4
        FRAME_MARGIN = 0.6 * cm   # bayroq ramkasining qalinligi
        INNER_PAD    = 0.9 * cm   # ramka ichidan matngacha bo'sh joy

        logo_path = os.path.join(os.path.dirname(__file__), "logo_sprechen.png")
        if not os.path.exists(logo_path):
            logo_path = None

        buf = io.BytesIO()

        def draw_frame_border(c, page_w, page_h):
            """Nemis bayrog'i uslubidagi 3 qatlamli ramka: sariq tashqi, qizil o'rta, qora ichki"""
            # Tashqi — sariq
            c.setStrokeColor(GOLD)
            c.setLineWidth(14)
            c.rect(7, 7, page_w - 14, page_h - 14, fill=0, stroke=1)
            # O'rta — qizil
            c.setStrokeColor(RED)
            c.setLineWidth(7)
            c.rect(16, 16, page_w - 32, page_h - 32, fill=0, stroke=1)
            # Ichki — qora
            c.setStrokeColor(BLACK)
            c.setLineWidth(2.5)
            c.rect(24, 24, page_w - 48, page_h - 48, fill=0, stroke=1)
            # Fon — och kremrang
            c.setFillColor(IVORY)
            c.rect(28, 28, page_w - 56, page_h - 56, fill=1, stroke=0)

        def header_height():
            return 4.2 * cm

        class VorstellenPDF(BaseDocTemplate):
            def __init__(self, filename, **kw):
                super().__init__(filename, **kw)
                content_top = PAGE_H - FRAME_MARGIN - INNER_PAD - header_height()
                frame = Frame(
                    FRAME_MARGIN + INNER_PAD,
                    FRAME_MARGIN + INNER_PAD,
                    PAGE_W - 2 * (FRAME_MARGIN + INNER_PAD),
                    content_top - (FRAME_MARGIN + INNER_PAD),
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                    id="main",
                )
                self.addPageTemplates(PT("p1", [frame], onPage=self._on_page))

            def _on_page(self, c, doc):
                draw_frame_border(c, PAGE_W, PAGE_H)

                # Logo — markazda yuqorida
                logo_size = 2.6 * cm
                logo_x = (PAGE_W - logo_size) / 2
                logo_y = PAGE_H - FRAME_MARGIN - INNER_PAD - logo_size + 0.3*cm
                if logo_path:
                    try:
                        c.drawImage(
                            logo_path, logo_x, logo_y,
                            width=logo_size, height=logo_size,
                            mask="auto", preserveAspectRatio=True,
                        )
                    except Exception:
                        pass

                # Sarlavha — logo ostida markazda
                title_y = logo_y - 0.55*cm
                c.setFont("Helvetica-Bold", 16)
                c.setFillColor(DARK)
                c.drawCentredString(PAGE_W / 2, title_y, "SPRECHEN MIT SPASS")

                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(RED)
                c.drawCentredString(PAGE_W / 2, title_y - 0.45*cm, "VORSTELLEN — Mukammal Natija")

                # Daraja badji — chap yuqori burchak
                badge_w, badge_h = 2.1*cm, 0.85*cm
                bx = FRAME_MARGIN + INNER_PAD
                by = PAGE_H - FRAME_MARGIN - INNER_PAD - badge_h + 0.2*cm
                c.setFillColor(RED)
                c.roundRect(bx, by, badge_w, badge_h, 4, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(bx + badge_w/2, by + 0.27*cm, str(level))

                # Yulduz badji — o'ng yuqori burchak
                ex = PAGE_W - FRAME_MARGIN - INNER_PAD - badge_w
                c.setFillColor(GOLD)
                c.roundRect(ex, by, badge_w, badge_h, 4, fill=1, stroke=0)
                c.setFillColor(DARK)
                c.setFont("Helvetica-Bold", 12)
                c.drawCentredString(ex + badge_w/2, by + 0.27*cm, f"{score}/7")

                # Ajratuvchi chiziq
                sep_y = title_y - 0.85*cm
                c.setStrokeColor(GOLD)
                c.setLineWidth(1.5)
                c.line(FRAME_MARGIN + INNER_PAD, sep_y, PAGE_W - FRAME_MARGIN - INNER_PAD, sep_y)

        # ── STYLES ──
        head_style = ParagraphStyle(
            "Head", fontName="Helvetica-Bold", fontSize=12,
            textColor=RED, spaceBefore=10, spaceAfter=5, leading=15,
        )
        body_style = ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9.5,
            textColor=DARK, leading=14, spaceAfter=3,
        )
        german_style = ParagraphStyle(
            "German", fontName="Helvetica-Oblique", fontSize=10,
            textColor=BLACK, leading=16, spaceAfter=3,
        )
        footer_style = ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=7.5,
            textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceBefore=6,
        )

        story = []

        # Ball jadvali
        table_data = [
            ["Ko'rsatkich", "Ball", "Ko'rsatkich", "Ball"],
            ["Grammatika", f"{grammar_score}/10", "So'z boyligi", f"{vocab_score}/10"],
            ["Ravonlik", f"{fluency_score}/10", "Aniqlangan daraja", str(detected_level)],
        ]
        col_w = (PAGE_W - 2*(FRAME_MARGIN + INNER_PAD)) / 4
        tbl = Table(table_data, colWidths=[col_w*1.3, col_w*0.7, col_w*1.3, col_w*0.7])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), BLACK),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 8.5),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,1), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LGRAY, colors.white]),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#BBBBBB")),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.35*cm))

        story.append(Paragraph("📝 SIZNING JAVOBLARINGIZ", head_style))
        story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
        story.append(Spacer(1, 0.12*cm))
        for line in (user_answers or "Javoblar yo'q.").split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph(f"✨ MUKAMMAL VARIANT ({level} DARAJASI)", head_style))
        story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
        story.append(Spacer(1, 0.12*cm))
        for para in (improved_text or "").split(". "):
            p = para.strip()
            if p:
                if not p.endswith("."):
                    p += "."
                story.append(Paragraph(p, german_style))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("💡 MASLAHATLAR", head_style))
        story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
        story.append(Spacer(1, 0.1*cm))
        tips = [
            "Bu matnni yodlang va har kuni ovozda mashq qiling.",
            "Har kuni 5 marta takrorlang — muskul xotirasi hosil bo'ladi.",
            "Ovozingizni yozib, tinglang va taqqoslang.",
            "Imtihonda 15 soniya tayyorlanish vaqtingiz bor — tez o'ylang!",
            "7 ta bo'limning barchasini yoritishga harakat qiling.",
        ]
        for i, t in enumerate(tips, 1):
            story.append(Paragraph(f"{i}. {t}", body_style))

        story.append(Spacer(1, 0.4*cm))
        story.append(HRFlowable(width="100%", thickness=1.5, color=RED))
        story.append(Paragraph("@sprechenmitspass  |  t.me/sprechenmitspass  |  Deutsch Meister Pro", footer_style))

        doc = VorstellenPDF(buf, pagesize=A4)
        doc.build(story)
        return buf.getvalue()

    except ImportError as e:
        logger.warning(f"reportlab import xatosi: {e}")
        return None
    except Exception as e:
        logger.error(f"PDF qurishda xato: {e}")
        return None


# ==================== ERFAHRUNGEN (TAJRIBA SUHBATI) ====================

ERFAHRUNGEN_TOPICS_LIST = [
    ("travel", "✈️ Sayohat"),
    ("work", "💼 Ish va Kasb"),
    ("hobby", "🎨 Hobbilar"),
    ("family", "👨‍👩‍👧 Oila"),
    ("study", "📚 O'qish"),
    ("food", "🍽️ Taom"),
    ("sport", "⚽ Sport"),
    ("city", "🏙️ Shahar va Yashash"),
]


async def erfahrungen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    rows = []
    for key, label in ERFAHRUNGEN_TOPICS_LIST:
        rows.append([InlineKeyboardButton(label, callback_data=f"erf_topic_{key}")])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")])

    await query.edit_message_text(
        "💬 *Erfahrungen — Tajriba Suhbati*\n\n"
        "Qaysi mavzuda nemis tilida suhbatlashasiz?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return ERFAHRUNGEN_MENU


async def erfahrungen_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    topic_key = query.data.replace("erf_topic_", "")
    topic_label = dict(ERFAHRUNGEN_TOPICS_LIST).get(topic_key, topic_key)
    context.user_data["erf_topic"] = topic_key
    context.user_data["erf_topic_label"] = topic_label

    try:
        from database import get_db
        db = get_db()
        user = db.get_or_create_user(query.from_user.id)
        level = user.get("current_level", "a1")
    except Exception:
        level = "a1"
    context.user_data["erf_level"] = level

    await query.edit_message_text(
        f"💬 *{esc_md(topic_label)} — Qiyinchilik darajasi*\n\n"
        f"Qaysi darajada suhbatlashasiz?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Oson (A1-A2)", callback_data=f"erf_diff_{topic_key}_{level}_easy")],
            [InlineKeyboardButton("🟡 O'rta (B1)", callback_data=f"erf_diff_{topic_key}_{level}_medium")],
            [InlineKeyboardButton("🔴 Qiyin (B2-C1)", callback_data=f"erf_diff_{topic_key}_{level}_hard")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_erfahrungen")],
        ]),
    )
    return ERFAHRUNGEN_TOPIC


async def erfahrungen_start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    difficulty = parts[-1]
    context.user_data["erf_difficulty"] = difficulty
    context.user_data["erf_history"] = []

    topic_label = context.user_data.get("erf_topic_label", "Suhbat")
    level = context.user_data.get("erf_level", "a1")

    diff_map = {"easy": "Oson (A1-A2)", "medium": "O'rta (B1)", "hard": "Qiyin (B2-C1)"}
    diff_label = diff_map.get(difficulty, difficulty)

    loading = await query.edit_message_text("⏳ *AI suhbat boshlayapti...*", parse_mode="MarkdownV2")

    ai_start = await groq_chat([
        {"role": "system", "content": (
            f"Siz nemis tili suhbat partneri va o'qituvchisisiz. "
            f"Mavzu: {topic_label}. Qiyinchilik: {diff_label}. Daraja: {level.upper()}. "
            f"Nemis tilida suhbatni boshlang. Bitta savol bering. "
            f"Keyin o'zbek tilida qisqa tarjima va grammatika maslahat qo'shing."
        )},
        {"role": "user", "content": "Suhbatni boshlang"},
    ])

    context.user_data["erf_history"] = [{"role": "assistant", "content": ai_start}]

    await query.edit_message_text(
        f"💬 *{esc_md(topic_label)} — {esc_md(diff_label)}*\n\n"
        f"🤖 *AI Mentor:*\n{esc_md(ai_start)}\n\n"
        f"_Javob yozing yoki ovoz yuboring_ 🎤",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 Suhbatni yakunlash", callback_data="erf_finish")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_erfahrungen")],
        ]),
    )
    return ERFAHRUNGEN_CHAT


async def erfahrungen_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "erf_finish":
            return await erfahrungen_result(update, context)
        return ERFAHRUNGEN_CHAT

    if not update.message:
        return ERFAHRUNGEN_CHAT

    text = update.message.text.strip() if update.message.text else ""
    if not text:
        return ERFAHRUNGEN_CHAT

    history = context.user_data.get("erf_history", [])
    topic_label = context.user_data.get("erf_topic_label", "Suhbat")
    level = context.user_data.get("erf_level", "a1")
    difficulty = context.user_data.get("erf_difficulty", "medium")

    history.append({"role": "user", "content": text})

    loading = await update.message.reply_text("⏳ *AI javob berayapti...*", parse_mode="MarkdownV2")

    ai_resp = await groq_chat([
        {"role": "system", "content": (
            f"Siz nemis tili suhbat partneri va o'qituvchisisiz. "
            f"Mavzu: {topic_label}. Daraja: {level.upper()}. "
            f"Talabaning javobidagi xatolarni muloyim tuzating, keyin suhbatni davom ettiring. "
            f"Nemis tilida javob bering va O'zbek tilidagi qisqa izoh qo'shing."
        )},
        *history[-6:],
    ])

    history.append({"role": "assistant", "content": ai_resp})
    context.user_data["erf_history"] = history

    try:
        await loading.delete()
    except Exception:
        pass

    try:
        from database import get_db
        db = get_db()
        db.add_xp(update.effective_user.id, 10, "erfahrungen_chat", text[:30])
    except Exception:
        pass

    await update.message.reply_text(
        f"🤖 *AI Mentor:*\n{esc_md(ai_resp)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 Suhbatni yakunlash", callback_data="erf_finish")],
        ]),
    )
    return ERFAHRUNGEN_CHAT


async def erfahrungen_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        edit_func = query.edit_message_text
    else:
        edit_func = None

    history = context.user_data.get("erf_history", [])
    level = context.user_data.get("erf_level", "a1")
    topic_label = context.user_data.get("erf_topic_label", "Suhbat")

    user_msgs = [m["content"] for m in history if m["role"] == "user"]
    combined = " | ".join(user_msgs) if user_msgs else "Javob berilmadi"

    eval_result = await groq_chat([
        {"role": "system", "content": (
            f"Nemis tili suhbat baholovchisisiz. Daraja: {level.upper()}. "
            f"Talabaning suhbatini baholang.\n"
            f"Format:\n⭐ BAL: /10\n✅ YAXSHI:\n❌ XATOLAR:\n💡 MASLAHAT:"
        )},
        {"role": "user", "content": f"Mavzu: {topic_label}\nTalaba: {combined}"},
    ])

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yana suhbat", callback_data="ai_erfahrungen")],
        [InlineKeyboardButton("🤖 AI Mentor", callback_data="ai_mentor_menu")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])

    result_text = (
        f"🏁 *Suhbat Yakunlandi\\!*\n\n"
        f"📌 *Mavzu:* {esc_md(topic_label)}\n\n"
        f"{esc_md(eval_result)}\n\n"
        f"🎁 *\\+50 XP* qo'shildi\\!"
    )

    try:
        from database import get_db
        db = get_db()
        user_id = update.callback_query.from_user.id if update.callback_query else update.effective_user.id
        db.add_xp(user_id, 50, "erfahrungen_complete", topic_label)
    except Exception:
        pass

    if edit_func:
        await edit_func(result_text, parse_mode="MarkdownV2", reply_markup=keyboard)
    elif update.message:
        await update.message.reply_text(result_text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return ERFAHRUNGEN_RESULT


# ==================== MISTAKE BANK ====================

async def mistake_bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        from database import get_db
        db = get_db()
        mistakes = db.get_user_mistakes(query.from_user.id) or []
        count = len(mistakes)
    except Exception:
        mistakes = []
        count = 0

    await query.edit_message_text(
        f"❌ *Xatolar Banki*\n\n"
        f"📊 Jami xatolar: *{count}* ta\n\n"
        f"Xatolaringizni ko'rib chiqing va ustida ishlang\\!",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📋 Xatolar ro'yxati ({count})", callback_data="mistake_list")],
            [InlineKeyboardButton("🎲 Tasodifiy xato", callback_data="mistake_random")],
            [InlineKeyboardButton("✏️ Mashq qilish", callback_data="mistake_practice_0")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")],
        ]),
    )
    return MISTAKE_BANK_MENU


async def mistake_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        from database import get_db
        db = get_db()
        mistakes = db.get_user_mistakes(query.from_user.id) or []
    except Exception:
        mistakes = []

    if not mistakes:
        await query.edit_message_text(
            "✅ *Xatolar yo'q\\!*\n\nHali xato qilinmagan yoki tuzatilgan 🎉",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mistake_bank")],
            ]),
        )
        return MISTAKE_REVIEW

    rows = []
    for i, m in enumerate(mistakes[:10]):
        wrong = m.get("wrong_text", f"Xato {i+1}")[:30]
        rows.append([InlineKeyboardButton(
            f"❌ {wrong}",
            callback_data=f"mistake_lesson_{i}"
        )])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mistake_bank")])

    await query.edit_message_text(
        f"📋 *Xatolar Ro'yxati*\n\n_{len(mistakes)} ta xato topildi_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return MISTAKE_REVIEW


async def mistake_mini_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[-1])

    try:
        from database import get_db
        db = get_db()
        mistakes = db.get_user_mistakes(query.from_user.id) or []
        mistake = mistakes[idx] if idx < len(mistakes) else None
    except Exception:
        mistake = None

    if not mistake:
        await query.answer("Xato topilmadi", show_alert=True)
        return MISTAKE_MINILESSON

    wrong = mistake.get("wrong_text", "")
    correct = mistake.get("correct_text", "")

    ai_lesson = await groq_chat([
        {"role": "system", "content": (
            "Siz nemis tili o'qituvchisisiz. "
            "Talabaning xatosi haqida qisqa mini-dars bering. "
            "O'zbek tilida tushuntirib, nemis tilida misollar keltiring."
        )},
        {"role": "user", "content": f"Xato: '{wrong}'\nTo'g'ri: '{correct}'"},
    ])

    await query.edit_message_text(
        f"📖 *Mini Dars*\n\n"
        f"❌ *Xato:* {esc_md(wrong)}\n"
        f"✅ *To'g'ri:* {esc_md(correct)}\n\n"
        f"🎓 *Tushuntirish:*\n{esc_md(ai_lesson)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 Ovozda o'qish", callback_data=f"mistake_speak_{idx}")],
            [InlineKeyboardButton("✏️ Mashq", callback_data=f"mistake_practice_{idx}")],
            [InlineKeyboardButton("🔙 Ro'yxatga", callback_data="mistake_list")],
        ]),
    )
    return MISTAKE_MINILESSON


async def mistake_speak_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...", show_alert=True)
    return MISTAKE_MINILESSON


async def mistake_improve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("✨ Yaxshilash funksiyasi", show_alert=True)
    return MISTAKE_MINILESSON


async def mistake_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[-1])

    try:
        from database import get_db
        db = get_db()
        db.mark_mistake_mastered(query.from_user.id, idx)
        db.add_xp(query.from_user.id, 20, "mistake_mastered", f"xato {idx}")
    except Exception:
        pass

    await query.answer("✅ O'zlashtirdi! +20 XP", show_alert=True)
    return MISTAKE_REVIEW


async def mistake_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        from database import get_db
        db = get_db()
        mistakes = db.get_user_mistakes(query.from_user.id) or []
    except Exception:
        mistakes = []

    if not mistakes:
        await query.answer("Xatolar topilmadi!", show_alert=True)
        return MISTAKE_BANK_MENU

    idx = random.randint(0, len(mistakes) - 1)
    # mistake_mini_lesson-ni chaqirish uchun query.data ni o'zgartiramiz
    context.user_data["_temp_mistake_idx"] = idx
    return await mistake_mini_lesson(update, context)


async def mistake_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[-1])

    try:
        from database import get_db
        db = get_db()
        mistakes = db.get_user_mistakes(query.from_user.id) or []
        mistake = mistakes[idx] if idx < len(mistakes) else None
    except Exception:
        mistake = None

    wrong = mistake.get("wrong_text", "") if mistake else "gapni yozing"

    context.user_data["practice_mistake_idx"] = idx
    context.user_data["practice_mistake"] = mistake

    await query.edit_message_text(
        f"✏️ *Mashq — Xatoni To'g'rilang*\n\n"
        f"❌ *Xato gap:* _{esc_md(wrong)}_\n\n"
        f"Bu gapni to'g'ri yozing\\:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Orqaga", callback_data="mistake_list")],
        ]),
    )
    return MISTAKE_PRACTICE


async def mistake_practice_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return MISTAKE_PRACTICE

    text = update.message.text.strip()
    mistake = context.user_data.get("practice_mistake", {})
    idx = context.user_data.get("practice_mistake_idx", 0)
    correct = mistake.get("correct_text", "") if mistake else ""

    ai_check = await groq_chat([
        {"role": "system", "content": (
            "Nemis tili o'qituvchisi sifatida talabaning javobini tekshiring. "
            "To'g'ri/noto'g'ri ekanligini ayting va qisqa tushuntiring. O'zbek tilida."
        )},
        {"role": "user", "content": f"To'g'ri javob: '{correct}'\nTalaba yozdi: '{text}'"},
    ])

    try:
        from database import get_db
        db = get_db()
        db.add_xp(update.effective_user.id, 20, "mistake_practice", text[:30])
    except Exception:
        pass

    await update.message.reply_text(
        f"🔍 *Tekshiruv Natijasi:*\n\n"
        f"📝 *Siz yozdingiz:* {esc_md(text)}\n"
        f"✅ *To'g'ri:* {esc_md(correct)}\n\n"
        f"🤖 *AI Baholash:*\n{esc_md(ai_check)}\n\n"
        f"🎁 *\\+20 XP*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ O'zlashtirildi!", callback_data=f"mistake_master_{idx}")],
            [InlineKeyboardButton("🔄 Qayta urinish", callback_data=f"mistake_practice_{idx}")],
            [InlineKeyboardButton("📋 Ro'yxatga", callback_data="mistake_list")],
        ]),
    )
    return MISTAKE_PRACTICE


# ==================== VOICE VOCAB ====================

VOCAB_TOPICS = {
    "a1": [
        "Salomlashish (Grüßen)",
        "Raqamlar (Zahlen)",
        "Ranglar (Farben)",
        "Kun va Oy (Tage & Monate)",
        "Oila (Familie)",
    ],
    "a2": [
        "Uy va Xona (Haus & Zimmer)",
        "Oziq-ovqat (Lebensmittel)",
        "Transport (Verkehr)",
        "Kasb (Berufe)",
        "Sport (Sport)",
    ],
    "b1": [
        "Muhit (Umwelt)",
        "Sog'liq (Gesundheit)",
        "Ta'lim (Bildung)",
        "Ish (Arbeit)",
        "Sayohat (Reisen)",
    ],
    "b2": [
        "Siyosat (Politik)",
        "Texnologiya (Technologie)",
        "San'at (Kunst)",
        "Iqtisodiyot (Wirtschaft)",
        "Jamiyat (Gesellschaft)",
    ],
}

SAMPLE_VOCAB = {
    "a1": [
        ("Hallo", "Salom"), ("Tschüss", "Xayr"), ("Danke", "Rahmat"),
        ("Bitte", "Iltimos"), ("Ja", "Ha"), ("Nein", "Yo'q"),
        ("gut", "yaxshi"), ("schlecht", "yomon"),
    ],
    "a2": [
        ("die Küche", "oshxona"), ("das Schlafzimmer", "yotoqxona"),
        ("das Brot", "non"), ("die Milch", "sut"),
        ("der Bus", "avtobus"), ("der Zug", "poyezd"),
    ],
    "b1": [
        ("die Umwelt", "atrof-muhit"), ("die Gesundheit", "sog'liq"),
        ("die Bildung", "ta'lim"), ("die Arbeit", "ish"),
        ("die Reise", "sayohat"), ("der Erfolg", "muvaffaqiyat"),
    ],
    "b2": [
        ("die Gesellschaft", "jamiyat"), ("die Technologie", "texnologiya"),
        ("die Wirtschaft", "iqtisodiyot"), ("die Kunst", "san'at"),
        ("die Politik", "siyosat"), ("die Forschung", "tadqiqot"),
    ],
}


async def voice_vocab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Voice Vocab asosiy menyusi"""
    query = update.callback_query
    await query.answer()
    return await voice_vocab_level_select(update, context)


async def voice_vocab_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🔊 *Ovozli Lug'at — Voice Vocab*\n\n"
        "Qaysi daraja uchun so'z o'rganasiz?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 A1", callback_data="vocab_level_a1"),
                InlineKeyboardButton("🟢 A2", callback_data="vocab_level_a2"),
            ],
            [
                InlineKeyboardButton("🟡 B1", callback_data="vocab_level_b1"),
                InlineKeyboardButton("🟡 B2", callback_data="vocab_level_b2"),
            ],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")],
        ]),
    )
    return VOICE_VOCAB_LEVEL


async def voice_vocab_topic_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = query.data.replace("vocab_level_", "")
    context.user_data["vocab_level"] = level

    topics = VOCAB_TOPICS.get(level, VOCAB_TOPICS["a1"])
    rows = []
    for i, topic in enumerate(topics):
        rows.append([InlineKeyboardButton(topic, callback_data=f"vocab_topic_{level}_{i}")])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ai_voice_vocab")])

    await query.edit_message_text(
        f"🔊 *Ovozli Lug'at — {level.upper()}*\n\n"
        f"Mavzu tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return VOICE_VOCAB_TOPIC


async def vocab_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    level = parts[2] if len(parts) > 2 else context.user_data.get("vocab_level", "a1")
    topic_idx = int(parts[3]) if len(parts) > 3 else 0

    context.user_data["vocab_level"] = level
    topics = VOCAB_TOPICS.get(level, VOCAB_TOPICS["a1"])
    topic = topics[topic_idx] if topic_idx < len(topics) else topics[0]
    context.user_data["vocab_topic"] = topic

    words = SAMPLE_VOCAB.get(level, SAMPLE_VOCAB["a1"])
    random.shuffle(words)
    context.user_data["vocab_words"] = words
    context.user_data["vocab_idx"] = 0
    context.user_data["vocab_correct"] = 0

    if not words:
        await query.answer("So'zlar topilmadi!", show_alert=True)
        return VOICE_VOCAB_MENU

    german, uzbek = words[0]

    await query.edit_message_text(
        f"🔊 *Ovozli Lug'at — {level.upper()}*\n"
        f"📌 *Mavzu:* {esc_md(topic)}\n\n"
        f"*1/{len(words)}*\n\n"
        f"🇩🇪 *{esc_md(german)}*\n\n"
        f"O'zbek tilidagi tarjimasini yozing:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💡 Ko'rsatish", callback_data="vocab_skip")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_voice_vocab")],
        ]),
    )
    return VOICE_VOCAB_TEST


async def vocab_test_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == "vocab_skip":
            words = context.user_data.get("vocab_words", [])
            idx = context.user_data.get("vocab_idx", 0)
            if idx < len(words):
                german, uzbek = words[idx]
                await query.answer(f"✅ To'g'ri javob: {uzbek}", show_alert=True)
            context.user_data["vocab_idx"] = idx + 1

        elif query.data == "vocab_test_finish":
            return await _vocab_result(query, context)

        idx = context.user_data.get("vocab_idx", 0)
        words = context.user_data.get("vocab_words", [])

        if idx >= len(words):
            return await _vocab_result(query, context)

        german, uzbek = words[idx]
        level = context.user_data.get("vocab_level", "a1")

        await query.edit_message_text(
            f"🔊 *{level.upper()} — {idx+1}/{len(words)}*\n\n"
            f"🇩🇪 *{esc_md(german)}*\n\n"
            f"O'zbek tilidagi tarjimasini yozing:",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💡 Ko'rsatish", callback_data="vocab_skip")],
                [InlineKeyboardButton("🏁 Yakunlash", callback_data="vocab_test_finish")],
            ]),
        )
        return VOICE_VOCAB_TEST

    elif update.message:
        text = update.message.text.strip().lower()
        words = context.user_data.get("vocab_words", [])
        idx = context.user_data.get("vocab_idx", 0)
        correct_count = context.user_data.get("vocab_correct", 0)

        if idx >= len(words):
            return VOICE_VOCAB_TEST

        german, uzbek = words[idx]
        is_correct = text == uzbek.lower() or text in uzbek.lower()

        if is_correct:
            correct_count += 1
            context.user_data["vocab_correct"] = correct_count
            feedback = "✅ *To'g'ri!*"
        else:
            feedback = f"❌ *Noto'g'ri!* To'g'ri javob: *{esc_md(uzbek)}*"

        context.user_data["vocab_idx"] = idx + 1

        if idx + 1 >= len(words):
            await update.message.reply_text(
                f"{feedback}\n\n🏁 Test tugadi!",
                parse_mode="MarkdownV2",
            )
            return await _vocab_result_msg(update.message, context)

        next_german, _ = words[idx + 1]
        await update.message.reply_text(
            f"{feedback}\n\n"
            f"*{idx+2}/{len(words)}*\n\n"
            f"🇩🇪 *{esc_md(next_german)}*\n\n"
            f"O'zbek tilidagi tarjimasini yozing:",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💡 Ko'rsatish", callback_data="vocab_skip")],
                [InlineKeyboardButton("🏁 Yakunlash", callback_data="vocab_test_finish")],
            ]),
        )
        return VOICE_VOCAB_TEST

    return VOICE_VOCAB_TEST


async def _vocab_result(query, context):
    words = context.user_data.get("vocab_words", [])
    correct = context.user_data.get("vocab_correct", 0)
    total = len(words)
    level = context.user_data.get("vocab_level", "a1")

    try:
        from database import get_db
        db = get_db()
        db.add_xp(query.from_user.id, correct * 5, "vocab_test", f"{level} test")
    except Exception:
        pass

    await query.edit_message_text(
        f"🏁 *Test Yakunlandi\\!*\n\n"
        f"✅ To'g'ri: *{correct}/{total}*\n"
        f"🎁 *\\+{correct * 5} XP*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 Talaffuz mashqi", callback_data="vocab_sprechen")],
            [InlineKeyboardButton("🔄 Qayta", callback_data=f"vocab_level_{level}")],
            [InlineKeyboardButton("🔙 Mentor", callback_data="ai_mentor_menu")],
        ]),
    )
    return VOICE_VOCAB_WORDS


async def _vocab_result_msg(message, context):
    words = context.user_data.get("vocab_words", [])
    correct = context.user_data.get("vocab_correct", 0)
    total = len(words)
    level = context.user_data.get("vocab_level", "a1")

    try:
        from database import get_db
        db = get_db()
        db.add_xp(message.from_user.id, correct * 5, "vocab_test", f"{level} test")
    except Exception:
        pass

    await message.reply_text(
        f"🏁 *Test Yakunlandi\\!*\n\n"
        f"✅ To'g'ri: *{correct}/{total}*\n"
        f"🎁 *\\+{correct * 5} XP*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 Talaffuz mashqi", callback_data="vocab_sprechen")],
            [InlineKeyboardButton("🔄 Qayta", callback_data=f"vocab_level_{level}")],
            [InlineKeyboardButton("🔙 Mentor", callback_data="ai_mentor_menu")],
        ]),
    )
    return VOICE_VOCAB_WORDS


async def vocab_sprechen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = context.user_data.get("vocab_level", "a1")
    words = context.user_data.get("vocab_words", SAMPLE_VOCAB.get(level, []))

    if not words:
        await query.answer("So'zlar topilmadi!", show_alert=True)
        return VOICE_VOCAB_SPRECHEN

    sample = random.sample(words, min(5, len(words)))
    word_list = "\n".join([f"🔸 *{esc_md(g)}* — {esc_md(u)}" for g, u in sample])
    context.user_data["sprechen_words"] = sample

    await query.edit_message_text(
        f"🎤 *Talaffuz Mashqi*\n\n"
        f"Quyidagi so'zlarni nemis tilida aytib yuboring:\n\n"
        f"{word_list}\n\n"
        f"Ovoz xabar yuboring! 🎙️",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Tayyor", callback_data="vocab_sprechen_ready")],
            [InlineKeyboardButton("📖 Hikoya mashqi", callback_data="vocab_speak_story")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_voice_vocab")],
        ]),
    )
    return VOICE_VOCAB_SPRECHEN


async def vocab_speak_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = context.user_data.get("vocab_level", "a1")
    words = context.user_data.get("vocab_words", SAMPLE_VOCAB.get(level, []))

    if not words:
        await query.answer("So'zlar topilmadi!", show_alert=True)
        return VOICE_VOCAB_SPRECHEN

    sample_words = [g for g, u in random.sample(words, min(3, len(words)))]
    story_prompt = f"So'zlardan foydalanib qisqa gap tuzing: {', '.join(sample_words)}"

    ai_story = await groq_chat([
        {"role": "system", "content": (
            f"Nemis tili o'qituvchisi sifatida berilgan so'zlardan foydalanib "
            f"{level.upper()} darajasida qisqa hikoya yarating (3-5 gap). "
            f"Keyin o'zbek tiliga tarjima qiling."
        )},
        {"role": "user", "content": story_prompt},
    ])

    await query.edit_message_text(
        f"📖 *Hikoya Mashqi*\n\n"
        f"So'zlar: _{esc_md(', '.join(sample_words))}_\n\n"
        f"{esc_md(ai_story)}\n\n"
        f"Bu hikoyani ovozda gapirib yuboring! 🎙️",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎭 Roleplay boshlash", callback_data="vocab_roleplay")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="vocab_sprechen")],
        ]),
    )
    return VOICE_VOCAB_SPRECHEN


async def vocab_sprechen_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎙️ *Tayyor bo'lgach ovoz yuboring\\!*\n\n"
        "Ovoz xabarni yuboring va AI talaffuzingizni baholaydi.",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Orqaga", callback_data="vocab_sprechen")],
        ]),
    )
    return VOICE_VOCAB_SPRECHEN


async def vocab_sprechen_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovoz xabarini qayta ishlash"""
    try:
        from voice_engine import listen_to_voice
        text = await listen_to_voice(update)
    except Exception:
        text = "❌ Ovoz tanilmadi"

    if text.startswith("❌"):
        await update.message.reply_text(
            f"❌ *Ovoz tanilmadi:* {esc_md(text)}\n\nQayta urinib ko'ring.",
            parse_mode="MarkdownV2",
        )
        return VOICE_VOCAB_SPRECHEN

    words = context.user_data.get("sprechen_words", [])
    word_list = [g for g, u in words] if words else []

    ai_eval = await groq_chat([
        {"role": "system", "content": (
            "Nemis tili talaffuz baholovchisi sifatida talabaning aytganlarini baholang. "
            "Talaffuz to'g'ri/noto'g'riligi haqida o'zbek tilida qisqa fikr bildiring."
        )},
        {"role": "user", "content": f"Kerakli so'zlar: {', '.join(word_list)}\nTalaba aytdi: {text}"},
    ])

    try:
        from database import get_db
        db = get_db()
        db.add_xp(update.effective_user.id, 25, "vocab_sprechen", text[:30])
    except Exception:
        pass

    await update.message.reply_text(
        f"🎤 *Siz aytdingiz:* _{esc_md(text)}_\n\n"
        f"🤖 *Baholash:*\n{esc_md(ai_eval)}\n\n"
        f"🎁 *\\+25 XP*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Qayta mashq", callback_data="vocab_sprechen")],
            [InlineKeyboardButton("🎭 Roleplay", callback_data="vocab_roleplay")],
            [InlineKeyboardButton("🔙 Mentor", callback_data="ai_mentor_menu")],
        ]),
    )
    return VOICE_VOCAB_SPRECHEN


async def vocab_roleplay_from_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = context.user_data.get("vocab_level", "a1")
    context.user_data["rp_from_vocab"] = True
    context.user_data["rp_level"] = level

    await query.edit_message_text(
        "🎭 *Vocab dan Roleplayga o'tish*\n\n"
        f"Daraja: *{level.upper()}*\n\n"
        "Rol o'yini boshlanmoqda...",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Boshlash", callback_data=f"rp_level_{level}")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_voice_vocab")],
        ]),
    )
    return ROLEPLAY_LEVEL


# ==================== ROLEPLAY ====================

ROLEPLAY_TOPICS = {
    "a1": [
        ("shop", "🛒 Do'konda xarid qilish"),
        ("cafe", "☕ Kafeda buyurtma berish"),
        ("intro", "👋 Yangi tanishish"),
        ("doctor", "🏥 Shifokorga borish"),
    ],
    "a2": [
        ("hotel", "🏨 Mehmonxonada"),
        ("station", "🚉 Vokzalda"),
        ("job_interview", "💼 Ish suhbati"),
        ("bank", "🏦 Bankda"),
    ],
    "b1": [
        ("debate", "🗣️ Muhokama"),
        ("university", "🎓 Universitetda"),
        ("complaint", "😤 Shikoyat qilish"),
        ("meeting", "👥 Yig'ilishda"),
    ],
    "b2": [
        ("negotiation", "🤝 Muzokaralar"),
        ("conference", "🎤 Konferentsiya"),
        ("job_advanced", "💼 Yuqori lavozim suhbati"),
        ("politics", "🏛️ Siyosiy muhokama"),
    ],
}


async def roleplay_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎭 *Rol O'yini — Roleplay*\n\n"
        "Haqiqiy hayot vaziyatlarida nemis tilida muloqot qiling\\!\n\n"
        "Daraja tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 A1", callback_data="rp_level_a1"),
                InlineKeyboardButton("🟢 A2", callback_data="rp_level_a2"),
            ],
            [
                InlineKeyboardButton("🟡 B1", callback_data="rp_level_b1"),
                InlineKeyboardButton("🟡 B2", callback_data="rp_level_b2"),
            ],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")],
        ]),
    )
    return ROLEPLAY_MENU


async def roleplay_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = query.data.replace("rp_level_", "")
    context.user_data["rp_level"] = level

    topics = ROLEPLAY_TOPICS.get(level, ROLEPLAY_TOPICS["a1"])
    rows = []
    for i, (key, label) in enumerate(topics):
        rows.append([InlineKeyboardButton(label, callback_data=f"rp_topic_{level}_{i}")])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ai_roleplay")])

    await query.edit_message_text(
        f"🎭 *Roleplay — {level.upper()}*\n\n"
        f"Vaziyat tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return ROLEPLAY_LEVEL


async def roleplay_topic_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    level = parts[2]
    topic_idx = int(parts[3]) if len(parts) > 3 else 0

    topics = ROLEPLAY_TOPICS.get(level, ROLEPLAY_TOPICS["a1"])
    topic_key, topic_label = topics[topic_idx] if topic_idx < len(topics) else topics[0]

    context.user_data["rp_topic_key"] = topic_key
    context.user_data["rp_topic_label"] = topic_label
    context.user_data["rp_history"] = []

    await query.edit_message_text(
        f"🎭 *{esc_md(topic_label)}*\n\n"
        f"*Daraja:* {level.upper()}\n\n"
        f"Siz mijoz/foydalanuvchi rolini o'ynaysiz. "
        f"AI xizmat ko'rsatuvchi rolini bajaradi.\n\n"
        f"Nemis tilida suhbatlashing\\! 🇩🇪",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Boshlash", callback_data="rp_start_dialog")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data=f"rp_level_{level}")],
        ]),
    )
    return ROLEPLAY_RULES


async def roleplay_start_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = context.user_data.get("rp_level", "a1")
    topic_label = context.user_data.get("rp_topic_label", "Suhbat")

    loading = await query.edit_message_text("⏳ *Suhbat boshlanyapti...*", parse_mode="MarkdownV2")

    ai_start = await groq_chat([
        {"role": "system", "content": (
            f"Siz {topic_label} vaziyatida xizmat ko'rsatuvchi rolisiz. "
            f"Daraja: {level.upper()}. "
            f"Nemis tilida suhbatni boshlang. "
            f"Qisqa va tabiiy gapirishga harakat qiling. "
            f"Har bir javobingiz oxirida O'zbek tilidagi qisqa izoh qo'shing."
        )},
        {"role": "user", "content": "Suhbatni boshlang"},
    ])

    context.user_data["rp_history"] = [{"role": "assistant", "content": ai_start}]

    await query.edit_message_text(
        f"🎭 *{esc_md(topic_label)}*\n\n"
        f"🤖 *AI ({level.upper()}):*\n{esc_md(ai_start)}\n\n"
        f"_Javob yozing yoki ovoz yuboring_ 🎤",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 Suhbatni yakunlash", callback_data="rp_finish")],
        ]),
    )
    return ROLEPLAY_CHAT


async def roleplay_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "rp_finish":
            return await roleplay_result(update, context)
        return ROLEPLAY_CHAT

    if not update.message:
        return ROLEPLAY_CHAT

    # Ovoz yoki matn
    if update.message.voice or update.message.audio:
        try:
            from voice_engine import listen_to_voice
            text = await listen_to_voice(update)
        except Exception:
            text = "❌ Ovoz tanilmadi"
    else:
        text = update.message.text.strip() if update.message.text else ""

    if not text or text.startswith("❌"):
        await update.message.reply_text("❗ Iltimos matn yoki ovoz yuboring.")
        return ROLEPLAY_CHAT

    history = context.user_data.get("rp_history", [])
    level = context.user_data.get("rp_level", "a1")
    topic_label = context.user_data.get("rp_topic_label", "Suhbat")

    history.append({"role": "user", "content": text})

    loading = await update.message.reply_text("⏳ *AI javob berayapti...*", parse_mode="MarkdownV2")

    ai_resp = await groq_chat([
        {"role": "system", "content": (
            f"Siz {topic_label} vaziyatida xizmat ko'rsatuvchi rolisiz. "
            f"Daraja: {level.upper()}. "
            f"Talabaning xatolarini muloyim tuzating va suhbatni davom ettiring. "
            f"Nemis tilida javob bering va O'zbek tilidagi qisqa izoh qo'shing."
        )},
        *history[-6:],
    ])

    history.append({"role": "assistant", "content": ai_resp})
    context.user_data["rp_history"] = history

    try:
        await loading.delete()
    except Exception:
        pass

    try:
        from database import get_db
        db = get_db()
        db.add_xp(update.effective_user.id, 10, "roleplay_chat", text[:30])
    except Exception:
        pass

    await update.message.reply_text(
        f"🤖 *AI ({level.upper()}):*\n{esc_md(ai_resp)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 Suhbatni yakunlash", callback_data="rp_finish")],
        ]),
    )
    return ROLEPLAY_CHAT


async def roleplay_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        edit_func = query.edit_message_text
        user_id = query.from_user.id
    elif update.message:
        edit_func = None
        user_id = update.effective_user.id
    else:
        return ROLEPLAY_RESULT

    history = context.user_data.get("rp_history", [])
    level = context.user_data.get("rp_level", "a1")
    topic_label = context.user_data.get("rp_topic_label", "Suhbat")

    user_msgs = [m["content"] for m in history if m["role"] == "user"]
    combined = " | ".join(user_msgs) if user_msgs else "Javob berilmadi"

    eval_result = await groq_chat([
        {"role": "system", "content": (
            f"Nemis tili suhbat imtihon tekshiruvchisi sifatida talabaning rol o'yinini baholang. "
            f"Vaziyat: {topic_label}. Daraja: {level.upper()}.\n"
            f"Format:\n⭐ BAL: /10\n✅ YAXSHI:\n❌ XATOLAR:\n💡 MASLAHAT:"
        )},
        {"role": "user", "content": f"Talaba: {combined}"},
    ])

    try:
        from database import get_db
        db = get_db()
        db.add_xp(user_id, 50, "roleplay_complete", topic_label)
    except Exception:
        pass

    result_text = (
        f"🎭 *Roleplay Yakunlandi\\!*\n\n"
        f"📌 *Vaziyat:* {esc_md(topic_label)}\n\n"
        f"{esc_md(eval_result)}\n\n"
        f"🎁 *\\+50 XP* qo'shildi\\!"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yana o'ynash", callback_data="ai_roleplay")],
        [InlineKeyboardButton("🤖 AI Mentor", callback_data="ai_mentor_menu")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])

    if edit_func:
        await edit_func(result_text, parse_mode="MarkdownV2", reply_markup=keyboard)
    elif update.message:
        await update.message.reply_text(result_text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return ROLEPLAY_RESULT
