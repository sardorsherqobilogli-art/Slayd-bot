#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - AI Mentor Moduli (TO'LIQ QAYTA YOZILGAN)
Daraja aniqlash, Vorstellen, Erfahrungen, Xato banki,
Ovozli Lug'at (A1-B2, 20 mavzu, 25 so'z), Rolli O'yin (TELC/Goethe uslubi)
"""

import json
import random
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    logger, GROQ_API_KEY, GROQ_API_URL, DEFAULT_AI_MODEL,
    LEVEL_DETECTION_QUESTIONS, VORSTELLEN_PROMPTS, ERFAHRUNGEN_TOPICS,
    XP_REWARDS, LEVEL_LABELS,
)
from database import get_db
from voice_engine import speak_text, listen_to_voice, analyze_pronunciation

# ==================== STATES ====================
(
    AI_MENTOR_MENU,
    LEVEL_DETECT_Q1, LEVEL_DETECT_Q2, LEVEL_DETECT_Q3, LEVEL_DETECT_Q4, LEVEL_DETECT_Q5,
    LEVEL_DETECT_RESULT,
    VORSTELLEN_MENU, VORSTELLEN_PREPARE, VORSTELLEN_Q1, VORSTELLEN_Q2, VORSTELLEN_Q3,
    VORSTELLEN_Q4, VORSTELLEN_Q5, VORSTELLEN_Q6, VORSTELLEN_Q7,
    VORSTELLEN_ANALYZE, VORSTELLEN_RESULT, VORSTELLEN_IMPROVE,
    ERFAHRUNGEN_MENU, ERFAHRUNGEN_TOPIC, ERFAHRUNGEN_DIFFICULTY, ERFAHRUNGEN_CHAT, ERFAHRUNGEN_RESULT,
    MISTAKE_BANK_MENU, MISTAKE_REVIEW, MISTAKE_MINILESSON, MISTAKE_PRACTICE,
    VOICE_VOCAB_MENU, VOICE_VOCAB_LEVEL, VOICE_VOCAB_TOPIC, VOICE_VOCAB_WORDS,
    VOICE_VOCAB_TEST, VOICE_VOCAB_SPRECHEN,
    ROLEPLAY_MENU, ROLEPLAY_LEVEL, ROLEPLAY_TOPIC, ROLEPLAY_RULES, ROLEPLAY_CHAT, ROLEPLAY_RESULT,
    AI_MENTOR_SETTINGS,
) = range(100, 139)


# ==================== GROQ AI HELPERS ====================

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
    if not text:
        return ""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ==================== MA'LUMOTLAR ====================

# Ovozli lug'at mavzulari (daraja bo'yicha)
VOCAB_TOPICS = {
    "a1": [
        "Begrüßung", "Familie", "Essen", "Reisen", "Wohnung",
        "Arbeit", "Freizeit", "Schule", "Einkaufen", "Gesundheit",
        "Wetter", "Tiere", "Farben", "Zahlen", "Zeit",
        "Kleidung", "Körper", "Stadt", "Natur", "Hobbys",
    ],
    "a2": [
        "Urlaub", "Berufe", "Kommunikation", "Verkehr", "Feste und Feiern",
        "Medien", "Sport", "Umwelt", "Reise planen", "Restaurant",
        "Bank", "Post", "Arzt", "Wohnungssuche", "Bewerbung",
        "Schule und Uni", "Kultur", "Politik einfach", "Geschichte einfach", "Technologie einfach",
    ],
    "b1": [
        "Gesellschaft", "Bildung", "Wirtschaft", "Klimawandel", "Migration",
        "Gesundheitssystem", "Arbeitswelt", "Digitalisierung", "Globalisierung", "Stadtentwicklung",
        "Generationen", "Medien und Werbung", "Konsum", "Jugendkultur", "Ehrenamt",
        "Sport und Gesellschaft", "Ernährung und Trends", "Sprachlernen", "Interkulturalität", "Reisen und Tourismus",
    ],
    "b2": [
        "Nachhaltigkeit", "Demokratie", "Menschenrechte", "Künstliche Intelligenz", "Bioethik",
        "Wirtschaftspolitik", "Sozialsysteme", "Kulturelle Identität", "Literatur und Kunst", "Wissenschaft",
        "Urbanisierung", "Gleichstellung", "Medizinische Forschung", "Digitale Transformation", "Internationale Beziehungen",
        "Klimapolitik", "Philosophie des Alltags", "Finanzwelt", "Bildungspolitik", "Sprache und Macht",
    ],
}

# Rolli o'yin mavzulari (daraja bo'yicha)
ROLEPLAY_TOPICS = {
    "a1": [
        "Geburtstag feiern", "Picknick planen", "Freunde einladen", "Einkaufen gehen",
        "Ausflug machen", "Kino besuchen", "Kochen zusammen", "Park besuchen",
        "Bibliothek", "Spielplatz", "Museum", "Zoo",
        "Schwimmbad", "Café treffen", "Spaziergang", "Gartenarbeit",
        "Hausaufgaben", "Aufräumen", "Backen", "Sport treiben",
    ],
    "a2": [
        "Klassenfahrt planen", "Sportevent organisieren", "Geburtstagsparty", "Urlaub buchen",
        "Wohnung renovieren", "Schulausflug", "Kulturveranstaltung", "Familienfest",
        "Grillparty", "Vereinstreffen", "Sommerfest", "Jugendprojekt",
        "Stadtbesichtigung", "Flohmarkt", "Freiwilligenarbeit", "Filmabend",
        "Lesekreis", "Kochkurs", "Tanzveranstaltung", "Weihnachtsfeier",
    ],
    "b1": [
        "Gemeindeprojekt", "Umweltaktion", "Stadtfest organisieren", "Vereinsgründung",
        "Schulprojekt", "Fundraising", "Berufsmesse", "Integrationsprojekt",
        "Kulturprojekt", "Nachbarschaftshilfe", "Sportturnier", "Musikveranstaltung",
        "Theaterstück", "Ausstellung", "Konferenz", "Workshop",
        "Seminartag", "Projektpräsentation", "Teambuilding", "Abschlussfest",
    ],
    "b2": [
        "Internationale Konferenz", "Politisches Forum", "Wissenschaftsprojekt", "Unternehmensstrategie",
        "Stadtplanung", "Soziales Projekt", "Kultureller Austausch", "Bildungsreform",
        "Umweltschutzprojekt", "Medienproduktion", "Digitales Projekt", "Forschungsprojekt",
        "NGO Gründung", "Wirtschaftsprojekt", "Integrationsprogramm", "Kunstprojekt",
        "Literarisches Projekt", "Historisches Projekt", "Philosophische Diskussion", "Innovationsprojekt",
    ],
}

# Rolli o'yin punktlari (mavzuga mos)
ROLEPLAY_PUNKTE = {
    "default": [
        "Wo? — Qayerda bo'ladi?",
        "Wann? — Qachon bo'ladi?",
        "Wer kommt? — Kim keladi?",
        "Was mitbringen? — Nima olib kelish?",
        "Wie viel kostet es? — Qancha turadi?",
    ]
}

LEVEL_EMOJI = {"a1": "🟢", "a2": "🟢", "b1": "🟡", "b2": "🟡", "c1": "🔵"}


# ==================== KEYBOARDS ====================

def ai_mentor_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Darajani aniqlash", callback_data="ai_level_detect")],
        [InlineKeyboardButton("🎤 Vorstellen (Taqdimot)", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("💬 Erfahrungen (B2/C1)", callback_data="ai_erfahrungen")],
        [InlineKeyboardButton("🔧 Mening xato bankim", callback_data="ai_mistake_bank")],
        [InlineKeyboardButton("📚 Ovozli lug'at", callback_data="ai_voice_vocab")],
        [InlineKeyboardButton("🎭 Rolli o'yinlar", callback_data="ai_roleplay")],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])


def three_section_keyboard(prefix: str, extra_buttons: list = None):
    """Tushuntirish | Tarjima | Yaxshilash tugmalari"""
    rows = [
        [
            InlineKeyboardButton("💡 Tushuntirish", callback_data=f"{prefix}_tushuntirish"),
            InlineKeyboardButton("🌐 Tarjima", callback_data=f"{prefix}_tarjima"),
            InlineKeyboardButton("✅ Yaxshilash", callback_data=f"{prefix}_yaxshilash"),
        ],
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data=f"{prefix}_speak")],
    ]
    if extra_buttons:
        rows.extend(extra_buttons)
    return InlineKeyboardMarkup(rows)


def level_select_keyboard(callback_prefix: str):
    """A1/A2/B1/B2 daraja tanlash"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1", callback_data=f"{callback_prefix}_a1"),
            InlineKeyboardButton("🟢 A2", callback_data=f"{callback_prefix}_a2"),
        ],
        [
            InlineKeyboardButton("🟡 B1", callback_data=f"{callback_prefix}_b1"),
            InlineKeyboardButton("🟡 B2", callback_data=f"{callback_prefix}_b2"),
        ],
        [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
    ])


def topics_keyboard(topics: list, callback_prefix: str):
    """Mavzular ro'yxati (2 ustunli)"""
    rows = []
    for i in range(0, len(topics), 2):
        row = [InlineKeyboardButton(topics[i], callback_data=f"{callback_prefix}_{i}")]
        if i + 1 < len(topics):
            row.append(InlineKeyboardButton(topics[i + 1], callback_data=f"{callback_prefix}_{i+1}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("↩️ Orqaga", callback_data="ai_mentor_menu")])
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
    await query.edit_message_text(
        f"🎯 *Darajani aniqlash* \\(5 ta savol\\)\n\n"
        f"*Savol 1/5:*\n{esc_md(question['question'])}\n\n"
        f"💡 Yordam uchun: `Yordam` deb yozing\n"
        f"📝 Yozma YOKI 🎙️ ovozli javob bering\\!",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="level_skip_0")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ])
    )
    return LEVEL_DETECT_Q1


async def level_detect_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja aniqlash savolini qayta ishlash — matn YOKI ovoz"""
    user_data = context.user_data.get("level_detect", {})
    q_idx = user_data.get("current_q", 0)

    # Callback (o'tkazib yuborish)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data.startswith("level_skip_"):
            user_data["answers"].append({"skipped": True, "correct": False, "answer": ""})
            q_idx += 1
            user_data["current_q"] = q_idx
            if q_idx >= len(LEVEL_DETECTION_QUESTIONS):
                return await _level_detect_show_result(query, context, via_callback=True)
            question = LEVEL_DETECTION_QUESTIONS[q_idx]
            await query.edit_message_text(
                f"🎯 *Savol {q_idx + 1}/5*\n\n{esc_md(question['question'])}\n\n"
                f"📝 Javobingizni yozing yoki 🎙️ ovoz yuboring:",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"level_skip_{q_idx}")],
                ])
            )
            return LEVEL_DETECT_Q1 + min(q_idx, 4)
        return LEVEL_DETECT_Q1

    # Ovozli javob
    if update.message and (update.message.voice or update.message.audio):
        loading = await update.message.reply_text("🎙️ *Ovoz tahlil qilinmoqda...*", parse_mode="MarkdownV2")
        user_text = await listen_to_voice(update)
        await loading.delete()
    elif update.message and update.message.text:
        user_text = update.message.text.strip()
    else:
        return LEVEL_DETECT_Q1 + min(q_idx, 4)

    # Yordam
    question = LEVEL_DETECTION_QUESTIONS[q_idx]
    if user_text.lower() in ["yordam", "help", "?"]:
        hints = "\n".join([f"💡 {h}" for h in question.get("hints", [])])
        user_data["hints_used"].append(q_idx)
        await update.message.reply_text(
            f"🎯 *Savol {q_idx + 1}/5*\n\n{esc_md(question['question'])}\n\n"
            f"*Yordam:*\n{hints}\n\nEndi javobingizni yozing:",
            parse_mode="MarkdownV2",
        )
        return LEVEL_DETECT_Q1 + min(q_idx, 4)

    # AI bilan tahlil + 3 tugma
    result = await groq_json([
        {"role": "system", "content": (
            "Nemis tili o'qituvchisi. Foydalanuvchi javobini tahlil qil. "
            "JSON formatida qaytargin: {"
            '"tushuntirish": "xatolar va grammatika tushuntirish (o\'zbek tilida)",'
            '"tarjima": "to\'g\'ri nemischa javob matni",'
            '"yaxshilash": "yaxshilangan variant va maslahatlar",'
            '"is_correct": true_yoki_false,'
            '"level_hint": "A1 yoki A2 yoki B1 yoki B2 yoki C1"'
            "}"
        )},
        {"role": "user", "content": f"Savol: {question['question']}\nJavob: {user_text}"}
    ])

    is_correct = result.get("is_correct", False)
    user_data["answers"].append({"answer": user_text, "correct": is_correct, "skipped": False})

    # Natijani saqlash (tugmalar uchun)
    context.user_data["ld_result"] = result
    context.user_data["ld_speak_text"] = result.get("tarjima", user_text)

    status = "✅ *To'g'ri\\!*" if is_correct else "❌ *Noto'g'ri*"

    await update.message.reply_text(
        f"{status}\n\n"
        f"🎯 *Sizning javobingiz:* _{esc_md(user_text)}_\n\n"
        f"Tahlilni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💡 Tushuntirish", callback_data="ld_show_tushuntirish"),
                InlineKeyboardButton("🌐 Tarjima", callback_data="ld_show_tarjima"),
                InlineKeyboardButton("✅ Yaxshilash", callback_data="ld_show_yaxshilash"),
            ],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="ld_speak")],
            [InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"level_skip_{q_idx + 1}")],
        ])
    )

    q_idx += 1
    user_data["current_q"] = q_idx
    return LEVEL_DETECT_Q1 + min(q_idx, 4)


async def ld_show_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Level detect — 3 tugma natijasi ko'rsatish"""
    query = update.callback_query
    await query.answer()

    result = context.user_data.get("ld_result", {})
    section = query.data.replace("ld_show_", "")

    content_map = {
        "tushuntirish": ("💡 *Tushuntirish*", result.get("tushuntirish", "Ma'lumot yo'q")),
        "tarjima": ("🌐 *To'g'ri variant*", result.get("tarjima", "Ma'lumot yo'q")),
        "yaxshilash": ("✅ *Yaxshilash tavsiyalari*", result.get("yaxshilash", "Ma'lumot yo'q")),
    }

    title, text = content_map.get(section, ("", ""))
    q_idx = context.user_data.get("level_detect", {}).get("current_q", 1)

    await query.edit_message_text(
        f"{title}\n\n{esc_md(text)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💡 Tushuntirish", callback_data="ld_show_tushuntirish"),
                InlineKeyboardButton("🌐 Tarjima", callback_data="ld_show_tarjima"),
                InlineKeyboardButton("✅ Yaxshilash", callback_data="ld_show_yaxshilash"),
            ],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="ld_speak")],
            [InlineKeyboardButton("➡️ Keyingi savol", callback_data=f"level_skip_{q_idx}")],
        ])
    )
    return LEVEL_DETECT_Q1 + min(max(q_idx - 1, 0), 4)


