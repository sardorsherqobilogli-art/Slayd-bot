#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - AI Mentor Moduli
Daraja aniqlash, Vorstellen, Erfahrungen, Xato banki, Ovozli lug'at, Rolli o'yinlar
"""

import json
import random
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    logger, GROQ_API_KEY, GROQ_API_URL, DEFAULT_AI_MODEL,
    LEVEL_DETECTION_QUESTIONS, VORSTELLEN_PROMPTS, ERFAHRUNGEN_TOPICS,
    ROLEPLAY_SCENARIOS, VOICE_VOCAB_CATEGORIES, XP_REWARDS, LEVEL_LABELS,
)
from database import get_db
from voice_engine import speak_text, listen_to_voice, analyze_pronunciation

# ==================== STATES ====================
(
    AI_MENTOR_MENU,
    LEVEL_DETECT_Q1, LEVEL_DETECT_Q2, LEVEL_DETECT_Q3, LEVEL_DETECT_Q4, LEVEL_DETECT_Q5,
    LEVEL_DETECT_RESULT,
    VORSTELLEN_START, VORSTELLEN_FOLLOWUP, VORSTELLEN_RESULT,
    ERFAHRUNGEN_MENU, ERFAHRUNGEN_TOPIC, ERFAHRUNGEN_DIFFICULTY, ERFAHRUNGEN_CHAT, ERFAHRUNGEN_RESULT,
    MISTAKE_BANK_MENU, MISTAKE_REVIEW, MISTAKE_MINILESSON, MISTAKE_PRACTICE,
    VOICE_VOCAB_MENU, VOICE_VOCAB_CATEGORY, VOICE_VOCAB_PRACTICE, VOICE_VOCAB_RESULT,
    ROLEPLAY_MENU, ROLEPLAY_SCENARIO, ROLEPLAY_CHAT, ROLEPLAY_RESULT,
    AI_MENTOR_SETTINGS,
) = range(15, 43)


# ==================== GROQ AI HELPER ====================

async def groq_chat(messages: list, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """Groq LLM orqali suhbat"""
    if not GROQ_API_KEY:
        return "❌ AI xizmati vaqtincha mavjud emas."

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEFAULT_AI_MODEL,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                },
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Groq chat xatosi: {e}")
        return "❌ AI javobida xato yuz berdi. Qayta urinib ko'ring."


async def groq_json(messages: list, max_tokens: int = 1024) -> dict:
    """Groq dan JSON formatida javob olish"""
    if not GROQ_API_KEY:
        return {"error": "AI xizmati o'chirilgan"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEFAULT_AI_MODEL,
                    "max_tokens": max_tokens,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            result = data["choices"][0]["message"]["content"]
            return json.loads(result)
    except Exception as e:
        logger.error(f"Groq JSON xatosi: {e}")
        return {"error": str(e)}


def esc_md(text: str) -> str:
    """MarkdownV2 escape"""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ==================== KEYBOARDS ====================

def ai_mentor_menu_keyboard():
    """AI Mentor asosiy menyusi"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Darajani aniqlash", callback_data="ai_level_detect")],
        [InlineKeyboardButton("🎤 Vorstellen (Taqdimot)", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("💬 Erfahrungen (B2/C1)", callback_data="ai_erfahrungen")],
        [InlineKeyboardButton("🔧 Mening xato bankim", callback_data="ai_mistake_bank")],
        [InlineKeyboardButton("🎙️ Ovozli lug'at", callback_data="ai_voice_vocab")],
        [InlineKeyboardButton("🎭 Rolli o'yinlar", callback_data="ai_roleplay")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])


