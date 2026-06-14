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
VORSTELLEN_MENU = 120
VORSTELLEN_Q1 = 121
VORSTELLEN_FOLLOWUP = 122
VORSTELLEN_RESULT = 123

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

VORSTELLEN_TOPICS = [
    "ism, yosh va kelib chiqish",
    "kasb va ta'lim",
    "qiziqishlar va hobbilar",
    "oila va do'stlar",
    "kundalik hayot va reja",
]

VORSTELLEN_EXAMPLES = {
    "a1": "Ich heiße [Ism]. Ich bin [yosh] Jahre alt. Ich komme aus Usbekistan.",
    "a2": "Ich heiße [Ism], ich bin [yosh] Jahre alt und komme aus Usbekistan. Ich arbeite als [kasb].",
    "b1": "Mein Name ist [Ism]. Ich bin [yosh] Jahre alt und stamme aus Usbekistan. Beruflich bin ich [kasb] und interessiere mich für [qiziqish].",
    "b2": "Gestatten Sie mir, mich kurz vorzustellen: Ich heiße [Ism], bin [yosh] Jahre alt und komme ursprünglich aus Usbekistan...",
    "c1": "Darf ich mich vorstellen? Mein Name ist [Ism]. Ich bin gebürtiger Usbeke/Usbeki und lebe seit einigen Jahren in Deutschland...",
}


async def vorstellen_start_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen modulini boshlash"""
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
    context.user_data["vs_history"] = []
    context.user_data["vs_round"] = 0

    example = VORSTELLEN_EXAMPLES.get(level, VORSTELLEN_EXAMPLES["a1"])

    await query.edit_message_text(
        f"👤 *O'zini Tanishtirish — Vorstellen*\n\n"
        f"📊 Darajangiz: *{level.upper()}*\n\n"
        f"Nemis tilida o'zingizni tanishtiring!\n\n"
        f"💡 *Namuna ({level.upper()}):*\n_{esc_md(example)}_\n\n"
        f"Endi o'zingiz yozing yoki gapirib yuboring 🎤",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💡 Maslahat ko'rish", callback_data="vorstellen_hint")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="ai_mentor_menu")],
        ]),
    )
    return VORSTELLEN_MENU


async def vorstellen_process_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen jarayonini boshqarish"""

    # Callback tugmasi bosilgan bo'lsa
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "vorstellen_hint":
            level = context.user_data.get("vs_level", "a1")
            example = VORSTELLEN_EXAMPLES.get(level, VORSTELLEN_EXAMPLES["a1"])
            await query.answer(f"💡 Namuna: {example[:100]}", show_alert=True)
            return VORSTELLEN_MENU

        elif data == "vorstellen_new":
            context.user_data["vs_history"] = []
            context.user_data["vs_round"] = 0
            return await vorstellen_start_new(update, context)

        elif data == "vorstellen_deeper":
            # Yangi savol berish
            history = context.user_data.get("vs_history", [])
            level = context.user_data.get("vs_level", "a1")
            round_num = context.user_data.get("vs_round", 0) + 1
            context.user_data["vs_round"] = round_num

            if round_num > len(VORSTELLEN_TOPICS):
                return await _vorstellen_final_result(query, context)

            topic = VORSTELLEN_TOPICS[round_num - 1] if round_num <= len(VORSTELLEN_TOPICS) else "umumiy"

            loading = await query.edit_message_text("⏳ *AI savol tayyorlamoqda...*", parse_mode="MarkdownV2")

            ai_question = await groq_chat([
                {"role": "system", "content": (
                    f"Siz nemis tili o'qituvchisisiz. Talaba darajasi: {level.upper()}. "
                    f"Vorstellen mashqi uchun '{topic}' mavzusida nemis tilida bitta savol bering. "
                    f"Savoldan keyin o'zbek tilidagi tarjimani qo'shing. "
                    f"Qisqa va aniq savollar bering."
                )},
                {"role": "user", "content": f"Suhbat tarixi: {json.dumps(history[-4:], ensure_ascii=False)}"},
            ])

            await query.edit_message_text(
                f"🗣️ *Suhbat — {round_num}/{len(VORSTELLEN_TOPICS)} savol*\n\n"
                f"🤖 *AI:* {esc_md(ai_question)}\n\n"
                f"Javob yozing yoki gapirib yuboring 🎤",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="vorstellen_skip")],
                    [InlineKeyboardButton("🏁 Yakunlash", callback_data="vorstellen_finish")],
                ]),
            )
            return VORSTELLEN_FOLLOWUP

        elif data == "vorstellen_skip":
            context.user_data["vs_round"] = context.user_data.get("vs_round", 0) + 1
            return await _vorstellen_final_result(query, context)

        elif data == "vorstellen_finish":
            return await _vorstellen_final_result(query, context)

        return VORSTELLEN_MENU

    # Matn yoki ovoz xabari
    elif update.message:
        text = update.message.text.strip() if update.message.text else ""

        if not text:
            await update.message.reply_text("❗ Iltimos matn yuboring yoki ovoz xabarini yuboring.")
            return VORSTELLEN_MENU

        history = context.user_data.get("vs_history", [])
        level = context.user_data.get("vs_level", "a1")
        round_num = context.user_data.get("vs_round", 0)

        history.append({"role": "user", "content": text})
        context.user_data["vs_history"] = history

        loading = await update.message.reply_text("⏳ *AI tahlil qilmoqda...*", parse_mode="MarkdownV2")

        # AI javob
        ai_response = await groq_chat([
            {"role": "system", "content": (
                f"Siz nemis tili o'qituvchisisiz. Talaba darajasi: {level.upper()}. "
                f"Talaba o'zini nemis tilida tanishtirmoqda. "
                f"1) Xatolarini tuzating (bo'lsa), 2) Yaxshi tomonlarini maqtang, "
                f"3) Kengaytirish uchun bitta savol bering. "
                f"O'zbek va nemis tillarida javob bering. Qisqa va ragbatlantiruvchi bo'ling."
            )},
            {"role": "user", "content": text},
        ])

        history.append({"role": "assistant", "content": ai_response})
        context.user_data["vs_history"] = history

        try:
            await loading.delete()
        except Exception:
            pass

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Davom etish", callback_data="vorstellen_deeper")],
            [InlineKeyboardButton("🔄 Yangidan boshlash", callback_data="vorstellen_new")],
            [InlineKeyboardButton("🏁 Yakunlash", callback_data="vorstellen_finish")],
        ])

        if round_num == 0:
            context.user_data["vs_round"] = 1

        await update.message.reply_text(
            f"🤖 *AI Mentor:*\n\n{esc_md(ai_response)}",
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )

        # XP berish
        try:
            from database import get_db
            db = get_db()
            db.add_xp(update.effective_user.id, 15, "vorstellen", text[:50])
        except Exception:
            pass

        return VORSTELLEN_FOLLOWUP

    return VORSTELLEN_MENU