async def ld_speak_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Level detect — ovozda o'qish"""
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")

    speak_text_val = context.user_data.get("ld_speak_text", "")
    if speak_text_val:
        await speak_text(query, speak_text_val, voice="female", speed=0.9)

    q_idx = context.user_data.get("level_detect", {}).get("current_q", 1)
    return LEVEL_DETECT_Q1 + min(max(q_idx - 1, 0), 4)


async def _level_detect_show_result(obj, context: ContextTypes.DEFAULT_TYPE, via_callback=False) -> int:
    """Daraja aniqlash yakuniy natijasi"""
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

    user_id = (obj.from_user.id if via_callback else obj.effective_user.id)
    db = get_db()
    db.update_user(user_id, current_level=level)

    level_desc = {
        "a1": "Boshlang'ich daraja\\. A1 lektsiyalaridan boshlang\\! 📚",
        "a2": "Elementar daraja\\. Asosiy grammatikani mustahkamlang\\! 📖",
        "b1": "O'rta daraja\\. Muloqot va murakkab mavzularni o'rganing\\! 💬",
        "b2": "Yuqori o'rta daraja\\. Akademik nemis tiliga o'ting\\! 🎓",
        "c1": "Yuqori daraja\\. Professional darajada erkin muloqot\\! 🏆",
    }

    text = (
        f"🎯 *Daraja aniqlash natijasi*\n\n"
        f"✅ To'g'ri: {correct_count}/5\n"
        f"💡 Yordam: {len(user_data.get('hints_used', []))} ta\n\n"
        f"📊 *Sizning darajangiz: {esc_md(LEVEL_LABELS.get(level, level.upper()))}*\n\n"
        f"{level_desc.get(level, '')}"
    )

    if via_callback:
        await obj.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard())
    else:
        await obj.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard())
    return AI_MENTOR_MENU


# ==================== 2. VORSTELLEN ====================

# ==================== VORSTELLEN MUKAMMAL (7 SAVOL + 4 DARAJA + PDF) ====================

# VORSTELLEN SAVOLLARI (Goethe/TELC imtihon uslubida)
VORSTELLEN_SAVOLLAR = [
    {
        "id": 1,
        "nemis": "Stellen Sie sich vor! Wie heißen Sie und wie alt sind Sie?",
        "uzbek": "O'zingizni taqdim eting! Ismingiz va yoshingizni ayting.",
        "mavzu": "Name und Alter",
        "shablon_a1": ["Ich heiße [NAME].", "Ich bin [NAME].", "Mein Name ist [NAME].", "Ich bin [ALTER] Jahre alt."],
        "shablon_a2": ["Mein Name ist [NAME] und ich bin [ALTER] Jahre alt.", "Ich heiße [NAME]. Ich wurde [ALTER] Jahre alt.", "Ich bin [NAME], [ALTER] Jahre alt."],
        "shablon_b1": ["Mein Name ist [NAME] und ich bin [ALTER] Jahre alt. Ich wurde in [JAHR] geboren.", "Ich heiße [NAME], bin [ALTER] Jahre alt und komme ursprünglich aus [LAND]."],
        "shablon_b2": ["Mein Name ist [NAME], ich bin [ALTER] Jahre alt und wurde in [STADT] geboren. Seit [JAHR] lebe ich in [LAND].", "Ich heiße [NAME], bin [ALTER] Jahre alt und komme aus einer großen Familie in [STADT]."]
    },
    {
        "id": 2,
        "nemis": "Woher kommen Sie? Erzählen Sie von Ihrem Heimatland.",
        "uzbek": "Qayerdansiz? Vataningiz haqida gapiring.",
        "mavzu": "Herkunft / Heimatland",
        "shablon_a1": ["Ich komme aus [LAND].", "Ich bin in [STADT] geboren.", "Das liegt in [RICHTUNG] von [LAND]."],
        "shablon_a2": ["Ich komme aus [LAND]. Das liegt in [RICHTUNG] von [KONTINENT].", "Ich wurde in [STADT] geboren. Das ist die Hauptstadt von [LAND].", "Das liegt in der Nähe von [LAND/STADT]."],
        "shablon_b1": ["Ich komme aus [LAND], das im [RICHTUNG] von [KONTINENT] liegt. Es ist ein [ADJEKTIV] Land mit [ANZAHL] Millionen Einwohnern.", "Ich bin in [STADT] geboren, der Hauptstadt von [LAND]. Die Stadt ist bekannt für [MERKMAL]."],
        "shablon_b2": ["Ich komme aus [LAND], einem [ADJEKTIV] Land im Herzen von [KONTINENT], das für seine [MERKMAL] weltweit bekannt ist.", "Meine Heimatstadt [STADT], in der ich geboren wurde, ist eine [ADJEKTIV] Stadt mit einer reichen Geschichte und [ANZAHL] Millionen Einwohnern."]
    },
    {
        "id": 3,
        "nemis": "Wo wohnen Sie? Beschreiben Sie Ihre Wohnung/Ihr Haus.",
        "uzbek": "Qayerda yashaysiz? Uy/apartamentingizni tavsiflang.",
        "mavzu": "Wohnort und Wohnung",
        "shablon_a1": ["Ich wohne in [STADT].", "Ich habe eine kleine Wohnung.", "Ich wohne in einem Haus."],
        "shablon_a2": ["Seit [ZEIT] wohne ich in [STADT].", "Ich wohne in einer [ADJEKTIV] Wohnung mit [ANZAHL] Zimmern.", "Ich bin vor [ZEIT] nach [STADT] gekommen."],
        "shablon_b1": ["Seit [ZEIT] Jahren wohne ich in [STADT]. Ich habe eine [ADJEKTIV] Wohnung mit [ANZAHL] Zimmern und einem [MERKMAL].", "Ich wohne in einem [ADJEKTIV] Haus im [RICHTUNG] von [STADT]. Am besten gefällt mir [MERKMAL], weil [GRUND]."],
        "shablon_b2": ["Seit [ZEIT] Jahren lebe ich in [STADT], einer [ADJEKTIV] Stadt mit [ANZAHL] Millionen Einwohnern. Meine Wohnung im [STADTVIERTEL] ist [ADJEKTIV] und bietet [VORTEIL].", "Ich wohne in einem [ADJEKTIV] Haus im [RICHTUNG] von [STADT], das [MERKMAL] hat. Besonders schätze ich [VORTEIL], weil [GRUND]."]
    },
    {
        "id": 4,
        "nemis": "Erzählen Sie von Ihrer Familie.",
        "uzbek": "Oilangiz haqida gapiring.",
        "mavzu": "Familie",
        "shablon_a1": ["Ich habe [ANZAHL] Bruder/Schwester.", "Meine Familie lebt in [ORT].", "Ich bin ledig. / Ich bin verheiratet."],
        "shablon_a2": ["Ich lebe mit meiner Familie in [ORT].", "Ich bin verheiratet und habe [ANZAHL] Kinder.", "Meine Familie ist [ADJEKTIV]. Wir treffen uns [ZEIT]."],
        "shablon_b1": ["Ich bin [FAMILIENSTAND] und habe [ANZAHL] Kinder. Meine Familie lebt in [ORT] und wir sehen uns [ZEIT].", "Meine Familie ist sehr [ADJEKTIV]. Wir machen oft zusammen [AKTIVITÄT], besonders am Wochenende."],
        "shablon_b2": ["Ich komme aus einer [ADJEKTIV] Familie mit [ANZAHL] Geschwistern. Unsere Familientraditionen, wie [TRADITION], sind mir sehr wichtig, weil [GRUND].", "Meine Familie lebt in [ORT]. Obwohl wir nicht jeden Tag zusammen sind, pflegen wir eine enge Beziehung durch [AKTIVITÄT]."]
    },
    {
        "id": 5,
        "nemis": "Wo haben Sie Deutsch gelernt? Wie lange lernen Sie schon?",
        "uzbek": "Qayerda nemis tilini o'rgandingiz? Qancha vaqtdan beri o'rganasiz?",
        "mavzu": "Deutsch lernen",
        "shablon_a1": ["Ich lerne Deutsch in [ORT].", "Ich lerne seit [ZEIT].", "Das war an der [SCHULE]."],
        "shablon_a2": ["Ich habe Deutsch an der [SCHULE] gelernt.", "Ich lerne seit [ZEIT] Monaten/Jahren Deutsch.", "Das war an der Universität [NAME]."],
        "shablon_b1": ["Ich habe Deutsch an der [SCHULE/UNI] gelernt. Ich lerne seit [ZEIT] Jahren und es macht mir [EMOTION].", "Ich habe dort [ZEIT] Jahre Deutsch gelernt. Besonders [ASPEKT] finde ich [ADJEKTIV]."],
        "shablon_b2": ["Ich habe Deutsch an der [SCHULE/UNI] in [ORT] gelernt, wo ich [ZEIT] Jahre intensiv studiert habe. Die Methoden, besonders [METHODE], haben mir sehr geholfen.", "Seit [ZEIT] Jahren lerne ich Deutsch mit [METHODEN]. Was mich besonders fasziniert, ist [ASPEKT], weil [GRUND]."]
    },
    {
        "id": 6,
        "nemis": "Was machen Sie? (Studium, Beruf, Schule...)",
        "uzbek": "Nima ish qilasiz? (O'qish, ish, maktab...)",
        "mavzu": "Studium und Arbeit",
        "shablon_a1": ["Ich bin Schüler/Student.", "Ich arbeite als [BERUF].", "Ich mache eine Ausbildung."],
        "shablon_a2": ["Ich arbeite als [BERUF] bei [FIRMA].", "Ich studiere [FACH] an der Universität [NAME].", "Ich mache eine Fortbildung als [BERUF]."],
        "shablon_b1": ["Ich studiere [FACH] an der [UNI] in [ORT]. Später möchte ich gerne als [BERUF] arbeiten, weil [GRUND].", "Aktuell bin ich als [BERUF] bei [FIRMA] tätig. Meine Aufgaben sind [AUFGABEN]."],
        "shablon_b2": ["Ich studiere [FACH] an der [UNI] in [ORT], mit Schwerpunkt auf [SCHWERPUNKT]. In meinem Heimatland war ich [BERUF], was ich gerne wieder in Deutschland machen möchte.", "Als [BERUF] bei [FIRMA] bin ich für [AUFGABEN] verantwortlich. Besonders herausfordernd finde ich [ASPEKT], aber auch [POSITIV]."]
    },
    {
        "id": 7,
        "nemis": "Welche Sprachen sprechen Sie? Warum lernen Sie Deutsch?",
        "uzbek": "Qaysi tillarni bilasiz? Nima uchun nemis tilini o'rganasiz?",
        "mavzu": "Sprachen",
        "shablon_a1": ["Meine Muttersprache ist [SPRACHE].", "Ich spreche [SPRACHE] und Deutsch.", "Ich lerne Deutsch, weil [GRUND]."],
        "shablon_a2": ["Meine Muttersprache ist [SPRACHE]. Außerdem spreche ich [SPRACHE] und natürlich Deutsch.", "Ich spreche [SPRACHE], [SPRACHE] und Deutsch.", "Ich lerne Deutsch, weil ich in Deutschland [ZIEL] möchte."],
        "shablon_b1": ["Meine Muttersprache ist [SPRACHE]. Außerdem spreche ich fließend [SPRACHE] und ein bisschen [SPRACHE]. Ich lerne Deutsch, weil [GRUND].", "Ich beherrsche [ANZAHL] Sprachen: [SPRACHEN]. Deutsch lerne ich, weil [GRUND]. Besonders [ASPEKT] finde ich [ADJEKTIV]."],
        "shablon_b2": ["Meine Muttersprache [SPRACHE] habe ich von Kindesbeinen an gesprochen. Durch [ERFAHRUNG] habe ich auch [SPRACHE] gelernt. Deutsch ist für mich wichtig, weil [GRUND] – besonders im Hinblick auf [ZUKUNFT].", "Ich spreche [SPRACHEN] auf [NIVEAU]-Niveau. Meine Motivation für Deutsch ist [GRUND], was sich in [SITUATION] als äußerst nützlich erwiesen hat."]
    }
]