def difficulty_keyboard(topic_key: str):
    """Erfahrungen qiyinlik darajasi"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 Oddiy", callback_data=f"erf_diff_{topic_key}_easy"),
            InlineKeyboardButton("🟡 O'rta", callback_data=f"erf_diff_{topic_key}_medium"),
            InlineKeyboardButton("🔴 Qiyin", callback_data=f"erf_diff_{topic_key}_hard"),
        ],
        [InlineKeyboardButton("↩️ Mavzularga qaytish", callback_data="ai_erfahrungen")],
    ])


def roleplay_scenarios_keyboard():
    """Rolli o'yin senariyalari"""
    rows = []
    for key, scenario in ROLEPLAY_SCENARIOS.items():
        rows.append([InlineKeyboardButton(
            scenario["name"],
            callback_data=f"rp_select_{key}"
        )])
    rows.append([InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")])
    return InlineKeyboardMarkup(rows)


def voice_vocab_categories_keyboard():
    """Ovozli lug'at kategoriyalari"""
    rows = []
    for key, name in VOICE_VOCAB_CATEGORIES.items():
        rows.append([InlineKeyboardButton(
            name,
            callback_data=f"vv_cat_{key}"
        )])
    rows.append([InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")])
    return InlineKeyboardMarkup(rows)


# ==================== 1. LEVEL DETECTION ====================

async def level_detect_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja aniqlashni boshlash"""
    query = update.callback_query
    await query.answer()

    context.user_data["level_detect"] = {
        "answers": [],
        "hints_used": [],
        "current_q": 0,
    }

    question = LEVEL_DETECTION_QUESTIONS[0]
    text = (
        f"🎯 *Darajani aniqlash* \\(5 ta savol\\)\n\n"
        f"{question['question']}\n\n"
        f"💡 *Yordam uchun:* `Yordam` deb yozing\n"
        f"📝 Javobingizni yozib yuboring:\\!"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="level_skip_0")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ])
    )
    return LEVEL_DETECT_Q1


async def level_detect_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja aniqlash savolini qayta ishlash"""
    user_data = context.user_data.get("level_detect", {})
    q_idx = user_data.get("current_q", 0)

    # Agar callback bo'lsa (o'tkazib yuborish)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data.startswith("level_skip_"):
            user_data["answers"].append({"skipped": True, "correct": False})
            q_idx += 1
            user_data["current_q"] = q_idx

            if q_idx >= len(LEVEL_DETECTION_QUESTIONS):
                return await level_detect_result(query, context)

            question = LEVEL_DETECTION_QUESTIONS[q_idx]
            await query.edit_message_text(
                f"🎯 *Savol {q_idx + 1}/5*\n\n{question['question']}\n\n"
                f"📝 Javobingizni yozib yuboring:",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"level_skip_{q_idx}")],
                    [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
                ])
            )
            return LEVEL_DETECT_Q1 + q_idx

    # Matnli javob
    text = update.message.text.strip()

    # Yordam so'rash
    if text.lower() in ["yordam", "help", "?"]:
        question = LEVEL_DETECTION_QUESTIONS[q_idx]
        hints = "\n".join([f"💡 {h}" for h in question.get("hints", [])])
        user_data["hints_used"].append(q_idx)
        await update.message.reply_text(
            f"🎯 *Savol {q_idx + 1}/5*\n\n"
            f"{question['question']}\n\n"
            f"*Yordam:*\n{hints}\n\n"
            f"📝 Endi javobingizni yozib yuboring:",
            parse_mode="MarkdownV2",
        )
        return LEVEL_DETECT_Q1 + q_idx

    # Javobni tekshirish
    question = LEVEL_DETECTION_QUESTIONS[q_idx]
    is_correct = question["check"](text)

    user_data["answers"].append({
        "answer": text,
        "correct": is_correct,
        "skipped": False,
    })

    if is_correct:
        await update.message.reply_text("✅ *To'g'ri\\!*", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(
            f"❌ *Noto'g'ri*\n\nJavobingiz: *{esc_md(text)}*\n\nKeyingi savolga o'tamiz\\...",
            parse_mode="MarkdownV2"
        )

    q_idx += 1
    user_data["current_q"] = q_idx

    if q_idx >= len(LEVEL_DETECTION_QUESTIONS):
        return await level_detect_text_result(update, context)

    # Keyingi savol
    question = LEVEL_DETECTION_QUESTIONS[q_idx]
    await update.message.reply_text(
        f"🎯 *Savol {q_idx + 1}/5*\n\n{question['question']}\n\n"
        f"💡 Yordam uchun: `Yordam` deb yozing\n"
        f"📝 Javobingizni yozib yuboring:",
        parse_mode="MarkdownV2",
    )
    return LEVEL_DETECT_Q1 + q_idx


async def level_detect_result(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja aniqlash natijasi (callback orqali)"""
    user_data = context.user_data.get("level_detect", {})
    answers = user_data.get("answers", [])
    correct_count = sum(1 for a in answers if a.get("correct", False))

    # Darajani aniqlash
    if correct_count <= 1:
        level = "a1"
    elif correct_count <= 2:
        level = "a2"
    elif correct_count <= 3:
        level = "b1"
    elif correct_count <= 4:
        level = "b2"
    else:
        level = "c1"

    user_id = query.from_user.id
    db = get_db()
    db.update_user(user_id, current_level=level)

    text = (
        f"🎯 *Daraja aniqlash natijasi*\n\n"
        f"✅ To'g'ri: {correct_count}/5\n"
        f"💡 Yordam: {len(user_data.get('hints_used', []))} ta\n\n"
        f"📊 *Sizning darajangiz: {LEVEL_LABELS.get(level, level)}*\n\n"
    )

    # Daraja tavsifi
    level_desc = {
        "a1": "Boshlang'ich daraja. A1 kitoblari va lektsiyalaridan boshlang! 📚",
        "a2": "Elementar daraja. Asosiy grammatikani mustahkamlang! 📖",
        "b1": "O'rta daraja. Muloqot va murakkab mavzularni o'rganing! 💬",
        "b2": "Yuqori o'rta daraja. Akademik va professional nemis tiliga o'ting! 🎓",
        "c1": "Yuqori daraja. Professional va ilmiy darajada erkin muloqot! 🏆",
    }
    text += level_desc.get(level, "")

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU


async def level_detect_text_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja aniqlash natijasi (matn orqali)"""
    user_data = context.user_data.get("level_detect", {})
    answers = user_data.get("answers", [])
    correct_count = sum(1 for a in answers if a.get("correct", False))

    if correct_count <= 1:
        level = "a1"
    elif correct_count <= 2:
        level = "a2"
    elif correct_count <= 3:
        level = "b1"
    elif correct_count <= 4:
        level = "b2"
    else:
        level = "c1"

    user_id = update.effective_user.id
    db = get_db()
    db.update_user(user_id, current_level=level)

    level_desc = {
        "a1": "Boshlang'ich daraja. A1 kitoblari va lektsiyalaridan boshlang! 📚",
        "a2": "Elementar daraja. Asosiy grammatikani mustahkamlang! 📖",
        "b1": "O'rta daraja. Muloqot va murakkab mavzularni o'rganing! 💬",
        "b2": "Yuqori o'rta daraja. Akademik va professional nemis tiliga o'ting! 🎓",
        "c1": "Yuqori daraja. Professional va ilmiy darajada erkin muloqot! 🏆",
    }

    await update.message.reply_text(
        f"🎯 *Daraja aniqlash natijasi*\n\n"
        f"✅ To'g'ri: {correct_count}/5\n"
        f"💡 Yordam: {len(user_data.get('hints_used', []))} ta\n\n"
        f"📊 *Sizning darajangiz: {LEVEL_LABELS.get(level, level)}*\n\n"
        f"{level_desc.get(level, '')}",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU


# ==================== 2. VORSTELLEN ====================

async def vorstellen_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen (taqdimot) boshlash"""
    query = update.callback_query
    await query.answer()

    context.user_data["vorstellen"] = {
        "messages": [],
        "step": 0,
    }

    text = (
        "🎤 *Vorstellen \\- O'zingizni taqdim etish*\n\n"
        "Men sizga 3 ta savol beraman\! Nemis yoki o'zbek tilida javob bering\!\n\n"
        "*1\-savol:*\n"
        "Stellen Sie sich vor\\! \(O'zingizni taqdim eting\\!\)\n\n"
        "Ismingiz, yoshingiz, qayerdanligingiz, nima ish qilishingiz haqida ayting\!"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎙️ Ovozda javob", callback_data="vorstellen_voice")],
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="ai_mentor_menu")],
        ])
    )
    return VORSTELLEN_START


async def vorstellen_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen javobini qayta ishlash"""
    v_data = context.user_data.get("vorstellen", {"step": 0, "messages": []})
    step = v_data["step"]

    # Ovozli javob
    if update.callback_query and update.callback_query.data == "vorstellen_voice":
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🎙️ *Ovozli javob rejimi*\n\n"
            "Nemischa gapiring va men tahlil qilaman!",
            parse_mode="MarkdownV2",
        )
        return VORSTELLEN_START

    # Matnli javob
    if update.message and update.message.text:
        user_text = update.message.text.strip()
    else:
        return VORSTELLEN_START

    v_data["messages"].append({"role": "user", "content": user_text})
    step += 1

    if step >= 3:
        # Natija - AI tahlil
        return await vorstellen_result(update, context, v_data)

    # Keyingi savol
    follow_up = VORSTELLEN_PROMPTS["follow_up"][min(step - 1, len(VORSTELLEN_PROMPTS["follow_up"]) - 1)]
    v_data["step"] = step

    await update.message.reply_text(
        f"✅ *Juda yaxshi\\!*\n\n*Savol {step + 1}/3:*\n{esc_md(follow_up)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="vorstellen_finish")],
        ])
    )
    return VORSTELLEN_START


async def vorstellen_result(update: Update, context: ContextTypes.DEFAULT_TYPE, v_data: dict) -> int:
    """Vorstellen natijasi - AI tahlil"""
    await update.message.reply_text("🧠 *AI tahlil qilmoqda\\.\\.\\.*", parse_mode="MarkdownV2")

    messages = [
        {"role": "system", "content": (
            "Siz nemis tili o'qituvchisisiz. Foydalanuvchi o'zini taqdim etdi. "
            "Quyidagi formatda tahlil bering (faqat JSON):\n"
            "{\n"
            "  'score': 0-10 (umumiy ball),\n"
            "  'grammar_errors': ['xato 1', 'xato 2'],\n"
            "  'vocabulary_score': 0-10,\n"
            "  'fluency_score': 0-10,\n"
            "  'feedback': 'batafsil tahlil ozbek tilida',\n"
            "  'improvements': ['tavsiya 1', 'tavsiya 2']\n"
            "}"
        )},
        {"role": "user", "content": f"Foydalanuvchi gaplari:\n" + "\n".join([m["content"] for m in v_data["messages"]])},
    ]

    result = await groq_json(messages, max_tokens=2048)

    if "error" in result:
        await update.message.reply_text(
            "❌ Tahlilda xato yuz berdi.\n\nKeyinroq qayta urinib ko'ring.",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    score = result.get("score", 5)
    feedback = result.get("feedback", "Yaxshi urinish!")
    grammar_errors = result.get("grammar_errors", [])
    improvements = result.get("improvements", [])

    # Speaking score ni saqlash
    user_id = update.effective_user.id
    db = get_db()
    db.add_speaking_score(
        user_id=user_id,
        session_type="vorstellen",
        topic="self_introduction",
        score=score,
        feedback=feedback,
        words_used=", ".join([m["content"] for m in v_data["messages"]]),
        grammar_errors="\n".join(grammar_errors),
    )

    # XP berish
    db.add_xp(user_id, XP_REWARDS["voice_practice"], "vorstellen", f"Ball: {score}/10")

    grammar_text = "\n".join([f"• {e}" for e in grammar_errors]) if grammar_errors else "✅ Grammatik xatolar kam"
    improve_text = "\n".join([f"💡 {i}" for i in improvements]) if improvements else ""

    await update.message.reply_text(
        f"🎤 *Vorstellen natijasi*\n\n"
        f"⭐ *Ball: {score}/10*\n"
        f"📚 *So'z boyligi: {result.get('vocabulary_score', 5)}/10*\n"
        f"🗣️ *Suvliklik: {result.get('fluency_score', 5)}/10*\n\n"
        f"*Tahlil:*\n{esc_md(feedback)}\n\n"
        f"*Grammatik xatolar:*\n{esc_md(grammar_text)}\n\n"
        f"*Yaxshilash uchun:*\n{esc_md(improve_text)}\n\n"
        f"🎁 *+{XP_REWARDS['voice_practice']} XP*",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU


# ==================== 3. ERFAHRUNGEN ====================

async def erfahrungen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Erfahrungen mavzulari menyusi"""
    query = update.callback_query
    await query.answer()

    # Faqat B2/C1 foydalanuvchilariga
    user_id = query.from_user.id
    db = get_db()
    user = db.get_or_create_user(user_id)
    level = user.get("current_level", "a1")

    if level in ["a1", "a2", "b1"]:
        await query.edit_message_text(
            f"💬 *Erfahrungen* faqat *B2 va C1* darajalarida mavjud\\!\n\n"
            f"Sizning darajangiz: {esc_md(LEVEL_LABELS.get(level, level))}\n\n"
            f"Avval darajangizni oshiring! 📚",
            parse_mode="MarkdownV2",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    # Mavzular ro'yxati
    text = "💬 *Erfahrungen \\- Mavzu Laboratoriyasi*\n\nMavzu tanlang:\n"
    for key, topic in ERFAHRUNGEN_TOPICS.items():
        text += f"\n{topic['name']}"

    rows = []
    for key, topic in ERFAHRUNGEN_TOPICS.items():
        rows.append([InlineKeyboardButton(
            topic["name"],
            callback_data=f"erf_topic_{key}"
        )])
    rows.append([InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")])

    await query.edit_message_text(
        "💬 *Erfahrungen \\- Mavzu Laboratoriyasi*\n\n"
        "*10 ta mavzu, 3 ta qiyinlik darajasi*\n\n"
        "🟢 *Oddiy* \\- oddiy savollar\n"
        "🟡 *O'rta* \\- muhokama savollari\n"
        "🔴 *Qiyin* \\- akademik munozara\n\n"
        "Mavzu tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return ERFAHRUNGEN_MENU


async def erfahrungen_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Erfahrungen mavzuni tanlash - qiyinlik darajasi"""
    query = update.callback_query
    await query.answer()

    topic_key = query.data.replace("erf_topic_", "")
    context.user_data["erfahrungen_topic"] = topic_key

    topic = ERFAHRUNGEN_TOPICS.get(topic_key)
    if not topic:
        return ERFAHRUNGEN_MENU

    await query.edit_message_text(
        f"{topic['name']}\n\n"
        f"Qiyinlik darajasini tanlang:\n\n"
        f"🟢 *Oddiy:* {esc_md(topic['easy'])}\n\n"
        f"🟡 *O'rta:* {esc_md(topic['medium'])}\n\n"
        f"🔴 *Qiyin:* {esc_md(topic['hard'])}",
        parse_mode="MarkdownV2",
        reply_markup=difficulty_keyboard(topic_key),
    )
    return ERFAHRUNGEN_DIFFICULTY


async def erfahrungen_start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Erfahrungen suhbatini boshlash"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    topic_key = parts[2]
    difficulty = parts[3]

    topic = ERFAHRUNGEN_TOPICS.get(topic_key)
    question = topic.get(difficulty, topic["easy"]) if topic else "Erzählen Sie von sich."

    context.user_data["erfahrungen"] = {
        "topic": topic_key,
        "difficulty": difficulty,
        "messages": [],
        "turns": 0,
    }

    # AI dan boshlang'ich javob
    system_prompt = (
        f"Sie sind ein deutscher Sprachlehrer für B2/C1 Niveau. "
        f"Das Thema ist: {topic['name'] if topic else 'Allgemein'}. "
        f"Stellen Sie eine folgende Frage und geben Sie dann Feedback. "
        f"Sprechen Sie Deutsch, aber erklären Sie komplexe Punkte auf Uzbekisch. "
        f"Seien Sie streng, aber ermutigend. Bewerten Sie Grammatik, Wortschatz und Flüssigkeit."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Mavzu: {topic_key}, Qiyinlik: {difficulty}\n\nSavol: {question}"},
    ]

    ai_response = await groq_chat(messages, max_tokens=2048)

    context.user_data["erfahrungen"]["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": ai_response},
    ]

    await query.edit_message_text(
        f"💬 *Erfahrungen: {esc_md(topic['name'] if topic else 'Mavzu')}*\n"
        f"Qiyinlik: {difficulty.upper()}\n\n"
        f"📝 *Savol:*\n{esc_md(question)}\n\n"
        f"{esc_md(ai_response)}\n\n"
        f"*Javobingizni yozing!* (yoki 🎙️ ovozli yuboring)",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="erf_finish")],
        ])
    )
    return ERFAHRUNGEN_CHAT