async def _vorstellen_final_result(query, context):
    """Vorstellen yakuniy natija"""
    history = context.user_data.get("vs_history", [])
    level = context.user_data.get("vs_level", "a1")

    if not history:
        await query.edit_message_text(
            "⚠️ Hech narsa yozilmadi. Qayta urinib ko'ring!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Qayta boshlash", callback_data="ai_vorstellen")],
                [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
            ]),
        )
        return VORSTELLEN_RESULT

    user_texts = [m["content"] for m in history if m["role"] == "user"]
    combined = " ".join(user_texts)

    loading = await query.edit_message_text("⏳ *Yakuniy tahlil tayyorlanmoqda...*", parse_mode="MarkdownV2")

    final_eval = await groq_chat([
        {"role": "system", "content": (
            f"Siz nemis tili imtihon tekshiruvchisisiz. Talaba darajasi: {level.upper()}. "
            f"Talabaning butun vorstellen mashqini baholang. "
            f"Format:\n"
            f"⭐ BAL: [1-10]\n"
            f"✅ YAXSHI: [2-3 narsa]\n"
            f"❌ XATOLAR: [asosiy xatolar]\n"
            f"💡 MASLAHAT: [keyingi mashq uchun]"
        )},
        {"role": "user", "content": f"Talabaning yozganlari:\n{combined}"},
    ])

    # XP berish
    try:
        from database import get_db
        db = get_db()
        db.add_xp(query.from_user.id, 50, "vorstellen_complete", "Vorstellen yakunlandi")
    except Exception:
        pass

    await query.edit_message_text(
        f"🎉 *Vorstellen Yakunlandi\\!*\n\n"
        f"{esc_md(final_eval)}\n\n"
        f"🎁 *\\+50 XP* qo'shildi\\!",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yana mashq qilish", callback_data="ai_vorstellen")],
            [InlineKeyboardButton("🤖 AI Mentor", callback_data="ai_mentor_menu")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ]),
    )
    return VORSTELLEN_RESULT


async def vs_show_section_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    section = query.data.replace("vs_show_", "")
    await query.answer(f"📄 {section} ko'rsatilmoqda", show_alert=True)
    return VORSTELLEN_RESULT


async def vs_speak_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("🔊 Ovoz funksiyasi", show_alert=True)
    return VORSTELLEN_RESULT


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