# Ogohlantirish matni
VORSTELLEN_OGOHLANTIRISH = """⚠️ *ESLATMA: Imtihon sharoitida*

• Tayyorlanish vaqti: *15 soniya*
• Biz sizga beramiz: *10 daqiqa*

📌 *Agar to'liq ma'lumot bera olmasangiz,*
*natija yaxshi bo'lmaydi!*

✅ *7 ta bo'limning barchasini yoritish shart!*
❌ Biror bo'lim qoldirilsa - ball kamayadi

🎯 *Maslahat: Oldin shablonlarni ko'rib chiqing!*"""

# Yulduz baholash
VORSTELLEN_YULDUZ = {
    7: "⭐⭐⭐⭐⭐⭐⭐ (7/7) - Mukammal! Barcha bo'limlar yoritilgan.",
    6: "⭐⭐⭐⭐⭐⭐ (6/7) - Yaxshi! 1 ta bo'lim yetishmayapti.",
    5: "⭐⭐⭐⭐⭐ (5/7) - O'rta. 2 ta bo'lim qoldirilgan.",
    4: "⭐⭐⭐⭐ (4/7) - Qoniqarli. 3 ta bo'lim yetishmayapti.",
    3: "⭐⭐⭐ (3/7) - Kam. 4 ta bo'lim qoldirilgan.",
    2: "⭐⭐ (2/7) - Juda kam. 5 ta bo'lim yetishmayapti.",
    1: "⭐ (1/7) - Yomon. 6 ta bo'lim qoldirilgan.",
    0: "❌ (0/7) - Hech qanday ma'lumot yo'q."
}


# ==================== VORSTELLEN KEYBOARDS ====================

def vorstellen_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎤 Boshlash (7 savol)", callback_data="vorstellen_start")],
        [InlineKeyboardButton("📚 Shablonlarni ko'rish", callback_data="vorstellen_templates")],
        [InlineKeyboardButton("⚠️ Qoidalar", callback_data="vorstellen_rules")],
        [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
    ])


def vorstellen_templates_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 A1 Shablon", callback_data="vorstellen_template_a1")],
        [InlineKeyboardButton("🟢 A2 Shablon", callback_data="vorstellen_template_a2")],
        [InlineKeyboardButton("🟡 B1 Shablon", callback_data="vorstellen_template_b1")],
        [InlineKeyboardButton("🟡 B2 Shablon", callback_data="vorstellen_template_b2")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data="vorstellen_menu")],
    ])


def vorstellen_level_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1", callback_data="vorstellen_level_a1"),
            InlineKeyboardButton("🟢 A2", callback_data="vorstellen_level_a2"),
        ],
        [
            InlineKeyboardButton("🟡 B1", callback_data="vorstellen_level_b1"),
            InlineKeyboardButton("🟡 B2", callback_data="vorstellen_level_b2"),
        ],
        [InlineKeyboardButton("↩️ Orqaga", callback_data="vorstellen_result")],
    ])


def vorstellen_continue_keyboard(q_num: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ Davom etish", callback_data=f"vorstellen_next_{q_num}")],
        [InlineKeyboardButton("⏹️ Tugatish", callback_data="vorstellen_finish")],
    ])


def vorstellen_result_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💡 Tushuntirish", callback_data="vs_show_tushuntirish"),
            InlineKeyboardButton("🌐 Tarjima", callback_data="vs_show_tarjima"),
            InlineKeyboardButton("✅ Yaxshilash", callback_data="vs_show_yaxshilash"),
        ],
        [InlineKeyboardButton("📄 PDF yuklash", callback_data="vorstellen_pdf")],
        [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
        [InlineKeyboardButton("🔁 Qayta urinish", callback_data="ai_vorstellen")],
        [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
    ])


# ==================== VORSTELLEN HANDLERS (YANGI) ====================

async def vorstellen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen asosiy menyusi - yangi"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎤 *Vorstellen - O'zingizni taqdim etish*\n\n"
        "*Goethe / TELC imtihon uslubida*\n\n"
        "📋 *7 ta savol:*\n"
        "1️⃣ Ism va yosh\n"
        "2️⃣ Qayerdansiz\n"
        "3️⃣ Yashash joyingiz\n"
        "4️⃣ Oilangiz\n"
        "5️⃣ Nemis tilini qayerda o'rgandingiz\n"
        "6️⃣ Nima ish qilasiz\n"
        "7️⃣ Qaysi tillarni bilasiz\n\n"
        "⚠️ *Imtihonda 15 soniya tayyorlanish vaqti!*\n"
        "*Biz sizga 10 daqiqa beramiz*\n\n"
        "*Bo'limni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=vorstellen_main_keyboard()
    )
    return VORSTELLEN_START


async def vorstellen_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Qoidalar ko'rsatish"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        f"{esc_md(VORSTELLEN_OGOHLANTIRISH)}\n\n"
        "*7 ta bo'lim:*\n"
        "1️⃣ Name und Alter\n"
        "2️⃣ Herkunft / Heimatland\n"
        "3️⃣ Wohnort und Wohnung\n"
        "4️⃣ Familie\n"
        "5️⃣ Deutsch lernen\n"
        "6️⃣ Studium und Arbeit\n"
        "7️⃣ Sprachen\n\n"
        "❌ *Agar biror bo'lim qoldirilsa:*\n"
        "• Ball kamayadi\n"
        "• Daraja pasayadi\n"
        "• Natija yaxshi bo'lmaydi\n\n"
        "✅ *Maslahat:* Oldin shablonlarni ko'rib chiqing!",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Shablonlarni ko'rish", callback_data="vorstellen_templates")],
            [InlineKeyboardButton("🎤 Boshlash", callback_data="vorstellen_start")],
            [InlineKeyboardButton("↩️ Orqaga", callback_data="vorstellen_menu")],
        ])
    )
    return VORSTELLEN_START


async def vorstellen_templates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shablonlarni ko'rsatish"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📚 *Shablonlar*\n\n"
        "Har bir daraja uchun tayyor iboralar:\n\n"
        "🟢 *A1* - Oddiy, qisqa gaplar\n"
        "🟢 *A2* - O'rta, birikmalar\n"
        "🟡 *B1* - Murakkab, tushuntirishlar\n"
        "🟡 *B2* - Professional, mukammal\n\n"
        "*Darajangizni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=vorstellen_templates_keyboard()
    )
    return VORSTELLEN_START


async def vorstellen_template_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Konkret shablon ko'rsatish"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("vorstellen_template_", "")

    text = f"📚 *{level.upper()} Shablonlar*\n\n"

    for savol in VORSTELLEN_SAVOLLAR:
        text += f"*{savol['id']}. {esc_md(savol['mavzu'])}*\n"
        shablon_key = f"shablon_{level}"
        for ibora in savol.get(shablon_key, []):
            text += f"• {esc_md(ibora)}\n"
        text += "\n"

    text += "\n💡 *Maslahat:* Bu iboralarni o'zingizga moslang!"

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 Boshlash", callback_data="vorstellen_start")],
            [InlineKeyboardButton("↩️ Orqaga", callback_data="vorstellen_templates")],
        ])
    )
    return VORSTELLEN_START


async def vorstellen_start_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Vorstellen boshlash - 7 ta savol"""
    query = update.callback_query
    await query.answer()

    # Reset user data
    context.user_data["vorstellen"] = {
        "answers": [],
        "current_q": 1,
        "voice_parts": [],
        "analysis": None,
    }

    savol = VORSTELLEN_SAVOLLAR[0]

    await query.edit_message_text(
        f"🎤 *Vorstellen - Savol {savol['id']}/7*\n\n"
        f"🇩🇪 *{esc_md(savol['nemis'])}*\n\n"
        f"🇺🇿 {esc_md(savol['uzbek'])}\n\n"
        f"📝 *Javobingizni yozing YOKI*\n"
        f"🎙️ *Ovozli xabar yuboring*\n\n"
        f"_(3 martagacha ovoz yuborish mumkin)_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="vorstellen_skip_1")],
            [InlineKeyboardButton("🏠 Tugatish", callback_data="vorstellen_finish")],
        ])
    )
    return VORSTELLEN_START


async def vorstellen_process_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Savol javobini qayta ishlash - yangi"""
    v_data = context.user_data.get("vorstellen", {})
    current_q = v_data.get("current_q", 1)

    # Callback handling
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == "vorstellen_finish":
            return await vorstellen_analyze_new(update, context)

        if query.data.startswith("vorstellen_skip_"):
            v_data["answers"].append({
                "q_num": current_q,
                "text": "",
                "voice": False,
                "skipped": True
            })
            return await _next_savol(update, context, current_q + 1)

        if query.data.startswith("vorstellen_next_"):
            return await _next_savol(update, context, current_q)

    # Message handling
    if not update.message:
        return VORSTELLEN_START

    # Ovozli xabar
    if update.message.voice or update.message.audio:
        loading = await update.message.reply_text("🎙️ *Ovoz tahlil qilinmoqda...*", parse_mode="MarkdownV2")

        user_text = await listen_to_voice(update)
        await loading.delete()

        v_data["voice_parts"].append({
            "q_num": current_q,
            "text": user_text
        })

        voice_count = len([v for v in v_data.get("voice_parts", []) if v["q_num"] == current_q])
        if voice_count < 3:
            await update.message.reply_text(
                f"✅ *Ovoz qabul qilindi!*\n\n"
                f"_{esc_md(user_text[:100])}..._\n\n"
                f"*Yana ovoz yuborishni xohlaysizmi?*\n"
                f"_(Yana {3 - voice_count} ta imkoniyat)_",
                parse_mode="MarkdownV2",
                reply_markup=vorstellen_continue_keyboard(current_q)
            )
            return VORSTELLEN_START
        else:
            return await _next_savol(update, context, current_q + 1)

    # Matnli xabar
    elif update.message.text:
        user_text = update.message.text.strip()

        v_data["answers"].append({
            "q_num": current_q,
            "text": user_text,
            "voice": False,
            "skipped": False
        })

        return await _next_savol(update, context, current_q + 1)

    return VORSTELLEN_START


async def _next_savol(update, context, next_q_num):
    """Keyingi savolga o'tish"""
    v_data = context.user_data.get("vorstellen", {})

    if next_q_num > 7:
        return await vorstellen_analyze_new(update, context)

    v_data["current_q"] = next_q_num
    savol = VORSTELLEN_SAVOLLAR[next_q_num - 1]

    # Ovozli qismlarni birlashtirish
    voice_parts = [v["text"] for v in v_data.get("voice_parts", []) if v["q_num"] == next_q_num - 1]
    if voice_parts:
        full_text = " ".join(voice_parts)
        v_data["answers"].append({
            "q_num": next_q_num - 1,
            "text": full_text,
            "voice": True,
            "skipped": False
        })
        v_data["voice_parts"] = [v for v in v_data.get("voice_parts", []) if v["q_num"] != next_q_num - 1]

    text = (
        f"🎤 *Savol {savol['id']}/7*\n\n"
        f"🇩🇪 *{esc_md(savol['nemis'])}*\n\n"
        f"🇺🇿 {esc_md(savol['uzbek'])}\n\n"
        f"📝 *Javobingizni yozing YOKI*\n"
        f"🎙️ *Ovozli xabar yuboring*"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data=f"vorstellen_skip_{next_q_num}")],
        [InlineKeyboardButton("🏠 Tugatish", callback_data="vorstellen_finish")],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return VORSTELLEN_START