async def erfahrungen_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Erfahrungen suhbat davomi"""
    erf_data = context.user_data.get("erfahrungen", {})
    turns = erf_data.get("turns", 0)

    if update.callback_query and update.callback_query.data == "erf_finish":
        return await erfahrungen_result(update, context)

    # Foydalanuvchi xabari
    if update.message and update.message.text:
        user_message = update.message.text.strip()
    else:
        return ERFAHRUNGEN_CHAT

    erf_data["messages"].append({"role": "user", "content": user_message})
    turns += 1
    erf_data["turns"] = turns

    if turns >= 5:
        return await erfahrungen_result(update, context)

    # AI javobi
    messages = erf_data["messages"][:]  # Copy
    messages.append({
        "role": "user",
        "content": f"Foydalanuvchi javobi ({turns}/5 almashinuv):\n{user_message}\n\n"
                   f"Keyingi savol bering yoki tahlil qiling. Faqat 1 ta savol!"
    })

    ai_response = await groq_chat(messages, max_tokens=2048)
    erf_data["messages"].append({"role": "assistant", "content": ai_response})

    await update.message.reply_text(
        f"{esc_md(ai_response)}\n\n"
        f"*({turns}/5)* \\-> Javobingizni yozing:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="erf_finish")],
        ])
    )
    return ERFAHRUNGEN_CHAT


async def erfahrungen_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Erfahrungen natijasi"""
    erf_data = context.user_data.get("erfahrungen", {})
    messages = erf_data.get("messages", [])
    turns = erf_data.get("turns", 0)

    await (update.callback_query.edit_message_text if update.callback_query
           else update.message.reply_text)(
        "🧠 *AI yakuniy tahlil qilmoqda\\.\\.\\.*",
        parse_mode="MarkdownV2"
    )

    # AI dan yakuniy tahlil
    analysis_messages = messages + [{
        "role": "user",
        "content": (
            "Suhbat tugadi. Quyidagi formatda yakuniy tahlil bering (faqat JSON):\n"
            "{\n"
            "  'score': 0-10,\n"
            "  'grammar_score': 0-10,\n"
            "  'vocabulary_score': 0-10,\n"
            "  'fluency_score': 0-10,\n"
            "  'feedback': 'batafsil tahlil ozbek tilida',\n"
            "  'good_points': ['yaxshi jihat 1', 'yaxshi jihat 2'],\n"
            "  'improvements': ['tavsiya 1', 'tavsiya 2']\n"
            "}"
        )
    }]

    result = await groq_json(analysis_messages, max_tokens=2048)

    user_id = (update.callback_query.from_user.id if update.callback_query
               else update.effective_user.id)
    db = get_db()

    score = result.get("score", 5)
    db.add_speaking_score(
        user_id=user_id,
        session_type="erfahrungen",
        topic=erf_data.get("topic", ""),
        score=score,
        feedback=result.get("feedback", ""),
        duration_seconds=turns * 60,
    )
    db.add_xp(user_id, XP_REWARDS["ai_conversation"], "erfahrungen", f"Ball: {score}/10")

    good_points = "\n".join([f"✅ {p}" for p in result.get("good_points", [])])
    improvements = "\n".join([f"💡 {i}" for i in result.get("improvements", [])])

    text = (
        f"🏁 *Erfahrungen natijasi*\n\n"
        f"⭐ *Umumiy ball: {score}/10*\n"
        f"📚 *Grammatika: {result.get('grammar_score', 5)}/10*\n"
        f"🗣️ *So'z boyligi: {result.get('vocabulary_score', 5)}/10*\n"
        f"💬 *Suvliklik: {result.get('fluency_score', 5)}/10*\n\n"
        f"*Tahlil:*\n{esc_md(result.get('feedback', 'Yaxshi urinish!'))}\n\n"
        f"*Yaxshi jihatlar:*\n{esc_md(good_points)}\n\n"
        f"*Yaxshilash uchun:*\n{esc_md(improvements)}\n\n"
        f"🎁 *+{XP_REWARDS['ai_conversation']} XP*"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard()
        )
    return AI_MENTOR_MENU