async def vorstellen_analyze_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI tahlil - yangi (7 savol + yulduz)"""
    v_data = context.user_data.get("vorstellen", {})
    answers = v_data.get("answers", [])

    # Oxirgi ovozli qismlarni birlashtirish
    current_q = v_data.get("current_q", 1)
    voice_parts = [v["text"] for v in v_data.get("voice_parts", []) if v["q_num"] == current_q]
    if voice_parts:
        full_text = " ".join(voice_parts)
        v_data["answers"].append({
            "q_num": current_q,
            "text": full_text,
            "voice": True,
            "skipped": False
        })

    # Qoldirilgan savollarni tekshirish
    answered_nums = set(a["q_num"] for a in answers if a.get("text"))
    missed = [i for i in range(1, 8) if i not in answered_nums]
    score = len(answered_nums)

    # AI tahlil
    all_text = "\n".join([f"Savol {a['q_num']}: {a['text']}" for a in answers if a.get("text")])

    loading = await (update.callback_query.edit_message_text if update.callback_query 
                     else update.message.reply_text)(
        "🧠 *AI tahlil qilmoqda...*\n\n"
        "• Grammatik tekshirilmoqda\n"
        "• So'z boyligi baholanmoqda\n"
        "• Suvliklik tekshirilmoqda\n"
        "• Daraja aniqlanmoqda\n\n"
        "_Iltimos, kuting..._",
        parse_mode="MarkdownV2"
    )

    result = await groq_json([
        {"role": "system", "content": (
            "Siz nemis tili o'qituvchisisiz. Foydalanuvchi 7 ta savolga javob berdi. "
            "Har bir savolni tahlil qiling va JSON formatida qaytaring:\n"
            "{\n"
            '  "grammar_score": 1-10,\n'
            '  "vocabulary_score": 1-10,\n'
            '  "fluency_score": 1-10,\n'
            '  "detected_level": "A1 yoki A2 yoki B1 yoki B2",\n'
            '  "tushuntirish": "xatolar va grammatika tushuntirish uzbek tilida",\n'
            '  "tarjima": "togri nemischa variant",\n'
            '  "yaxshilash_a1": "A1 darajasida mukammal variant",\n'
            '  "yaxshilash_a2": "A2 darajasida mukammal variant",\n'
            '  "yaxshilash_b1": "B1 darajasida mukammal variant",\n'
            '  "yaxshilash_b2": "B2 darajasida mukammal variant",\n'
            '  "grammar_errors": [{"xato": "...", "togri": "..."}],\n'
            '  "good_points": ["yaxshi jihatlar"]\n'
            "}"
        )},
        {"role": "user", "content": f"Javoblar:\n{all_text}\n\nQoldirilgan savollar: {missed}"}
    ], max_tokens=2048)

    v_data["analysis"] = result
    v_data["missed_questions"] = missed

    # Yulduz baholash
    stars = "⭐" * score + "☆" * (7 - score)
    yulduz_text = VORSTELLEN_YULDUZ.get(score, VORSTELLEN_YULDUZ[0])

    # Daraja
    level = result.get("detected_level", "A1")

    # XP qo'shish
    user_id = (update.callback_query.from_user.id if update.callback_query else update.effective_user.id)
    db = get_db()
    db.add_xp(user_id, XP_REWARDS.get("vorstellen", 30) + score * 5, "vorstellen", f"Ball: {score}/7")

    # Xatolarni saqlash
    for error in result.get("grammar_errors", []):
        if error.get("xato") and error.get("togri"):
            db.add_mistake(
                user_id=user_id,
                user_input=error["xato"],
                correct_form=error["togri"],
                mistake_type="vorstellen_grammar",
            )

    # Natija matni
    text = (
        f"🎤 *Vorstellen Tahlili*\n\n"
        f"{stars}\n"
        f"{yulduz_text}\n\n"
        f"📊 *Ball: {score}/7*\n"
        f"📚 *Grammatika: {result.get('grammar_score', 5)}/10*\n"
        f"🗣️ *So'z boyligi: {result.get('vocabulary_score', 5)}/10*\n"
        f"💬 *Suvliklik: {result.get('fluency_score', 5)}/10*\n\n"
        f"🎯 *Aniqlangan daraja: {level}*\n\n"
    )

    # Qoldirilgan savollar
    if missed:
        text += f"⚠️ *Qoldirilgan savollar: {', '.join(map(str, missed))}*\n"
        text += "❌ Bu ballingizga ta'sir qildi!\n\n"
        # Qoldirilgan savollar uchun maslahat
        text += "📌 *Maslahat:*\n"
        for m in missed:
            savol = VORSTELLEN_SAVOLLAR[m-1]
            text += f"{m}. {esc_md(savol['mavzu'])} - {esc_md(savol['shablon_a2'][0])}\n"
        text += "\n"

    # Yaxshi jihatlar
    good_points = result.get("good_points", [])
    if good_points:
        text += "✅ *Yaxshi jihatlar:*\n"
        for point in good_points[:3]:
            text += f"• {esc_md(point)}\n"
        text += "\n"

    text += "*Quyidagi bo'limlardan birini tanlang:*"

    # Save for later use
    context.user_data["vs_result"] = result
    context.user_data["vs_score"] = score
    context.user_data["vs_level"] = level

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=vorstellen_result_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=vorstellen_result_keyboard())

    return VORSTELLEN_RESULT


async def vs_show_section_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tushuntirish/Tarjima/Yaxshilash ko'rsatish - yangi"""
    query = update.callback_query
    await query.answer()

    result = context.user_data.get("vs_result", {})
    section = query.data.replace("vs_show_", "")

    if section == "tushuntirish":
        title = "💡 *Tushuntirish*"
        text = result.get("tushuntirish", "Ma'lumot yo'q")
    elif section == "tarjima":
        title = "🌐 *To'g'ri variant*"
        text = result.get("tarjima", "Ma'lumot yo'q")
    elif section == "yaxshilash":
        return await vs_improve_menu(update, context)
    else:
        return VORSTELLEN_RESULT

    await query.edit_message_text(
        f"{title}\n\n{esc_md(text)}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💡 Tushuntirish", callback_data="vs_show_tushuntirish"),
                InlineKeyboardButton("🌐 Tarjima", callback_data="vs_show_tarjima"),
                InlineKeyboardButton("✅ Yaxshilash", callback_data="vs_show_yaxshilash"),
            ],
            [InlineKeyboardButton("📄 PDF yuklash", callback_data="vorstellen_pdf")],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
            [InlineKeyboardButton("🔁 Qayta urinish", callback_data="ai_vorstellen")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    )
    return VORSTELLEN_RESULT


async def vs_improve_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Yaxshilash - daraja tanlash"""
    query = update.callback_query
    await query.answer()

    detected = context.user_data.get("vs_level", "A1")

    await query.edit_message_text(
        f"✅ *Yaxshilash*\n\n"
        f"AI aniqlagan darajangiz: *{detected}*\n\n"
        f"Qaysi darajada mukammal variant ko'rishni xohlaysiz?\n\n"
        f"🟢 *A1* - Oddiy, qisqa\n"
        f"🟢 *A2* - O'rta\n"
        f"🟡 *B1* - Murakkab\n"
        f"🟡 *B2* - Professional\n\n"
        f"*Tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=vorstellen_level_keyboard()
    )
    return VORSTELLEN_RESULT


async def vs_improve_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tanlangan darajada mukammal variant"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("vorstellen_level_", "")
    result = context.user_data.get("vs_result", {})

    # Darajaga mos yaxshilash
    improve_key = f"yaxshilash_{level}"
    improved_text = result.get(improve_key, "")

    if not improved_text:
        # AI dan so'rash
        all_text = "\n".join([f"Savol {a['q_num']}: {a['text']}" for a in context.user_data.get("vorstellen", {}).get("answers", []) if a.get("text")])

        ai_result = await groq_chat([
            {"role": "system", "content": (
                f"Siz nemis tili o'qituvchisisiz. Foydalanuvchi javoblarini {level.upper()} darajasida "
                f"mukammallashtiring. Faqat nemischa javob bering. 7 ta savolning barchasini qamrovchi uzun matn yarating."
            )},
            {"role": "user", "content": f"Javoblarni {level.upper()} darajasida mukammallashtir:\n{all_text}"}
        ], max_tokens=1024)

        improved_text = ai_result

    # Save for PDF
    context.user_data["vs_improved_text"] = improved_text
    context.user_data["vs_improved_level"] = level

    await query.edit_message_text(
        f"✨ *{level.upper()} darajasida mukammal variant:*\n\n"
        f"{esc_md(improved_text)}\n\n"
        f"💡 *Maslahat:* Bu matnni yodlang!\n"
        f"📄 PDF shaklda yuklab olishingiz mumkin.",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 PDF yuklash", callback_data="vorstellen_pdf")],
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vs_speak")],
            [InlineKeyboardButton("🔄 Boshqa daraja", callback_data="vs_show_yaxshilash")],
            [InlineKeyboardButton("🔁 Qayta urinish", callback_data="ai_vorstellen")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    )
    return VORSTELLEN_RESULT


async def vs_speak_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovozda o'qish - yangi"""
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")

    improved_text = context.user_data.get("vs_improved_text", "")
    if not improved_text:
        result = context.user_data.get("vs_result", {})
        improved_text = result.get("tarjima", "")

    if improved_text:
        await speak_text(query, improved_text, voice="female", speed=0.9)

    return VORSTELLEN_RESULT


async def vorstellen_pdf_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mukammal PDF yaratish va yuborish - reportlab bilan"""
    query = update.callback_query
    await query.answer("📄 PDF yaratilmoqda...")

    v_data = context.user_data.get("vorstellen", {})
    result = context.user_data.get("vs_result", {})
    level = context.user_data.get("vs_improved_level", context.user_data.get("vs_level", "A1")).upper()
    score = context.user_data.get("vs_score", 0)
    improved_text = context.user_data.get("vs_improved_text", "")
    user_id = query.from_user.id

    if not improved_text:
        all_text = "\n".join([f"Savol {a['q_num']}: {a['text']}" for a in v_data.get("answers", []) if a.get("text")])
        improved_text = await groq_chat([
            {"role": "system", "content": (
                f"Nemis tili o'qituvchisi. Javoblarni {level} darajasida mukammallashtir. "
                f"Faqat nemischa, uzun va to'liq matn."
            )},
            {"role": "user", "content": f"Mukammallashtir:\n{all_text}"}
        ], max_tokens=1024)
        context.user_data["vs_improved_text"] = improved_text

    # Foydalanuvchi javoblari
    user_answers_list = [
        f"{a['q_num']}. {a.get('text', '')}" for a in v_data.get("answers", []) if a.get("text")
    ]

    # Maslahatlar
    tips = [
        "Bu matnni yodlang va har kuni ovozda mashq qiling.",
        "Har kuni 5 marta takrorlang — muskul xotirasi hosil bo'ladi.",
        "Ovozingizni yozib, so'ng tinglang va taqqoslang.",
        "Imtihonda 15 soniya tayyorlanish vaqtingiz bor — tez o'ylang!",
        "7 ta bo'limning barchasini albatta yoritib bering.",
    ]

    # ── REPORTLAB IMPORT ──
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import (
            Paragraph, Spacer, Table, TableStyle, HRFlowable,
            BaseDocTemplate, Frame, PageTemplate as PT,
        )
        import io as _io

        BLACK = colors.HexColor("#1a1a1a")
        RED   = colors.HexColor("#CC0000")
        GOLD  = colors.HexColor("#D4A017")
        DARK  = colors.HexColor("#2C2C2C")
        LGRAY = colors.HexColor("#F5F5F5")
        WHITE = colors.white

        PAGE_W, PAGE_H = A4
        MARGIN_L = 2.0 * cm
        MARGIN_R = 2.0 * cm
        MARGIN_T = 2.2 * cm
        MARGIN_B = 2.0 * cm
        CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

        LOGO_SIZE = 3.0 * cm
        logo_x = MARGIN_L
        logo_y = PAGE_H - MARGIN_T - LOGO_SIZE - 4
        badge_x = PAGE_W - MARGIN_R - 2.4 * cm
        badge_y = logo_y + LOGO_SIZE * 0.2
        sep_y   = logo_y - 0.3 * cm
        stars_y = sep_y - 0.7 * cm
        CONTENT_START_Y = stars_y - 1.4 * cm

        LOGO_PATH = '/home/claude/logo_transparent.png'

        # Ballar
        grammar_score  = result.get("grammar_score", 0)
        vocab_score    = result.get("vocabulary_score", 0)
        fluency_score  = result.get("fluency_score", 0)
        detected_lvl   = result.get("detected_level", level)

        def draw_page(c, doc):
            bar_h = 6
            c.setFillColor(BLACK); c.rect(0, PAGE_H-bar_h, PAGE_W/3, bar_h, fill=1, stroke=0)
            c.setFillColor(RED);   c.rect(PAGE_W/3, PAGE_H-bar_h, PAGE_W/3, bar_h, fill=1, stroke=0)
            c.setFillColor(GOLD);  c.rect(PAGE_W*2/3, PAGE_H-bar_h, PAGE_W/3, bar_h, fill=1, stroke=0)
            c.setFillColor(GOLD);  c.rect(0, 0, PAGE_W/3, bar_h, fill=1, stroke=0)
            c.setFillColor(RED);   c.rect(PAGE_W/3, 0, PAGE_W/3, bar_h, fill=1, stroke=0)
            c.setFillColor(BLACK); c.rect(PAGE_W*2/3, 0, PAGE_W/3, bar_h, fill=1, stroke=0)
            # Logo
            import os
            if os.path.exists(LOGO_PATH):
                try:
                    c.drawImage(LOGO_PATH, logo_x, logo_y, width=LOGO_SIZE, height=LOGO_SIZE,
                                mask='auto', preserveAspectRatio=True)
                except Exception:
                    pass
            # Sarlavha
            c.setFont("Helvetica-Bold", 22); c.setFillColor(BLACK)
            c.drawString(logo_x + LOGO_SIZE + 0.5*cm, logo_y + LOGO_SIZE*0.6, "VORSTELLEN")
            c.setFont("Helvetica-Bold", 11); c.setFillColor(RED)
            c.drawString(logo_x + LOGO_SIZE + 0.5*cm, logo_y + LOGO_SIZE*0.25,
                         "Mukammal Natija  |  Deutsch Meister Pro")
            # Badge
            c.setFillColor(RED); c.roundRect(badge_x, badge_y, 2.4*cm, 1.0*cm, 5, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(badge_x + 1.2*cm, badge_y + 0.22*cm, level)
            # Chiziq
            c.setStrokeColor(GOLD); c.setLineWidth(2)
            c.line(MARGIN_L, sep_y, PAGE_W - MARGIN_R, sep_y)
            # Yulduzlar (unicode emas, ASCII)
            c.setFont("Helvetica-Bold", 13); c.setFillColor(GOLD)
            stars_str = "* " * score + "o " * (7 - score)
            c.drawString(MARGIN_L, stars_y, stars_str)
            yulduz_map = {7:"Mukammal! Barcha bolimlar yoritilgan.",
                          6:"Yaxshi! 1 ta bolim yetishmayapti.",
                          5:"Orta. 2 ta bolim qoldirilgan.",
                          4:"Qoniqarli. 3 ta bolim yetishmayapti.",
                          3:"Kam. 4 ta bolim qoldirilgan.",
                          2:"Juda kam. 5 ta bolim yetishmayapti.",
                          1:"Yomon. 6 ta bolim qoldirilgan."}
            c.setFont("Helvetica", 9); c.setFillColor(DARK)
            c.drawString(MARGIN_L, stars_y - 0.42*cm, yulduz_map.get(score, ""))

        class VorstellenDoc(BaseDocTemplate):
            def __init__(self, buf, **kw):
                super().__init__(buf, **kw)
                frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W, CONTENT_START_Y - MARGIN_B,
                              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='main')
                self.addPageTemplates([PT('first', [frame], onPage=draw_page)])

        def sec_h(text, color=RED):
            return Paragraph(f"<b>{text}</b>",
                ParagraphStyle("SH", fontName="Helvetica-Bold", fontSize=10.5,
                               textColor=color, spaceBefore=6, spaceAfter=3, leading=15,
                               backColor=LGRAY, borderPad=3))

        def body(text, size=9.5):
            return Paragraph(text,
                ParagraphStyle("BP", fontName="Helvetica", fontSize=size,
                               textColor=DARK, leading=14, spaceAfter=2))

        def german(text):
            return Paragraph(f"<i>{text}</i>",
                ParagraphStyle("GP", fontName="Helvetica-Oblique", fontSize=10,
                               textColor=BLACK, leading=16, spaceAfter=3))

        # ── STORY ──
        story = []

        # Ball jadvali
        cw = CONTENT_W / 4
        tbl = Table([
            ["Korsatkich", "Ball", "Korsatkich", "Ball"],
            ["Umumiy ball", f"{score}/7", "Daraja", detected_lvl],
            ["Grammatika",  f"{grammar_score}/10", "Soz boyligi", f"{vocab_score}/10"],
            ["Ravonlik",    f"{fluency_score}/10", "", ""],
        ], colWidths=[cw*1.6, cw*0.9, cw*1.6, cw*0.9])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), BLACK), ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,0), 9),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"), ("FONTSIZE", (0,1), (-1,-1), 10),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [LGRAY, WHITE]),
            ("BACKGROUND",    (2,1), (3,1), RED), ("TEXTCOLOR", (2,1), (3,1), WHITE),
            ("FONTNAME",      (2,1), (3,1), "Helvetica-Bold"), ("FONTSIZE", (2,1), (3,1), 11),
            ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING",    (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.3*cm))

        # Javoblar
        story.append(sec_h("SIZNING JAVOBLARINGIZ", BLACK))
        story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD))
        story.append(Spacer(1, 0.08*cm))
        for line in user_answers_list:
            story.append(body(line))
        story.append(Spacer(1, 0.25*cm))

        # Mukammal variant
        story.append(sec_h(f"MUKAMMAL VARIANT ({level} DARAJASI)", RED))
        story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD))
        story.append(Spacer(1, 0.08*cm))
        for sent in improved_text.split(". "):
            s = sent.strip()
            if s:
                story.append(german(s + "."))
        story.append(Spacer(1, 0.25*cm))

        # Maslahatlar
        story.append(sec_h("MASLAHATLAR", DARK))
        story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD))
        story.append(Spacer(1, 0.08*cm))
        for i, tip in enumerate(tips, 1):
            story.append(body(f"{i}. {tip}"))

        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=2, color=RED))
        story.append(Paragraph(
            "@Muminov_Abdullokh  |  t.me/sprechenmitspass  |  Deutsch Meister Pro",
            ParagraphStyle("Footer", fontName="Helvetica", fontSize=8,
                           textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceBefore=4)
        ))

        # ── BUILD ──
        buf = _io.BytesIO()
        doc = VorstellenDoc(
            buf, pagesize=A4,
            rightMargin=MARGIN_R, leftMargin=MARGIN_L,
            topMargin=PAGE_H - CONTENT_START_Y, bottomMargin=MARGIN_B,
        )
        doc.build(story)
        buf.seek(0)

        await query.message.reply_document(
            document=buf,
            filename=f"Vorstellen_{level}_{user_id}.pdf",
            caption=f"✅ *Vorstellen \\- {level} darajasida mukammal PDF*\n\n"
                    f"📄 Yuklab oling va yodlang\\!\n"
                    f"@Muminov\\_Abdullokh \\| t\\.me/sprechenmitspass",
            parse_mode="MarkdownV2"
        )

    except ImportError:
        # Reportlab yo'q bo'lsa txt yuboramiz
        from io import BytesIO as _BIO
        content = f"VORSTELLEN - {level}\n\nJAVOBLAR:\n"
        content += "\n".join(user_answers_list)
        content += f"\n\nMUKAMMAL VARIANT:\n{improved_text}"
        buf = _BIO(content.encode("utf-8"))
        await query.message.reply_document(
            document=buf, filename=f"Vorstellen_{level}_{user_id}.txt",
            caption=f"✅ Vorstellen - {level}"
        )

    return VORSTELLEN_RESULT


vorstellen_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(vorstellen_menu, pattern="^ai_vorstellen$"),
        CallbackQueryHandler(vorstellen_menu, pattern="^vorstellen_menu$"),
    ],
    states={
        VORSTELLEN_MENU: [
            CallbackQueryHandler(vorstellen_start_new, pattern="^vorstellen_start$"),
            CallbackQueryHandler(vorstellen_rules, pattern="^vorstellen_rules$"),
            CallbackQueryHandler(vorstellen_templates, pattern="^vorstellen_templates$"),
            CallbackQueryHandler(vorstellen_template_show, pattern="^vorstellen_template_"),
        ],
        VORSTELLEN_PREPARE: [
            CallbackQueryHandler(vorstellen_start_new, pattern="^vorstellen_go$"),
            CallbackQueryHandler(vorstellen_templates, pattern="^vorstellen_templates$"),
        ],
        VORSTELLEN_Q1: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_Q2: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_Q3: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_Q4: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_Q5: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_Q6: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_Q7: [MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, vorstellen_process_new)],
        VORSTELLEN_RESULT: [
            CallbackQueryHandler(vs_show_section_new, pattern="^vs_show_tushuntirish$"),
            CallbackQueryHandler(vs_show_section_new, pattern="^vs_show_tarjima$"),
            CallbackQueryHandler(vs_show_section_new, pattern="^vs_show_yaxshilash$"),
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
    },
    fallbacks=[
        CallbackQueryHandler(vorstellen_menu, pattern="^vorstellen_menu$"),
        CallbackQueryHandler(ai_mentor_menu_handler, pattern="^ai_mentor_menu$"),
    ],
    map_to_parent={
        VORSTELLEN_MENU: AI_MENTOR_MENU,
    }
)

async def erfahrungen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Erfahrungen — faqat B2/C1"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    user = db.get_or_create_user(user_id)
    level = user.get("current_level", "a1")

    if level in ["a1", "a2", "b1"]:
        await query.edit_message_text(
            f"💬 *Erfahrungen* faqat *B2 va C1* darajalarida mavjud\\!\n\n"
            f"Sizning darajangiz: {esc_md(LEVEL_LABELS.get(level, level))}\n\n"
            f"Avval darajangizni oshiring\\! 📚",
            parse_mode="MarkdownV2",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    rows = []
    for key, topic in ERFAHRUNGEN_TOPICS.items():
        rows.append([InlineKeyboardButton(topic["name"], callback_data=f"erf_topic_{key}")])
    rows.append([InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")])

    await query.edit_message_text(
        "💬 *Erfahrungen \\- Mavzu Laboratoriyasi*\n\n"
        "*10 ta mavzu, 3 ta qiyinlik darajasi*\n\n"
        "🟢 Oddiy | 🟡 O'rta | 🔴 Qiyin\n\n"
        "Mavzu tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return ERFAHRUNGEN_MENU


async def erfahrungen_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    topic_key = query.data.replace("erf_topic_", "")
    context.user_data["erfahrungen_topic"] = topic_key
    topic = ERFAHRUNGEN_TOPICS.get(topic_key)
    if not topic:
        return ERFAHRUNGEN_MENU

    await query.edit_message_text(
        f"{topic['name']}\n\n*Qiyinlik darajasini tanlang:*\n\n"
        f"🟢 *Oddiy:* {esc_md(topic.get('easy', ''))}\n\n"
        f"🟡 *O'rta:* {esc_md(topic.get('medium', ''))}\n\n"
        f"🔴 *Qiyin:* {esc_md(topic.get('hard', ''))}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 Oddiy", callback_data=f"erf_diff_{topic_key}_easy"),
                InlineKeyboardButton("🟡 O'rta", callback_data=f"erf_diff_{topic_key}_medium"),
                InlineKeyboardButton("🔴 Qiyin", callback_data=f"erf_diff_{topic_key}_hard"),
            ],
            [InlineKeyboardButton("↩️ Mavzularga qaytish", callback_data="ai_erfahrungen")],
        ]),
    )
    return ERFAHRUNGEN_DIFFICULTY


async def erfahrungen_start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    topic_key = parts[2]
    difficulty = parts[3]

    topic = ERFAHRUNGEN_TOPICS.get(topic_key)
    question = topic.get(difficulty, topic.get("easy", "Erzählen Sie von sich.")) if topic else "Erzählen Sie von sich."

    context.user_data["erfahrungen"] = {
        "topic": topic_key, "difficulty": difficulty,
        "messages": [], "turns": 0,
    }

    system_prompt = (
        f"Sie sind ein deutscher Sprachlehrer für B2/C1 Niveau. "
        f"Das Thema ist: {topic['name'] if topic else 'Allgemein'}. "
        f"Sprechen Sie Deutsch, erklären Sie komplexe Punkte auf Uzbekisch."
    )

    ai_response = await groq_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Mavzu: {topic_key}, Qiyinlik: {difficulty}\nSavol: {question}"},
    ], max_tokens=512)

    context.user_data["erfahrungen"]["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": ai_response},
    ]

    await query.edit_message_text(
        f"💬 *Erfahrungen: {esc_md(topic['name'] if topic else 'Mavzu')}*\n"
        f"Qiyinlik: {difficulty.upper()}\n\n"
        f"📝 *Savol:*\n{esc_md(question)}\n\n"
        f"{esc_md(ai_response)}\n\n"
        f"*Javobingizni yozing yoki ovoz yuboring\\!*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="erf_finish")],
        ])
    )
    return ERFAHRUNGEN_CHAT


async def erfahrungen_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    erf_data = context.user_data.get("erfahrungen", {})
    turns = erf_data.get("turns", 0)

    if update.callback_query and update.callback_query.data == "erf_finish":
        return await erfahrungen_result(update, context)

    # Ovozli yoki matnli
    if update.message and (update.message.voice or update.message.audio):
        loading = await update.message.reply_text("🎙️ *Ovoz tahlil qilinmoqda...*", parse_mode="MarkdownV2")
        user_message = await listen_to_voice(update)
        await loading.delete()
    elif update.message and update.message.text:
        user_message = update.message.text.strip()
    else:
        return ERFAHRUNGEN_CHAT

    erf_data["messages"].append({"role": "user", "content": user_message})
    turns += 1
    erf_data["turns"] = turns

    if turns >= 5:
        return await erfahrungen_result(update, context)

    messages = erf_data["messages"][:] + [{
        "role": "user",
        "content": f"Foydalanuvchi javobi ({turns}/5):\n{user_message}\nKeyingi savol bering!"
    }]

    ai_response = await groq_chat(messages, max_tokens=512)
    erf_data["messages"].append({"role": "assistant", "content": ai_response})

    await update.message.reply_text(
        f"{esc_md(ai_response)}\n\n*\\({turns}/5\\)* \\-\\> Javobingizni yozing:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="erf_finish")],
        ])
    )
    return ERFAHRUNGEN_CHAT


async def erfahrungen_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    erf_data = context.user_data.get("erfahrungen", {})
    messages = erf_data.get("messages", [])
    turns = erf_data.get("turns", 0)

    await (update.callback_query.edit_message_text if update.callback_query
           else update.message.reply_text)(
        "🧠 *AI yakuniy tahlil qilmoqda\\.\\.\\.*", parse_mode="MarkdownV2"
    )

    result = await groq_json(messages + [{
        "role": "user",
        "content": (
            "Suhbat tugadi. JSON tahlil bering: {"
            '"score": 0-10, "grammar_score": 0-10, "vocabulary_score": 0-10, '
            '"fluency_score": 0-10, "feedback": "tahlil o\'zbek tilida", '
            '"good_points": ["..."], "improvements": ["..."]}'
        )
    }], max_tokens=1024)

    user_id = (update.callback_query.from_user.id if update.callback_query else update.effective_user.id)
    db = get_db()
    score = result.get("score", 5)
    db.add_xp(user_id, XP_REWARDS.get("ai_conversation", 50), "erfahrungen", f"Ball: {score}/10")

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
        f"🎁 *+{XP_REWARDS.get('ai_conversation', 50)} XP*"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard())
    return AI_MENTOR_MENU


# ==================== 4. MISTAKE BANK ====================

async def mistake_bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        text += "Xatolaringizni ko'rib chiqing va mini\\-darslarni o'ting\\! 📚"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Xatolar ro'yxati", callback_data="mistake_list")],
            [InlineKeyboardButton("🎲 Tasodifiy mini-dars", callback_data="mistake_random")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    else:
        text += "Ajoyib\\! Sizda faol xatolar yo'q\\! 🎉"
        keyboard = ai_mentor_menu_keyboard()

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return MISTAKE_BANK_MENU


async def mistake_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    mistakes = db.get_mistakes(user_id, mastered=False, limit=10)

    if not mistakes:
        await query.edit_message_text(
            "✅ *Barcha xatolar o'zlashtirilgan\\!*\n\nAjoyib ish\\! 🎉",
            parse_mode="MarkdownV2",
            reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    text = "🔧 *Sizning xatolaringiz:*\n\n"
    keyboard_rows = []
    for i, m in enumerate(mistakes[:5], 1):
        text += f"{i}\\. *{esc_md(m['user_input'])}* → {esc_md(m['correct_form'])}\n"
        text += f"   _{esc_md(m['mistake_type'])}_\n\n"
        keyboard_rows.append([InlineKeyboardButton(
            f"{i}. {m['user_input'][:20]} → Mini-dars",
            callback_data=f"mistake_lesson_{m['id']}"
        )])

    keyboard_rows.append([InlineKeyboardButton("↩️ Xato bankiga qaytish", callback_data="ai_mistake_bank")])
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard_rows))
    return MISTAKE_BANK_MENU


async def mistake_mini_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_lesson_", ""))
    db = get_db()
    mistake = db.get_mistake_by_id(mistake_id)

    if not mistake:
        await query.edit_message_text("❌ Xato topilmadi.", reply_markup=ai_mentor_menu_keyboard())
        return AI_MENTOR_MENU

    context.user_data["current_mistake_id"] = mistake_id
    context.user_data["mistake_speak_text"] = mistake.get("correct_form", "")

    lesson_text = mistake.get("mini_lesson", "")
    if not lesson_text:
        result = await groq_json([
            {"role": "system", "content": "Siz nemis tili grammatika o'qituvchisisiz."},
            {"role": "user", "content": (
                f'Xato: "{mistake["user_input"]}" To\'g\'ri: "{mistake["correct_form"]}" '
                f'Turi: {mistake["mistake_type"]}\n'
                'JSON: {"rule": "grammatik qoida", "explanation": "tushuntirish o\'zbek tilida", '
                '"example_correct": "3 ta to\'g\'ri misol", "example_wrong": "3 ta noto\'g\'ri misol", '
                '"tip": "xotirada saqlash maslahat"}'
            )},
        ], max_tokens=1024)

        lesson_text = (
            f"📚 *Grammatik qoida:*\n{esc_md(result.get('rule', 'N/A'))}\n\n"
            f"📝 *Tushuntirish:*\n{esc_md(result.get('explanation', 'N/A'))}\n\n"
            f"✅ *To'g'ri misollar:*\n{esc_md(result.get('example_correct', 'N/A'))}\n\n"
            f"❌ *Noto'g'ri misollar:*\n{esc_md(result.get('example_wrong', 'N/A'))}\n\n"
            f"💡 *Maslahat:*\n{esc_md(result.get('tip', 'N/A'))}"
        )

    await query.edit_message_text(
        f"🔧 *Mini-dars*\n\n"
        f"❌ *Sizning xato: {esc_md(mistake['user_input'])}*\n"
        f"✅ *To'g'ri: {esc_md(mistake['correct_form'])}*\n"
        f"📌 *Turi: {esc_md(mistake['mistake_type'])}*\n\n"
        f"{lesson_text}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data=f"mistake_speak_{mistake_id}")],
            [InlineKeyboardButton("✏️ Mashqlarni bajarish", callback_data=f"mistake_practice_{mistake_id}")],
            [InlineKeyboardButton("✨ Yaxshilash", callback_data=f"mistake_improve_{mistake_id}")],
            [InlineKeyboardButton("✅ O'zlashtirdim", callback_data=f"mistake_master_{mistake_id}")],
            [InlineKeyboardButton("↩️ Xatolar ro'yxati", callback_data="mistake_list")],
        ])
    )
    return MISTAKE_MINILESSON


async def mistake_speak_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xatoning to'g'ri versiyasini ovozda o'qish"""
    query = update.callback_query
    await query.answer("🔊 Ovoz tayyorlanmoqda...")

    mistake_id = int(query.data.replace("mistake_speak_", ""))
    db = get_db()
    mistake = db.get_mistake_by_id(mistake_id)

    if mistake and mistake.get("correct_form"):
        await speak_text(query, mistake["correct_form"], voice="female", speed=0.85)

    return MISTAKE_MINILESSON