# ==================== 4. MISTAKE BANK ====================

async def mistake_bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xato banki menyusi"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    stats = db.get_mistake_stats(user_id)

    text = (
        f"🔧 *Mening xato bankim*\n\n"
        f"❌ *Faol xatolar: {stats['active']}*\n"
        f"✅ *O'zlashtirilgan: {stats['mastered']}*\n"
        f"📊 *Jami: {stats['total']}*\n\n"
    )

    if stats["active"] > 0:
        text += "Xatolaringizni ko'rib chiqing va mini-darslarni o'ting! 📚"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Xatolar ro'yxati", callback_data="mistake_list")],
            [InlineKeyboardButton("🎲 Tasodifiy mini-dars", callback_data="mistake_random")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    else:
        text += "Ajoyib! Sizda faol xatolar yo'q! 🎉\n\n"
        text += "AI Mentor bilan suhbatlashishda xatolar avtomatik saqlanadi."
        keyboard = ai_mentor_menu_keyboard()

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return MISTAKE_BANK_MENU


async def mistake_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xatolar ro'yxati"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    mistakes = db.get_mistakes(user_id, mastered=False, limit=10)

    if not mistakes:
        await query.edit_message_text(
            "✅ *Barcha xatolar o'zlashtirilgan!*\n\nAjoyib ish! 🎉",
            parse_mode="MarkdownV2",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    text = "🔧 *Sizning xatolarингiz:*\n\n"
    keyboard_rows = []
    for i, m in enumerate(mistakes[:5], 1):
        text += f"{i}\. *{esc_md(m['user_input'])}* \\→ {esc_md(m['correct_form'])}\n"
        text += f"   Turi: {esc_md(m['mistake_type'])}\n\n"
        keyboard_rows.append([InlineKeyboardButton(
            f"{i}. {m['user_input'][:20]}... → Mini-dars",
            callback_data=f"mistake_lesson_{m['id']}"
        )])

    keyboard_rows.append([InlineKeyboardButton("↩️ Xato bankiga qaytish", callback_data="ai_mistake_bank")])
    keyboard_rows.append([InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")])

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard_rows))
    return MISTAKE_BANK_MENU


async def mistake_mini_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xato bo'yicha mini-dars"""
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_lesson_", ""))
    db = get_db()
    mistake = db.get_mistake_by_id(mistake_id)

    if not mistake:
        await query.edit_message_text(
            "❌ Xato topilmadi.",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    context.user_data["current_mistake_id"] = mistake_id

    # Mini-dars matni
    lesson_text = mistake.get("mini_lesson", "")
    if not lesson_text:
        # AI dan mini-dars yaratish
        prompt = f"""Xato: "{mistake['user_input']}" 
To'g'ri: "{mistake['correct_form']}" 
Turi: {mistake['mistake_type']}

Quyidagi formatda mini-dars bering (faqat JSON):
{{
    "rule": "grammatik qoida (nemischa)",
    "explanation": "tushuntirish (o'zbek tilida)",
    "example_correct": "3 ta to'g'ri misol",
    "example_wrong": "3 ta noto'g'ri misol", 
    "tip": "xotirada saqlash uchun maslahat"
}}"""

        result = await groq_json([
            {"role": "system", "content": "Siz nemis tili grammatika o'qituvchisisiz."},
            {"role": "user", "content": prompt},
        ], max_tokens=1024)

        lesson_text = (
            f"📚 *Grammatik qoida:*\n{result.get('rule', 'N/A')}\n\n"
            f"📝 *Tushuntirish:*\n{result.get('explanation', 'N/A')}\n\n"
            f"✅ *To'g'ri misollar:*\n{result.get('example_correct', 'N/A')}\n\n"
            f"❌ *Noto'g'ri misollar:*\n{result.get('example_wrong', 'N/A')}\n\n"
            f"💡 *Maslahat:*\n{result.get('tip', 'N/A')}"
        )

        # Saqlash
        db._connect().__enter__().cursor().execute(
            "UPDATE mistakes SET mini_lesson = ? WHERE id = ?",
            (lesson_text, mistake_id)
        )

    await query.edit_message_text(
        f"🔧 *Mini-dars*\n\n"
        f"❌ *Sizning xato: {esc_md(mistake['user_input'])}*\n"
        f"✅ *To'g'ri: {esc_md(mistake['correct_form'])}*\n"
        f"📌 *Turi: {esc_md(mistake['mistake_type'])}*\n\n"
        f"{esc_md(lesson_text)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Mashqlarni bajarish", callback_data=f"mistake_practice_{mistake_id}")],
            [InlineKeyboardButton("✅ O'zlashtirdim", callback_data=f"mistake_master_{mistake_id}")],
            [InlineKeyboardButton("↩️ Xatolar ro'yxati", callback_data="mistake_list")],
        ])
    )
    return MISTAKE_MINILESSON