async def mistake_improve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xato bo'yicha AI dan to'liq tushuntirish"""
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_improve_", ""))
    db = get_db()
    mistake = db.get_mistake_by_id(mistake_id)

    if not mistake:
        return MISTAKE_BANK_MENU

    result = await groq_json([
        {"role": "system", "content": "Nemis tili o'qituvchisi."},
        {"role": "user", "content": (
            f'Xato: "{mistake["user_input"]}" To\'g\'ri: "{mistake["correct_form"]}"\n'
            'JSON: {"tafsilot": "batafsil tushuntirish o\'zbek tilida (5-7 gap)", '
            '"sinonimlar": ["sinon1", "sinon2"], '
            '"misollar": ["misol 1", "misol 2", "misol 3"]}'
        )},
    ])

    sinonimlar = ", ".join(result.get("sinonimlar", []))
    misollar = "\n".join([f"• {esc_md(m)}" for m in result.get("misollar", [])])

    await query.edit_message_text(
        f"✨ *To'liq tushuntirish*\n\n"
        f"❌ *Xato:* {esc_md(mistake['user_input'])}\n"
        f"✅ *To'g'ri:* {esc_md(mistake['correct_form'])}\n\n"
        f"📝 *Tafsilot:*\n{esc_md(result.get('tafsilot', ''))}\n\n"
        f"🔁 *Sinonimlar:* {esc_md(sinonimlar)}\n\n"
        f"📌 *Misollar:*\n{misollar}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data=f"mistake_speak_{mistake_id}")],
            [InlineKeyboardButton("✅ O'zlashtirdim", callback_data=f"mistake_master_{mistake_id}")],
            [InlineKeyboardButton("↩️ Xatolar ro'yxati", callback_data="mistake_list")],
        ])
    )
    return MISTAKE_MINILESSON


async def mistake_practice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_practice_", ""))
    db = get_db()
    mistake = db.get_mistake_by_id(mistake_id)

    if not mistake:
        return MISTAKE_BANK_MENU

    result = await groq_json([
        {"role": "system", "content": "Nemis tili mashq yaratuvchisi."},
        {"role": "user", "content": (
            f'Xato: "{mistake["user_input"]}" To\'g\'ri: "{mistake["correct_form"]}"\n'
            'JSON: {"exercises": [{"task": "mashq", "answer": "javob"}, '
            '{"task": "mashq", "answer": "javob"}, {"task": "mashq", "answer": "javob"}]}'
        )},
    ])

    exercises = result.get("exercises", [
        {"task": "To'g'ri variantni yozing:", "answer": mistake["correct_form"]},
    ])

    context.user_data["mistake_exercises"] = {
        "exercises": exercises, "current": 0,
        "correct": 0, "mistake_id": mistake_id,
    }

    ex = exercises[0]
    await query.edit_message_text(
        f"✏️ *Mashq 1/{len(exercises)}*\n\n{esc_md(ex['task'])}\n\nJavobingizni yozing:",
        parse_mode="MarkdownV2",
    )
    return MISTAKE_PRACTICE


async def mistake_practice_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ex_data = context.user_data.get("mistake_exercises", {})
    current = ex_data.get("current", 0)
    exercises = ex_data.get("exercises", [])

    if not exercises or current >= len(exercises):
        return MISTAKE_BANK_MENU

    user_answer = update.message.text.strip()
    correct_answer = exercises[current].get("answer", "")
    is_correct = user_answer.lower().strip() in correct_answer.lower() or correct_answer.lower() in user_answer.lower()

    if is_correct:
        ex_data["correct"] += 1
        await update.message.reply_text(f"✅ *To'g'ri\\!* `{esc_md(correct_answer)}`", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(
            f"❌ *Noto'g'ri*\nSiz: `{esc_md(user_answer)}`\nTo'g'ri: `{esc_md(correct_answer)}`",
            parse_mode="MarkdownV2"
        )

    current += 1
    ex_data["current"] = current

    if current >= len(exercises):
        correct_count = ex_data["correct"]
        total = len(exercises)
        mistake_id = ex_data["mistake_id"]
        db = get_db()
        db.review_mistake(mistake_id)
        db.add_xp(update.effective_user.id, XP_REWARDS.get("mistake_corrected", 5),
                  "mistake_practice", f"{correct_count}/{total}")

        if correct_count == total:
            db.master_mistake(mistake_id)
            await update.message.reply_text(
                f"🎉 *Barcha mashqlar bajarildi\\!* {correct_count}/{total}\n\n"
                f"✅ Bu xato o'zlashtirildi\\!\n🎁 *+{XP_REWARDS.get('mistake_corrected', 5)} XP*",
                parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                f"📊 *Natija: {correct_count}/{total}*\n\nYana mashq qilishingiz mumkin\\!",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Qayta mashq", callback_data=f"mistake_practice_{mistake_id}")],
                    [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
                ])
            )
        return AI_MENTOR_MENU

    ex = exercises[current]
    await update.message.reply_text(
        f"✏️ *Mashq {current + 1}/{len(exercises)}*\n\n{esc_md(ex['task'])}\n\nJavobingizni yozing:",
        parse_mode="MarkdownV2",
    )
    return MISTAKE_PRACTICE


async def mistake_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    mistake_id = int(query.data.replace("mistake_master_", ""))
    db = get_db()
    db.master_mistake(mistake_id)
    db.add_xp(query.from_user.id, XP_REWARDS.get("mistake_corrected", 5), "mistake_mastered")

    await query.edit_message_text(
        f"✅ *Xato o'zlashtirildi\\!* 🎉\n\n🎁 *+{XP_REWARDS.get('mistake_corrected', 5)} XP*",
        parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU


async def mistake_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    mistakes = db.get_mistakes(user_id, mastered=False, limit=100)

    if not mistakes:
        await query.edit_message_text(
            "✅ *Barcha xatolar o'zlashtirilgan\\!*\n\nAjoyib ish\\! 🎉",
            parse_mode="MarkdownV2", reply_markup=ai_mentor_menu_keyboard(),
        )
        return AI_MENTOR_MENU

    mistake = random.choice(mistakes)
    context.user_data["current_mistake_id"] = mistake["id"]

    result = await groq_json([
        {"role": "system", "content": "Nemis tili o'qituvchisi."},
        {"role": "user", "content": (
            f'Xato: "{mistake["user_input"]}" To\'g\'ri: "{mistake["correct_form"]}"\n'
            'JSON: {"rule": "grammatik qoida (qisqa)", '
            '"explanation": "tushuntirish o\'zbek tilida qisqa", "tip": "maslahat"}'
        )},
    ])

    await query.edit_message_text(
        f"🎲 *Tasodifiy mini-dars*\n\n"
        f"❌ *Xato: {esc_md(mistake['user_input'])}*\n"
        f"✅ *To'g'ri: {esc_md(mistake['correct_form'])}*\n\n"
        f"📚 *Qoida:*\n{esc_md(result.get('rule', 'N/A'))}\n\n"
        f"📝 *Tushuntirish:*\n{esc_md(result.get('explanation', 'N/A'))}\n\n"
        f"💡 *Maslahat:*\n{esc_md(result.get('tip', 'N/A'))}",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data=f"mistake_speak_{mistake['id']}")],
            [InlineKeyboardButton("✏️ Mashq qilish", callback_data=f"mistake_practice_{mistake['id']}")],
            [InlineKeyboardButton("✅ O'zlashtirdim", callback_data=f"mistake_master_{mistake['id']}")],
            [InlineKeyboardButton("🎲 Boshqa mini-dars", callback_data="mistake_random")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    )
    return MISTAKE_MINILESSON


# ==================== 5. OVOZLI LUG'AT (TO'LIQ QAYTA YOZILGAN) ====================

async def voice_vocab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovozli lug'at — daraja tanlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📚 *Ovozli Lug'at*\n\n"
        "AI 25 ta so'z generatsiya qiladi\\.\n"
        "Test, Sprechen va Rolli o'yin imkoniyatlari\\!\n\n"
        "*Darajangizni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=level_select_keyboard("vocab_level"),
    )
    return VOICE_VOCAB_LEVEL


async def voice_vocab_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja tanlandi — mavzu tanlash"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("vocab_level_", "")
    context.user_data["vocab_level"] = level
    topics = VOCAB_TOPICS.get(level, [])

    await query.edit_message_text(
        f"📚 *Ovozli Lug'at — {level.upper()}*\n\n"
        f"*Mavzu tanlang \\({len(topics)} ta mavzu\\):*",
        parse_mode="MarkdownV2",
        reply_markup=topics_keyboard(topics, f"vocab_topic_{level}"),
    )
    return VOICE_VOCAB_TOPIC


async def voice_vocab_topic_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mavzu tanlandi — 25 ta so'z generatsiya"""
    query = update.callback_query
    await query.answer()

    # callback: vocab_topic_{level}_{idx}
    parts = query.data.split("_")
    level = parts[2]
    topic_idx = int(parts[3])
    topics = VOCAB_TOPICS.get(level, [])

    if topic_idx >= len(topics):
        return VOICE_VOCAB_TOPIC

    topic = topics[topic_idx]
    context.user_data["vocab_topic"] = topic
    context.user_data["vocab_level"] = level

    await query.edit_message_text(
        f"📚 *{esc_md(topic)}*\n\n⏳ *AI 25 ta so'z tayyorlamoqda\\.\\.\\.*",
        parse_mode="MarkdownV2",
    )

    # AI dan 25 so'z
    words_data = await _vocab_generate_words(level, topic)
    context.user_data["vocab_words"] = words_data

    if not words_data:
        await query.message.reply_text(
            "❌ So'zlar yuklanmadi. Qayta urinib ko'ring.",
            reply_markup=ai_mentor_menu_keyboard()
        )
        return AI_MENTOR_MENU

    # Ko'rsatish
    text = f"📚 *{esc_md(level.upper())} — {esc_md(topic)}* \\(25 ta so'z\\)\n\n"
    for i, w in enumerate(words_data[:25], 1):
        german = w.get("german", "")
        uzbek = w.get("uzbek", "")
        izoh = w.get("izoh", "")
        sinonimlar = ", ".join(w.get("sinonimlar", []))

        text += f"*{i}\\.* {esc_md(german)} — {esc_md(uzbek)}\n"
        if izoh:
            text += f"   📝 _{esc_md(izoh)}_\n"
        if sinonimlar:
            text += f"   🔁 _{esc_md(sinonimlar)}_\n"
        text += "\n"

        # Telegram 4096 belgi chegarasi — bo'laklash
        if len(text) > 3500 and i < 25:
            await query.message.reply_text(text, parse_mode="MarkdownV2")
            text = ""

    if text:
        await query.message.reply_text(
            text if text else f"📚 *{esc_md(topic)}*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ Test qilish", callback_data="vocab_test_start"),
                    InlineKeyboardButton("🎤 Sprechen", callback_data="vocab_sprechen"),
                    InlineKeyboardButton("🎭 Rolli o'yin", callback_data="vocab_roleplay"),
                ],
                [InlineKeyboardButton("🔁 Boshqa mavzu", callback_data=f"vocab_level_{level}")],
                [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
            ])
        )

    return VOICE_VOCAB_WORDS


async def _vocab_generate_words(level: str, topic: str) -> list:
    """AI dan 25 so'z generatsiya qilish"""
    result = await groq_json([
        {"role": "system", "content": (
            f"Sen nemis tili lug'at mutaxassisisiz. {level.upper()} darajasi uchun "
            f"'{topic}' mavzusida 25 ta so'z ber. "
            "Faqat JSON: {\"words\": [{\"german\": \"das Wort\", \"uzbek\": \"tarjima\", "
            "\"izoh\": \"qisqacha izoh o'zbek tilida (1 gap)\", \"sinonimlar\": []}]}"
        )},
        {"role": "user", "content": f"Level: {level}, Mavzu: {topic}, 25 ta so'z ber."}
    ], max_tokens=2048)
    return result.get("words", [])


async def vocab_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at testi boshlash"""
    query = update.callback_query
    await query.answer()

    words = context.user_data.get("vocab_words", [])
    if not words:
        return VOICE_VOCAB_WORDS

    context.user_data["vocab_test"] = {
        "words": words, "current": 0,
        "correct": 0, "direction": "uzb_to_de",
    }

    w = words[0]
    await query.edit_message_text(
        f"🧠 *Test 1/{len(words)}*\n\n"
        f"🇺🇿 *{esc_md(w.get('uzbek', ''))}* — Nemischasi nima?\n\n"
        f"_\\(Yozma yoki 🎙️ ovozli javob bering\\)_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="vocab_skip")],
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="vocab_test_finish")],
        ])
    )
    return VOICE_VOCAB_TEST


async def vocab_test_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Test javobini qayta ishlash"""
    test_data = context.user_data.get("vocab_test", {})
    words = test_data.get("words", [])
    current = test_data.get("current", 0)

    if update.callback_query:
        cb = update.callback_query
        await cb.answer()
        if cb.data == "vocab_test_finish":
            return await _vocab_test_result(cb, context)
        if cb.data == "vocab_skip":
            current += 1
            test_data["current"] = current
            if current >= len(words):
                return await _vocab_test_result(cb, context)
            w = words[current]
            await cb.edit_message_text(
                f"🧠 *Test {current + 1}/{len(words)}*\n\n"
                f"🇺🇿 *{esc_md(w.get('uzbek', ''))}* — Nemischasi nima?\n\n"
                f"_\\(Yozma yoki 🎙️ ovozli\\)_",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="vocab_skip")],
                    [InlineKeyboardButton("⏹️ Tugatish", callback_data="vocab_test_finish")],
                ])
            )
            return VOICE_VOCAB_TEST

    # Matn yoki ovoz
    if update.message and (update.message.voice or update.message.audio):
        loading = await update.message.reply_text("🎙️ *Tahlil qilinmoqda...*", parse_mode="MarkdownV2")
        user_answer = await listen_to_voice(update)
        await loading.delete()
    elif update.message and update.message.text:
        user_answer = update.message.text.strip()
    else:
        return VOICE_VOCAB_TEST

    if current >= len(words):
        return AI_MENTOR_MENU

    correct_word = words[current].get("german", "").lower()
    is_correct = (
        user_answer.lower().replace("der ", "").replace("die ", "").replace("das ", "") in
        correct_word.replace("der ", "").replace("die ", "").replace("das ", "")
        or correct_word.replace("der ", "").replace("die ", "").replace("das ", "") in
        user_answer.lower().replace("der ", "").replace("die ", "").replace("das ", "")
    )

    if is_correct:
        test_data["correct"] += 1
        db = get_db()
        db.add_xp(update.effective_user.id, XP_REWARDS.get("vocab_test_correct", 5),
                  "vocab_test", words[current].get("german", ""))
        await update.message.reply_text(
            f"✅ *To'g'ri\\!* `{esc_md(words[current].get('german', ''))}` \\+5 XP",
            parse_mode="MarkdownV2"
        )
    else:
        await update.message.reply_text(
            f"❌ *Noto'g'ri*\n"
            f"Siz: `{esc_md(user_answer)}`\n"
            f"To'g'ri: `{esc_md(words[current].get('german', ''))}`",
            parse_mode="MarkdownV2"
        )

    current += 1
    test_data["current"] = current

    if current >= len(words):
        correct_count = test_data["correct"]
        total = len(words)
        await update.message.reply_text(
            f"🏁 *Test tugadi\\!*\n\n"
            f"✅ *To'g'ri: {correct_count}/{total}*\n"
            f"⭐ *Ball: {int(correct_count/total*10)}/10*\n\n"
            f"🎁 *+{correct_count * XP_REWARDS.get('vocab_test_correct', 5)} XP*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Qayta test", callback_data="vocab_test_start")],
                [InlineKeyboardButton("🎤 Sprechen", callback_data="vocab_sprechen")],
                [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
            ])
        )
        return VOICE_VOCAB_WORDS

    w = words[current]
    await update.message.reply_text(
        f"🧠 *Test {current + 1}/{len(words)}*\n\n"
        f"🇺🇿 *{esc_md(w.get('uzbek', ''))}* — Nemischasi nima?\n\n"
        f"_\\(Yozma yoki 🎙️ ovozli\\)_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="vocab_skip")],
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="vocab_test_finish")],
        ])
    )
    return VOICE_VOCAB_TEST


async def _vocab_test_result(query, context) -> int:
    test_data = context.user_data.get("vocab_test", {})
    correct = test_data.get("correct", 0)
    total = len(test_data.get("words", [1]))
    await query.edit_message_text(
        f"🏁 *Test tugadi\\!*\n\n✅ *To'g'ri: {correct}/{total}*",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return VOICE_VOCAB_WORDS


async def vocab_sprechen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sprechen — 1 daqiqalik hikoya"""
    query = update.callback_query
    await query.answer()

    words = context.user_data.get("vocab_words", [])
    topic = context.user_data.get("vocab_topic", "Allgemein")
    level = context.user_data.get("vocab_level", "a1")

    if not words:
        return VOICE_VOCAB_WORDS

    await query.edit_message_text(
        f"🎤 *Sprechen — {esc_md(topic)}*\n\n⏳ *Hikoya tayyorlanmoqda\\.\\.\\.*",
        parse_mode="MarkdownV2",
    )

    word_list = ", ".join([w.get("german", "") for w in words[:25]])
    story = await groq_chat([
        {"role": "system", "content": (
            f"Siz nemis tili o'qituvchisisiz. {level.upper()} darajasi uchun "
            f"'{topic}' mavzusida 1 daqiqalik hikoya yaz. "
            f"Barcha quyidagi so'zlar ishtirok etsin: {word_list}. "
            "Hikoya natural, chiroyli va o'qish uchun qulay bo'lsin. "
            "Taxminan 120-150 so'z. Faqat nemischa yaz."
        )},
        {"role": "user", "content": "Hikoya yaz"}
    ], max_tokens=512)

    context.user_data["vocab_sprechen_story"] = story
    context.user_data["vocab_sprechen_started"] = False

    await query.message.reply_text(
        f"🎤 *Sprechen — {esc_md(topic)}*\n\n"
        f"*Hikoya \\(1 daqiqa\\):*\n\n{esc_md(story)}\n\n"
        f"_O'qib yodlang, keyin ovozda aytib bering\\!_",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Ovozda eshitish", callback_data="vocab_speak_story")],
            [InlineKeyboardButton("🎙️ O'zim aytib beraman", callback_data="vocab_sprechen_ready")],
            [InlineKeyboardButton("↩️ Orqaga", callback_data="ai_voice_vocab")],
        ])
    )
    return VOICE_VOCAB_SPRECHEN


async def vocab_speak_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hikoyani TTS bilan o'qish"""
    query = update.callback_query
    await query.answer("🔊 Hikoya o'qilmoqda...")

    story = context.user_data.get("vocab_sprechen_story", "")
    if story:
        await speak_text(query, story, voice="female", speed=0.9)

    return VOICE_VOCAB_SPRECHEN


async def vocab_sprechen_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi hikoyani aytishga tayyor"""
    query = update.callback_query
    await query.answer()

    context.user_data["vocab_sprechen_started"] = True
    await query.edit_message_text(
        "🎙️ *Endi siz aytib bering\\!*\n\n"
        "Hikoyani ovozli xabar sifatida yuboring\\.\n"
        "_Kamera o'chirilmaydi, faqat ovoz yuboring\\._",
        parse_mode="MarkdownV2",
    )
    return VOICE_VOCAB_SPRECHEN


async def vocab_sprechen_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi ovozini tahlil qilish"""
    if not context.user_data.get("vocab_sprechen_started"):
        return VOICE_VOCAB_SPRECHEN

    if not update.message or not (update.message.voice or update.message.audio):
        await update.message.reply_text("🎙️ Iltimos, ovozli xabar yuboring!")
        return VOICE_VOCAB_SPRECHEN

    loading = await update.message.reply_text("🧠 *Tahlil qilinmoqda...*", parse_mode="MarkdownV2")
    user_text = await listen_to_voice(update)
    await loading.delete()

    story = context.user_data.get("vocab_sprechen_story", "")
    topic = context.user_data.get("vocab_topic", "Allgemein")

    result = await groq_json([
        {"role": "system", "content": "Nemis tili o'qituvchisi. Nutqni baholash."},
        {"role": "user", "content": (
            f"Asl hikoya: {story}\n"
            f"Foydalanuvchi dedi: {user_text}\n"
            'JSON: {"score": 0-10, "feedback": "tahlil o\'zbek tilida", '
            '"good": "yaxshi jihatlar", "improve": "yaxshilash kerak"}'
        )},
    ])

    user_id = update.effective_user.id
    db = get_db()
    db.add_xp(user_id, XP_REWARDS.get("vocab_sprechen", 30), "vocab_sprechen", topic)

    await update.message.reply_text(
        f"🎤 *Sprechen natijasi*\n\n"
        f"⭐ *Ball: {result.get('score', 5)}/10*\n\n"
        f"✅ *Yaxshi:* {esc_md(result.get('good', ''))}\n\n"
        f"💡 *Yaxshilash:* {esc_md(result.get('improve', ''))}\n\n"
        f"📝 *Tahlil:* {esc_md(result.get('feedback', ''))}\n\n"
        f"🎁 *+{XP_REWARDS.get('vocab_sprechen', 30)} XP*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Qayta urinish", callback_data="vocab_sprechen")],
            [InlineKeyboardButton("🎭 Rolli o'yin", callback_data="vocab_roleplay")],
            [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
        ])
    )
    return VOICE_VOCAB_WORDS