async def mistake_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xato bo'yicha mashqlar"""
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_practice_", ""))
    db = get_db()
    mistake = db.get_mistake_by_id(mistake_id)

    if not mistake:
        return MISTAKE_BANK_MENU

    # AI dan 3 ta mashq yaratish
    prompt = f"""Xato: "{mistake['user_input']}" → To'g'ri: "{mistake['correct_form']}"
Turi: {mistake['mistake_type']}

3 ta mashq yarat (faqat JSON):
{{
    "exercises": [
        {{"task": "mashq matni", "answer": "javob"}},
        {{"task": "mashq matni", "answer": "javob"}},
        {{"task": "mashq matni", "answer": "javob"}}
    ]
}}"""

    result = await groq_json([
        {"role": "system", "content": "Siz nemis tili mashq yaratuvchisisiz."},
        {"role": "user", "content": prompt},
    ])

    exercises = result.get("exercises", [])
    if not exercises:
        exercises = [
            {"task": f"To'g'ri variantni tanlang: I ___ ein Buch.", "answer": "habe"},
            {"task": f"Gapni to'g'ri ayting: Men 25 yoshdaman", "answer": "Ich bin 25 Jahre alt."},
        ]

    context.user_data["mistake_exercises"] = {
        "exercises": exercises,
        "current": 0,
        "correct": 0,
        "mistake_id": mistake_id,
    }

    ex = exercises[0]
    await query.edit_message_text(
        f"✏️ *Mashq 1/{len(exercises)}*\n\n{esc_md(ex['task'])}\n\n"
        f"Javobingizni yozing:",
        parse_mode="MarkdownV2",
    )
    return MISTAKE_PRACTICE