async def vocab_roleplay_from_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lug'at bo'limidan rolli o'yinga o'tish"""
    query = update.callback_query
    await query.answer()

    topic = context.user_data.get("vocab_topic", "")
    level = context.user_data.get("vocab_level", "a1")

    # O'sha mavzuda rolli o'yin boshlash
    if topic:
        context.user_data["rp_level"] = level
        context.user_data["rp_topic"] = topic
        return await _roleplay_start_with_topic(query, context, level, topic)

    return await roleplay_menu(update, context)


# ==================== 6. ROLLI O'YIN (TO'LIQ QAYTA YOZILGAN - TELC/GOETHE USLUBI) ====================

async def roleplay_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yin — daraja tanlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎭 *Rolli O'yin*\n\n"
        "TELC / Goethe / ÖSD imtihoniga tayyorgarlik\\!\n\n"
        "Biz ikkovimiz birgalikda bir narsani rejalashtiramiz \\(gemeinsam etwas planen\\)\\.\n\n"
        "*Darajangizni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=level_select_keyboard("rp_level"),
    )
    return ROLEPLAY_LEVEL


async def roleplay_level_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja tanlandi — mavzu tanlash"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("rp_level_", "")
    context.user_data["rp_level"] = level
    topics = ROLEPLAY_TOPICS.get(level, [])

    await query.edit_message_text(
        f"🎭 *Rolli O'yin — {level.upper()}*\n\n"
        f"*Mavzu tanlang \\({len(topics)} ta mavzu\\):*",
        parse_mode="MarkdownV2",
        reply_markup=topics_keyboard(topics, f"rp_topic_{level}"),
    )
    return ROLEPLAY_TOPIC


async def roleplay_topic_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mavzu tanlandi — qoidalar ko'rsatish"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    level = parts[2]
    topic_idx = int(parts[3])
    topics = ROLEPLAY_TOPICS.get(level, [])

    if topic_idx >= len(topics):
        return ROLEPLAY_TOPIC

    topic = topics[topic_idx]
    context.user_data["rp_topic"] = topic
    context.user_data["rp_level"] = level

    return await _roleplay_show_rules(query, context, level, topic)


async def _roleplay_show_rules(query, context, level: str, topic: str) -> int:
    """Rolli o'yin qoidalarini ko'rsatish"""
    # Mavzuga mos punktlar generatsiya
    punkte = await groq_json([
        {"role": "system", "content": "Nemis tili o'qituvchisi. TELC Sprechen uslubi."},
        {"role": "user", "content": (
            f"'{topic}' mavzusida birgalikda rejalashtirish uchun 5 ta punkt ber. "
            f"Daraja: {level.upper()}. "
            'JSON: {"punkte": ["1. Wo? - ...", "2. Wann? - ...", "3. ...", "4. ...", "5. ..."]}'
        )},
    ])

    punkt_list = punkte.get("punkte", ROLEPLAY_PUNKTE["default"])
    context.user_data["rp_punkte"] = punkt_list

    punkt_text = "\n".join([f"{esc_md(p)}" for p in punkt_list])

    await query.edit_message_text(
        f"🎭 *Rolli O'yin — {esc_md(topic)}*\n\n"
        f"📋 *QOIDALAR:*\n"
        f"Bu o'yin TELC/Goethe imtihonidagi Sprechen qismi uslubida\\.\n"
        f"Biz ikkovimiz birgalikda *{esc_md(topic)}* ni rejalashtiramiz\\.\n\n"
        f"✅ *Vazifangiz:*\n"
        f"• Taklif kiriting\n"
        f"• Savol bering\n"
        f"• Kelishuvga erishing\n\n"
        f"📌 *PUNKTLAR \\(hammasi hal qilinishi shart\\):*\n\n"
        f"{punkt_text}\n\n"
        f"⏱ Vaqt: \\~2 daqiqa\n\n"
        f"Tayyor bo'lsangiz bosing 👇",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Boshlash", callback_data="rp_start_dialog")],
            [InlineKeyboardButton("↩️ Mavzularga qaytish", callback_data=f"rp_level_{context.user_data.get('rp_level', 'a1')}")],
        ])
    )
    return ROLEPLAY_RULES


async def _roleplay_start_with_topic(query, context, level: str, topic: str) -> int:
    """Berilgan mavzu bilan rolli o'yin boshlash (lug'atdan kelganda)"""
    punkte = await groq_json([
        {"role": "system", "content": "Nemis tili o'qituvchisi. TELC Sprechen uslubi."},
        {"role": "user", "content": (
            f"'{topic}' mavzusida birgalikda rejalashtirish uchun 5 ta punkt ber. "
            'JSON: {"punkte": ["1. ...", "2. ...", "3. ...", "4. ...", "5. ..."]}'
        )},
    ])
    context.user_data["rp_punkte"] = punkte.get("punkte", ROLEPLAY_PUNKTE["default"])
    context.user_data["rp_topic"] = topic
    context.user_data["rp_level"] = level

    return await _roleplay_show_rules(query, context, level, topic)


async def roleplay_start_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Dialog boshlash — AI birinchi salom beradi"""
    query = update.callback_query
    await query.answer()

    topic = context.user_data.get("rp_topic", "Geburtstag feiern")
    level = context.user_data.get("rp_level", "a1")
    punkte = context.user_data.get("rp_punkte", ROLEPLAY_PUNKTE["default"])

    punkt_1 = punkte[0] if punkte else "Wo soll es stattfinden?"

    context.user_data["roleplay"] = {
        "topic": topic, "level": level,
        "punkte": punkte, "messages": [],
        "turns": 0, "resolved_punkte": [],
    }

    ai_start = await groq_chat([
        {"role": "system", "content": (
            f"Sen A'ning roli — oddiy nemis tilida gaplashuvchi shaxs. "
            f"Biz '{topic}' ni birgalikda rejalashtiryapmiz. "
            f"Salom berib, birinchi punktdan boshlang: {punkt_1}. "
            f"Qisqa, natural, {level.upper()} darajasiga mos. 2-3 gap."
        )},
        {"role": "user", "content": "Start"},
    ], max_tokens=256)

    context.user_data["roleplay"]["messages"] = [
        {"role": "assistant", "content": ai_start}
    ]

    await query.edit_message_text(
        f"🎭 *{esc_md(topic)}*\n\n"
        f"🤖 *AI:* {esc_md(ai_start)}\n\n"
        f"*Javobingizni yozing yoki 🎙️ ovoz yuboring\\!*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="rp_finish")],
        ])
    )

    # AI gapini ovozda ham yuborish
    await speak_text(query, ai_start, voice="female", speed=1.0)

    return ROLEPLAY_CHAT


async def roleplay_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yin suhbati"""
    rp_data = context.user_data.get("roleplay", {})
    turns = rp_data.get("turns", 0)

    if update.callback_query and update.callback_query.data == "rp_finish":
        return await roleplay_result(update, context)

    # Ovozli yoki matnli
    if update.message and (update.message.voice or update.message.audio):
        loading = await update.message.reply_text("🎙️ *Ovoz tahlil qilinmoqda...*", parse_mode="MarkdownV2")
        user_msg = await listen_to_voice(update)
        await loading.delete()
    elif update.message and update.message.text:
        user_msg = update.message.text.strip()
    else:
        return ROLEPLAY_CHAT

    rp_data["messages"].append({"role": "user", "content": user_msg})
    turns += 1
    rp_data["turns"] = turns

    if turns >= 7:
        return await roleplay_result(update, context)

    topic = rp_data.get("topic", "")
    level = rp_data.get("level", "a1")
    punkte = rp_data.get("punkte", [])
    resolved = rp_data.get("resolved_punkte", [])
    remaining = [p for i, p in enumerate(punkte) if i not in resolved]

    system_msg = {
        "role": "system",
        "content": (
            f"Sen A'ning roli. '{topic}' rejalashtiryapmiz. {level.upper()} darajasi. "
            f"Qolgan punktlar: {remaining}. "
            f"Keyingi punktni taklif qil yoki kelish. Qisqa natural 2-3 gap."
        )
    }

    ai_response = await groq_chat(
        [system_msg] + rp_data["messages"][-6:],
        max_tokens=256
    )
    rp_data["messages"].append({"role": "assistant", "content": ai_response})

    await update.message.reply_text(
        f"🤖 *AI:* {esc_md(ai_response)}\n\n"
        f"*\\({turns}/7\\)* \\-\\> Javobingizni yozing:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ Tugatish", callback_data="rp_finish")],
        ])
    )

    await speak_text(update, ai_response, voice="female", speed=1.0)
    return ROLEPLAY_CHAT


async def roleplay_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Rolli o'yin yakuniy natijasi + so'zlar ro'yxati"""
    rp_data = context.user_data.get("roleplay", {})
    messages = rp_data.get("messages", [])
    topic = rp_data.get("topic", "")
    turns = rp_data.get("turns", 0)

    await (update.callback_query.edit_message_text if update.callback_query
           else update.message.reply_text)(
        "🧠 *AI tahlil qilmoqda\\.\\.\\.*", parse_mode="MarkdownV2"
    )

    analysis = await groq_json([
        {"role": "system", "content": "Nemis tili o'qituvchisi. Suhbatni batafsil tahlil qil."},
        {"role": "user", "content": (
            f"Mavzu: {topic}\nSuhbat: {messages}\n\n"
            'JSON: {"score": 0-10, "fluency": 0-10, '
            '"good_points": ["...", "..."], "improve": ["...", "..."], '
            '"aktiv_sozlar": ["so\'z1", "so\'z2", "so\'z3", "so\'z4", "so\'z5"], '
            '"passiv_sozlar": ["so\'z1", "so\'z2", "so\'z3"], '
            '"asosiy_birikmalar": ["birizma1", "birizma2", "birizma3"]}'
        )},
    ])

    user_id = (update.callback_query.from_user.id if update.callback_query else update.effective_user.id)
    db = get_db()
    score = analysis.get("score", 5)
    db.add_xp(user_id, XP_REWARDS.get("roleplay_complete", 40), "roleplay", topic)

    good_points = "\n".join([f"✅ {esc_md(p)}" for p in analysis.get("good_points", [])])
    improve = "\n".join([f"⚠️ {esc_md(i)}" for i in analysis.get("improve", [])])
    aktiv = ", ".join([esc_md(w) for w in analysis.get("aktiv_sozlar", [])])
    passiv = ", ".join([esc_md(w) for w in analysis.get("passiv_sozlar", [])])
    birikmalar = "\n".join([f"• {esc_md(b)}" for b in analysis.get("asosiy_birikmalar", [])])

    text = (
        f"🏁 *Rolli o'yin tugadi\\! — {esc_md(topic)}*\n\n"
        f"⭐ *Ball: {score}/10*\n"
        f"💬 *Suvliklik: {analysis.get('fluency', 5)}/10*\n\n"
        f"{good_points}\n\n"
        f"{improve}\n\n"
        f"📚 *AKTIV SO'ZLAR \\(ishlating\\):*\n{aktiv}\n\n"
        f"📖 *PASSIV SO'ZLAR \\(biling\\):*\n{passiv}\n\n"
        f"🔑 *ASOSIY BIRIKMALAR:*\n{birikmalar}\n\n"
        f"⚠️ *ESLATMA: Ertaga tekshiraman\\!*\n"
        f"Bu so'zlarni yodlang \\— ertaga tekshiruv bo'ladi 🎯\n\n"
        f"🎁 *\\+{XP_REWARDS.get('roleplay_complete', 40)} XP*"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Qayta o'ynash", callback_data=f"rp_level_{rp_data.get('level', 'a1')}")],
        [InlineKeyboardButton("🏠 AI Mentor", callback_data="ai_mentor_menu")],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)

    return AI_MENTOR_MENU


# ==================== AI MENTOR MENU HANDLER ====================

async def ai_mentor_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI Mentor asosiy menyusi"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🤖 *AI Mentor*\n\n"
        "*Imkoniyatlar:*\n\n"
        "🎯 *Darajani aniqlash* \\- 5 ta savol bilan darajangizni bilib oling\n"
        "🎤 *Vorstellen* \\- O'zingizni taqdim etish mashqi \\(3 tugma tahlil\\)\n"
        "💬 *Erfahrungen* \\- B2/C1 mavzularida suhbatlashish\n"
        "🔧 *Xato banki* \\- Xatolaringizni saqlash va mini\\-darslar\n"
        "📚 *Ovozli lug'at* \\- A1/A2/B1/B2, 20 mavzu, 25 so'z\n"
        "🎭 *Rolli o'yinlar* \\- TELC/Goethe uslubi, 20 mavzu\n\n"
        "*Bo'limni tanlang:*",
        parse_mode="MarkdownV2",
        reply_markup=ai_mentor_menu_keyboard(),
    )
    return AI_MENTOR_MENU


# ==================== main.py UCHUN ALIAS'LAR ====================
# main__8_.py eski nomlarni import qiladi — shu alias'lar mos qiladi

vorstellen_start    = vorstellen_start_new
vorstellen_process  = vorstellen_process_new
vs_show_section     = vs_show_section_new
vs_speak_handler    = vs_speak_new

# main.py VORSTELLEN_START (200) va VORSTELLEN_FOLLOWUP (201) kutadi
# Lekin ai_mentor_work da Vorstellen state'lari range(100,139) ichida
# VORSTELLEN_MENU=107, VORSTELLEN_Q1=109... shu state'larga yo'naltirish
VORSTELLEN_START    = VORSTELLEN_MENU      # 107 — birinchi savol state
VORSTELLEN_FOLLOWUP = VORSTELLEN_Q1       # 109 — jarayon davomida