async def mistake_practice_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mashqni qayta ishlash"""
    ex_data = context.user_data.get("mistake_exercises", {})
    current = ex_data.get("current", 0)
    exercises = ex_data.get("exercises", [])

    if not exercises or current >= len(exercises):
        return MISTAKE_BANK_MENU

    user_answer = update.message.text.strip()
    correct_answer = exercises[current].get("answer", "")

    is_correct = user_answer.lower() in correct_answer.lower() or correct_answer.lower() in user_answer.lower()

    if is_correct:
        ex_data["correct"] += 1
        await update.message.reply_text(f"✅ *To'g'ri!* {esc_md(correct_answer)}", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(
            f"❌ *Noto'g'ri*\nSiz: {esc_md(user_answer)}\nTo'g'ri: {esc_md(correct_answer)}",
            parse_mode="MarkdownV2"
        )

    current += 1
    ex_data["current"] = current

    if current >= len(exercises):
        # Barcha mashqlar tugadi
        correct_count = ex_data["correct"]
        total = len(exercises)
        mistake_id = ex_data["mistake_id"]

        db = get_db()
        db.review_mistake(mistake_id)
        db.add_xp(update.effective_user.id, XP_REWARDS["mistake_corrected"], "mistake_practice",
                  f"{correct_count}/{total} to'g'ri")

        if correct_count == total:
            db.master_mistake(mistake_id)
            await update.message.reply_text(
                f"🎉 *Barcha mashqlar bajarildi!* {correct_count}/{total}\n\n"
                f"✅ Bu xato o'zlashtirildi!\n\n"
                f"🎁 *+{XP_REWARDS['mistake_corrected']} XP*",
                reply_markup=ai_mentor_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                f"📊 *Natija: {correct_count}/{total}*\n\n"
                f"Yana mashq qilishingiz mumkin!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Qayta mashq", callback_data=f"mistake_practice_{mistake_id}")],
                    [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
                ])
            )
        return AI_MENTOR_MENU

    # Keyingi mashq
    ex = exercises[current]
    await update.message.reply_text(
        f"✏️ *Mashq {current + 1}/{len(exercises)}*\n\n{esc_md(ex['task'])}\n\n"
        f"Javobingizni yozing:",
        parse_mode="MarkdownV2",
    )
    return MISTAKE_PRACTICE


async def mistake_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xatoni o'zlashtirilgan deb belgilash"""
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_master_", ""))
    db = get_db()
    db.master_mistake(mistake_id)
    db.add_xp(query.from_user.id, XP_REWARDS["mistake_corrected"], "mistake_mastered")

    await query.edit_message_text(
        "✅ *Xato o'zlashtirildi!* 🎉\n\n"
        f"🎁 *+{XP_REWARDS['mistake_corrected']} XP*",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU


async def mistake_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tasodifiy mini-dars"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    mistakes = db.get_mistakes(user_id, mastered=False, limit=100)

    if not mistakes:
        await query.edit_message_text(
            "✅ *Barcha xatolar o'zlashtirilgan!*\n\nAjoyib ish! 🎉",
            parse_mode="MarkdownV2",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    # Tasodifiy xato tanlash
    mistake = random.choice(mistakes)
    context.user_data["current_mistake_id"] = mistake["id"]

    # Mini-dars yaratish
    prompt = f"""Xato: "{mistake['user_input']}" → To'g'ri: "{mistake['correct_form']}" 
Turi: {mistake['mistake_type']}

Qisqa mini-dars (faqat JSON):
{{
    "rule": "grammatik qoida (qisqa)",
    "explanation": "tushuntirish (o'zbek tilida, qisqa)",
    "tip": "xotirada saqlash uchun maslahat"
}}"""

    result = await groq_json([
        {"role": "system", "content": "Siz nemis tili o'qituvchisisiz."},
        {"role": "user", "content": prompt},
    ])

    await query.edit_message_text(
        f"🎲 *Tasodifiy mini-dars*\n\n"
        f"❌ *Xato: {esc_md(mistake['user_input'])}*\n"
        f"✅ *To'g'ri: {esc_md(mistake['correct_form'])}*\n\n"
        f"📚 *Qoida:*\n{esc_md(result.get('rule', 'N/A'))}\n\n"
        f"📝 *Tushuntirish:*\n{esc_md(result.get('explanation', 'N/A'))}\n\n"
        f"💡 *Maslahat:*\n{esc_md(result.get('tip', 'N/A'))}\n\n"
        f"🎁 *+{XP_REWARDS['mistake_corrected']} XP* olish uchun mashq qiling!",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Mashq qilish", callback_data=f"mistake_practice_{mistake['id']}")],
            [InlineKeyboardButton("✅ O'zlashtirdim", callback_data=f"mistake_master_{mistake['id']}")],
            [InlineKeyboardButton("🎲 Boshqa mini-dars", callback_data="mistake_random")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    )
    return MISTAKE_MINILESSON


# ==================== 5. VOICE VOCABULARY ====================

# Kategoriyalar bo'yicha so'zlar (A1 darajasi)
VOCAB_WORDS = {
    "alltag": [
        ("der Morgen", "ertalab"), ("der Tag", "kun"), ("die Nacht", "tun"),
        ("das Haus", "uy"), ("die Wohnung", "kvartira"), ("die Schule", "maktab"),
        ("die Arbeit", "ish"), ("die Zeit", "vaqt"), ("das Wasser", "suv"),
        ("das Brot", "non"), ("die Milch", "sut"), ("der Kaffee", "qahva"),
    ],
    "essen": [
        ("der Apfel", "olma"), ("das Brot", "non"), ("das Ei", "tuxum"),
        ("der Fisch", "baliq"), ("das Fleisch", "go'sht"), ("die Kartoffel", "kartoshka"),
        ("der Käse", "pishloq"), ("die Tomate", "pomidor"), ("die Orange", "apelsin"),
        ("die Suppe", "sho'rva"), ("der Salat", "salat"), ("das Eis", "muzqaymoq"),
    ],
    "reisen": [
        ("der Zug", "poyezd"), ("das Auto", "avtomobil"), ("das Flugzeug", "samolyot"),
        ("der Bahnhof", "vokzal"), ("der Flughafen", "aeroport"), ("das Hotel", "mehmonxona"),
        ("die Reise", "sayohat"), ("der Urlaub", "ta'til"), ("die Stadt", "shahar"),
        ("das Land", "mamlakat"), ("die Straße", "ko'cha"), ("die Karte", "xarita"),
    ],
    "familie": [
        ("die Familie", "oila"), ("die Mutter", "ona"), ("der Vater", "ota"),
        ("die Schwester", "opa/singil"), ("der Bruder", "aka/uka"), ("die Oma", "buvi"),
        ("der Opa", "bobo"), ("das Kind", "bola"), ("die Tochter", "qiz"),
        ("der Sohn", "o'gil"), ("die Frau", "ayol"), ("der Mann", "erkak"),
    ],
    "arbeit": [
        ("die Arbeit", "ish"), ("das Büro", "ofis"), ("der Chef", "boshliq"),
        ("der Kollege", "hamkasb"), ("das Geld", "pul"), ("die Zeit", "vaqt"),
        ("der Beruf", "kasb"), ("das Gehalt", "ish haqi"), ("die Pause", "tanaffus"),
        ("der Computer", "kompyuter"), ("das Telefon", "telefon"), ("die E-Mail", "email"),
    ],
    "gefuehle": [
        ("glücklich", "baxtli"), ("traurig", "qayg'uli"), ("müde", "charchagan"),
        ("hungrig", "och"), ("durstig", "chanqoq"), ("nervös", "asabiy"),
        ("wütend", "g'azablangan"), ("kalt", "sovuq"), ("warm", "issiq"),
        ("schön", "chiroyli"), ("gut", "yaxshi"), ("schlecht", "yomon"),
    ],
}


async def voice_vocab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovozli lug'at menyusi"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎙️ *Ovozli lug'at \\- AI Takrorlash*\n\n"
        "Kategoriya tanlang:\n\n"
        "Men so'zni ovozda aytaaman, siz esa takrorlaysiz. "
        "AI sizning talaffuzingizni tahlil qiladi!\n\n"
        "*Kategoriyalar:*",
        parse_mode="MarkdownV2",
        reply_markup=voice_vocab_categories_keyboard(),
    )
    return VOICE_VOCAB_MENU


async def voice_vocab_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kategoriya tanlash - so'zni ko'rsatish"""
    query = update.callback_query
    await query.answer()

    cat_key = query.data.replace("vv_cat_", "")
    words = VOCAB_WORDS.get(cat_key, [])

    if not words:
        return VOICE_VOCAB_MENU

    # Tasodifiy so'z tanlash
    word_pair = random.choice(words)
    german, uzbek = word_pair

    context.user_data["voice_vocab"] = {
        "category": cat_key,
        "current_word": german,
        "uzbek": uzbek,
        "score": 0,
        "total": 0,
    }

    # TTS bilan so'zni aytyapmiz
    await query.edit_message_text(
        f"🎙️ *Ovozli lug'at*\n\n"
        f"🔊 *So'z:* {german}\n"
        f"🇺🇿 *Tarjima: ||{esc_md(uzbek)}||*\n\n"
        f"1️⃣ TTS ovozini eshiting\n"
        f"2️⃣ Ovozli xabar yuboring\n"
        f"3️⃣ AI talaffuzingizni tahlil qiladi\n\n"
        f"*Ovozli xabaringizni yuboring!*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 So'zni eshitish", callback_data="vv_play_word")],
            [InlineKeyboardButton("🔄 Boshqa so'z", callback_data=f"vv_cat_{cat_key}")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    )

    # TTS ovozni yuborish
    await speak_text(query, f"{german}", voice="female", speed=0.9)

    return VOICE_VOCAB_PRACTICE


async def voice_vocab_play_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """So'zni qayta eshitish"""
    query = update.callback_query
    await query.answer()

    vv_data = context.user_data.get("voice_vocab", {})
    word = vv_data.get("current_word", "")

    if word:
        await speak_text(query, word, voice="female", speed=0.9)

    return VOICE_VOCAB_PRACTICE


async def voice_vocab_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi ovozli xabarini qayta ishlash"""
    vv_data = context.user_data.get("voice_vocab", {})
    current_word = vv_data.get("current_word", "")
    uzbek = vv_data.get("uzbek", "")

    if not update.message or not (update.message.voice or update.message.audio):
        await update.message.reply_text(
            "🎙️ Iltimos, ovozli xabar yuboring!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔊 So'zni eshitish", callback_data="vv_play_word")],
                [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
            ])
        )
        return VOICE_VOCAB_PRACTICE

    # "Tahlil qilinmoqda" xabari
    loading = await update.message.reply_text("🧠 *Talaffuz tahlil qilinmoqda...*", parse_mode="MarkdownV2")

    # Ovozni matnga o'girish
    user_text = await listen_to_voice(update)

    # Talaffuzni tahlil qilish
    analysis = await analyze_pronunciation(current_word, user_text)

    await loading.delete()

    score = analysis.get("score", 0)
    feedback = analysis.get("feedback", "")
    tips = analysis.get("tips", "")
    is_correct = analysis.get("correct", False)

    vv_data["total"] += 1
    if is_correct:
        vv_data["score"] += 1

    user_id = update.effective_user.id
    db = get_db()
    db.add_voice_practice(user_id, current_word, user_text, score, feedback)

    if is_correct:
        db.add_xp(user_id, XP_REWARDS["voice_practice"] // 2, "voice_vocab_correct", current_word)
        await update.message.reply_text(
            f"🎉 *Ajoyib!*\n\n"
            f"Siz: *{esc_md(user_text)}*\n"
            f"To'g'ri: *{esc_md(current_word)}*\n\n"
            f"⭐ *Ball: {score}/10*\n"
            f"{esc_md(feedback)}\n\n"
            f"💡 {esc_md(tips)}\n\n"
            f"🎁 *+{XP_REWARDS['voice_practice'] // 2} XP*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Boshqa so'z", callback_data=f"vv_cat_{vv_data['category']}")],
                [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
            ])
        )
    else:
        await update.message.reply_text(
            f"📝 *Natija*\n\n"
            f"Siz: *{esc_md(user_text)}*\n"
            f"To'g'ri: *{esc_md(current_word)}*\n"
            f"🇺🇿 *{esc_md(uzbek)}*\n\n"
            f"⭐ *Ball: {score}/10*\n"
            f"{esc_md(feedback)}\n\n"
            f"💡 {esc_md(tips)}\n\n"
            f"Yana urinib ko'ring!",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔊 Qayta eshitish", callback_data="vv_play_word")],
                [InlineKeyboardButton("🔄 Boshqa so'z", callback_data=f"vv_cat_{vv_data['category']}")],
                [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
            ])
        )

    return VOICE_VOCAB_PRACTICE


# ==================== 6. ROLEPLAY ====================

async def roleplay_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yinlar menyusi"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎭 *Rolli o'yinlar*\n\n"
        "Senariy tanlang va nemis tilida suhbatlashing!\n"
        "AI sizning rolingizdagi sherik bo'ladi.\n\n"
        "*Mavjud senariylar:*",
        parse_mode="MarkdownV2",
        reply_markup=roleplay_scenarios_keyboard(),
    )
    return ROLEPLAY_MENU


async def roleplay_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yin senariyini tanlash"""
    query = update.callback_query
    await query.answer()

    scenario_key = query.data.replace("rp_select_", "")
    scenario = ROLEPLAY_SCENARIOS.get(scenario_key)

    if not scenario:
        return ROLEPLAY_MENU

    context.user_data["roleplay"] = {
        "scenario": scenario_key,
        "messages": [
            {"role": "system", "content": scenario["ai_role"]},
        ],
        "turns": 0,
        "vocab_used": [],
    }

    # AI dan boshlang'ich xabar
    ai_msg = await groq_chat([
        {"role": "system", "content": scenario["ai_role"]},
        {"role": "user", "content": f"Start: {scenario['setup']}. Begrüßen Sie mich und stellen Sie eine erste Frage. Kurz und natürlich (2-3 Sätze)."},
    ])

    context.user_data["roleplay"]["messages"].append({"role": "assistant", "content": ai_msg})

    # TTS bilan AI xabarini aytyapmiz
    await query.edit_message_text(
        f"🎭 *{esc_md(scenario['name'])}*\n\n"
        f"📖 *Vazifa:* {esc_md(scenario['setup'])}\n\n"
        f"*Foydali so'zlar:*\n" + "\n".join([f"• {esc_md(w)}" for w in scenario['vocab']]) + "\n\n"
        f"🤖 *AI:* {esc_md(ai_msg)}\n\n"
        f"*Javobingizni yozing!* (yoki 🎙️ ovozli)",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="rp_finish")],
        ])
    )

    # AI xabarini ovozda ham yuborish
    await speak_text(query, ai_msg, voice="female", speed=1.0)

    return ROLEPLAY_CHAT


async def roleplay_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yin suhbati"""
    rp_data = context.user_data.get("roleplay", {})
    turns = rp_data.get("turns", 0)

    if update.callback_query and update.callback_query.data == "rp_finish":
        return await roleplay_result(update, context)

    # Foydalanuvchi xabari
    user_msg = ""
    if update.message and update.message.text:
        user_msg = update.message.text.strip()
    else:
        return ROLEPLAY_CHAT

    rp_data["messages"].append({"role": "user", "content": user_msg})
    turns += 1
    rp_data["turns"] = turns

    if turns >= 6:
        return await roleplay_result(update, context)

    # AI javobi
    ai_response = await groq_chat(rp_data["messages"], max_tokens=512)
    rp_data["messages"].append({"role": "assistant", "content": ai_response})

    # Ovozda yuborish
    await update.message.reply_text(
        f"🤖 *AI:* {esc_md(ai_response)}\n\n"
        f"*({turns}/6)* \\-> Javobingizni yozing:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="rp_finish")],
        ])
    )

    # TTS
    await speak_text(update, ai_response, voice="female", speed=1.0)

    return ROLEPLAY_CHAT


async def roleplay_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yin natijasi"""
    rp_data = context.user_data.get("roleplay", {})
    messages = rp_data.get("messages", [])
    scenario_key = rp_data.get("scenario", "")
    turns = rp_data.get("turns", 0)

    scenario = ROLEPLAY_SCENARIOS.get(scenario_key, {})

    await (update.callback_query.edit_message_text if update.callback_query
           else update.message.reply_text)(
        "🧠 *AI tahlil qilmoqda\\.\\.\\.*",
        parse_mode="MarkdownV2"
    )

    # AI tahlil
    analysis = await groq_json([
        {"role": "system", "content": "Siz nemis tili o'qituvchisisiz. Suhbatni tahlil qiling."},
        {"role": "user", "content": (
            f"Suhbat: {messages}\n\n"
            f"Quyidagi formatda tahlil (faqat JSON):\n"
            f"{{'score': 0-10, 'feedback': 'tahlil ozbek tilida', 'vocab_used': ['soz1', 'soz2'], "
            f"'grammar_note': 'grammatika izohi', 'fluency': 0-10}}"
        )},
    ])

    user_id = (update.callback_query.from_user.id if update.callback_query
               else update.effective_user.id)
    db = get_db()

    score = analysis.get("score", 5)
    db.add_speaking_score(
        user_id=user_id,
        session_type="roleplay",
        topic=scenario.get("name", ""),
        score=score,
        feedback=analysis.get("feedback", ""),
        duration_seconds=turns * 45,
    )
    db.add_xp(user_id, XP_REWARDS["roleplay_complete"], "roleplay", scenario.get("name", ""))

    vocab_used = ", ".join(analysis.get("vocab_used", []))

    text = (
        f"🏁 *Rolli o'yin natijasi: {esc_md(scenario.get('name', ''))}*\n\n"
        f"⭐ *Ball: {score}/10*\n"
        f"💬 *Suvliklik: {analysis.get('fluency', 5)}/10*\n\n"
        f"*Tahlil:*\n{esc_md(analysis.get('feedback', 'Yaxshi!'))}\n\n"
        f"*Foydalanilgan so'zlar:*\n{esc_md(vocab_used)}\n\n"
        f"📚 *Grammatika:*\n{esc_md(analysis.get('grammar_note', ''))}\n\n"
        f"🎁 *+{XP_REWARDS['roleplay_complete']} XP*"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard()
        )
    return AI_MENTOR_MENU


# ==================== AI MENTOR MENU HANDLER ====================

async def ai_mentor_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI Mentor asosiy menyusini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🤖 *AI Mentor*\n\n"
        "*Imkoniyatlar:*\n\n"
        "🎯 *Darajani aniqlash* \\- 5 ta savol bilan darajangizni bilib oling\n"
        "🎤 *Vorstellen* \\- O'zingizni taqdim etish mashqi\n"
        "💬 *Erfahrungen* \\- B2/C1 mavzularida suhbatlashish\n"
        "🔧 *Xato banki* \\- Xatolaringizni saqlash va mini-darslar\n"
        "🎙️ *Ovozli lug'at* \\- TTS + talaffuz tahlili\n"
        "🎭 *Rolli o'yinlar* \\- Hayotiy situatsiyalar\n\n"
        "*Bo'limni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU
