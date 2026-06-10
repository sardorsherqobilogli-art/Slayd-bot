"""
AI Mentor moduli - Groq API (bepul)
"""
import os
import io
import logging
import tempfile
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# ============ CONVERSATION STATE RAQAMLARI ============
MENU = 0
LEVEL_DETECT = 10
LEVEL_RESPONSE = 11
VORSTELLEN = 20
VORSTELLEN_RESPONSE = 21
VOICE_VOCAB_LEVEL = 30
VOICE_VOCAB_TOPIC = 31
VOICE_VOCAB_LEARN = 32
VOICE_VOCAB_TEST = 33
VOICE_VOCAB_SPRECHEN = 34
VOICE_VOCAB_ROLEPLAY = 35
ROLEPLAY_MENU = 40
ROLEPLAY_TOPIC = 41
ROLEPLAY_CONVERSATION = 42
MISTAKE_BANK = 50
MISTAKE_RETEST = 51
AKTIV_PASSIV_LEVEL = 60
AKTIV_PASSIV_TOPIC = 61
AKTIV_PASSIV_LEARN = 62

# ============ GROQ CLIENT ============
_groq_client = None

def set_api_key(key: str):
    """Groq API kalitini o'rnatish"""
    global _groq_client
    from groq import Groq
    _groq_client = Groq(api_key=key)
    logger.info("Groq client tayyor")


async def _ask_ai(system: str, user: str, max_tokens: int = 600) -> str:
    """Groq LLM ga so'rov yuborish"""
    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq AI xatolik: {e}")
        return "❌ AI javob bermadi. Qaytadan urinib ko'ring."


# ============ YORDAMCHI FUNKSIYALAR ============
async def _send_voice(update: Update, text: str, gender: str = "female"):
    """Matnni ovozga o'girib yuborish"""
    try:
        from voice_engine import speak_text
        audio_bytes = await speak_text(text, gender)
        if audio_bytes:
            await update.effective_message.reply_voice(
                voice=io.BytesIO(audio_bytes),
                caption=f"🔊 {text[:100]}..."
            )
        else:
            await update.effective_message.reply_text(f"🔊 (Ovoz xatoligi)\n\n{text}")
    except Exception as e:
        logger.error(f"Voice yuborish xatoligi: {e}")
        await update.effective_message.reply_text(text)


async def _transcribe_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Foydalanuvchi ovozini matnga o'girish"""
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        from voice_engine import listen_to_voice
        text = await listen_to_voice(tmp_path)
        os.unlink(tmp_path)
        return text
    except Exception as e:
        logger.error(f"Transcribe xatoligi: {e}")
        return ""


# ============ MENYU ============
def _main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Darajani aniqlash", callback_data="level_detect")],
        [InlineKeyboardButton("🎤 Vorstellen", callback_data="vorstellen")],
        [InlineKeyboardButton("📚 Ovozli lug'at", callback_data="voice_vocab")],
        [InlineKeyboardButton("🎭 Rolli o'yin", callback_data="roleplay")],
        [InlineKeyboardButton("📋 Xato banki", callback_data="mistake_bank")],
        [InlineKeyboardButton("📖 Aktiv/Passiv (B1/B2)", callback_data="aktiv_passiv")],
    ])


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏠 *Asosiy menyu*\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    msg = update.effective_message
    await msg.reply_text(text, reply_markup=_main_keyboard(), parse_mode="Markdown")


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu":
        await query.edit_message_text(
            "🏠 *Asosiy menyu*\n\nQuyidagi bo'limlardan birini tanlang:",
            reply_markup=_main_keyboard(),
            parse_mode="Markdown"
        )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("❌ Bekor qilindi.", reply_markup=_main_keyboard())
    return ConversationHandler.END


# ============ DARAJA ANIQLASH ============
async def start_level_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎯 *Darajani aniqlash*\n\n"
        "Nemis tilida bir necha jumla yozing yoki gapirib yuboring.\n"
        "Men sizning darajangizni aniqlayman (A1-B2).\n\n"
        "📝 Masalan: *Ich heiße Sardor und ich lerne Deutsch.*",
        parse_mode="Markdown"
    )
    return LEVEL_DETECT


async def process_level_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        user_text = await _transcribe_voice(update, context)
        if not user_text:
            await update.message.reply_text("❌ Ovozni tanib bo'lmadi. Yozing yoki qayta urinib ko'ring.")
            return LEVEL_DETECT
    else:
        user_text = update.message.text

    system = (
        "Sen nemis tili ekspertisan. Foydalanuvchi yozgan/gapirgan nemis matni asosida "
        "uning darajasini aniqla (A1, A2, B1, B2). "
        "Qisqa tahlil va tavsiyalar ber. Uzbek tilida javob ber."
    )
    result = await _ask_ai(system, f"Daraja aniqla: {user_text}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Qayta urinish", callback_data="level_detect")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    await update.message.reply_text(
        f"📊 *Tahlil natijasi:*\n\n{result}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def level_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return ConversationHandler.END


# ============ VORSTELLEN ============
async def start_vorstellen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 A1 - Boshlang'ich", callback_data="vorst_a1")],
        [InlineKeyboardButton("🟡 A2 - Asosiy", callback_data="vorst_a2")],
        [InlineKeyboardButton("🟠 B1 - O'rta", callback_data="vorst_b1")],
        [InlineKeyboardButton("🔴 B2 - Yuqori", callback_data="vorst_b2")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    await query.edit_message_text(
        "🎤 *Vorstellen - O'zingizni tanishtirish*\n\nDarajangizni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return VORSTELLEN


async def process_vorstellen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data.get("vorst_level", "A2")

    if update.message.voice:
        user_text = await _transcribe_voice(update, context)
        if not user_text:
            await update.message.reply_text("❌ Ovozni tanib bo'lmadi.")
            return VORSTELLEN
    else:
        user_text = update.message.text

    system = (
        f"Sen nemis tili {level} darajasi bo'yicha murabbiysan. "
        "Foydalanuvchi o'zini tanishtirdi. Xatolarini ko'rsat, to'g'ri versiyasini ber, "
        "va qanday yaxshilash kerakligini ayt. Uzbek tilida javob ber."
    )
    result = await _ask_ai(system, user_text)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Qayta mashq", callback_data="vorstellen")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    await update.message.reply_text(
        f"📝 *Natija ({level}):*\n\n{result}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def vorstellen_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level_map = {"vorst_a1": "A1", "vorst_a2": "A2", "vorst_b1": "B1", "vorst_b2": "B2"}
    level = level_map.get(query.data, "A2")
    context.user_data["vorst_level"] = level

    templates = {
        "A1": "Ich heiße [Ism]. Ich bin [Yosh] Jahre alt. Ich komme aus [Mamlakat].",
        "A2": "Guten Tag! Mein Name ist [Ism]. Ich bin [Yosh] Jahre alt. Ich komme aus [Mamlakat] und wohne in [Shahar]. Ich lerne Deutsch, weil [Sabab].",
        "B1": "Hallo, ich heiße [Ism]. Ich bin [Yosh] Jahre alt und komme ursprünglich aus [Mamlakat]. Ich lerne seit [Muddat] Deutsch, weil ich [Sabab]. In meiner Freizeit [Hobbylar].",
        "B2": "Guten Tag! Mein Name ist [Ism]. Ich bin [Yosh] Jahre alt und stamme aus [Mamlakat], lebe jedoch seit [Muddat] in Deutschland. Mein Ziel ist es, [Maqsad] zu erreichen.",
    }

    await query.edit_message_text(
        f"🎤 *Vorstellen - {level} darajasi*\n\n"
        f"Quyidagi shablondan foydalaning:\n\n"
        f"```\n{templates[level]}\n```\n\n"
        f"Endi o'z ma'lumotlaringiz bilan yozing yoki gapirib yuboring:",
        parse_mode="Markdown"
    )
    return VORSTELLEN


# ============ OVOZLI LUG'AT ============
VOCAB_TOPICS = {
    "a1": ["Salom va xayrlashuv", "Raqamlar", "Ranglar", "Oila", "Oziq-ovqat"],
    "a2": ["Uy va mebel", "Ish va kasb", "Transport", "Do'kon va narxlar", "Sog'liq"],
    "b1": ["Muhit va tabiat", "Sayohat", "Ommaviy axborot", "Madaniyat", "Ta'lim"],
    "b2": ["Siyosat", "Iqtisodiyot", "Texnologiya", "Falsafa", "Ilm-fan"],
}

async def start_voice_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 A1", callback_data="vocab_level_a1"),
         InlineKeyboardButton("🟡 A2", callback_data="vocab_level_a2")],
        [InlineKeyboardButton("🟠 B1", callback_data="vocab_level_b1"),
         InlineKeyboardButton("🔴 B2", callback_data="vocab_level_b2")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])
    await query.edit_message_text(
        "📚 *Ovozli lug'at*\n\nDarajangizni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return VOICE_VOCAB_LEVEL


async def voice_vocab_level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = query.data.replace("vocab_level_", "")
    context.user_data["vocab_level"] = level
    topics = VOCAB_TOPICS.get(level, [])
    buttons = [[InlineKeyboardButton(f"📖 {t}", callback_data=f"vocab_topic_{i}")] for i, t in enumerate(topics)]
    buttons.append([InlineKeyboardButton("🏠 Menyu", callback_data="menu")])
    await query.edit_message_text(
        f"📚 *{level.upper()} - Mavzu tanlang:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return VOICE_VOCAB_TOPIC


async def voice_vocab_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("vocab_topic_", ""))
    level = context.user_data.get("vocab_level", "a1")
    topic = VOCAB_TOPICS[level][idx]
    context.user_data["vocab_topic"] = topic

    system = (
        f"Sen nemis tili o'qituvchisan. {level.upper()} darajasi uchun "
        f"'{topic}' mavzusidan 10 ta muhim so'z ber. "
        f"Format: so'z - tarjima (uzbekcha). Har birini yangi qatorda yoz."
    )
    words = await _ask_ai(system, f"{topic} mavzusidan so'zlar", max_tokens=400)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 So'zlarni tinglash", callback_data="vocab_all_words")],
        [InlineKeyboardButton("📝 Test", callback_data="vocab_test")],
        [InlineKeyboardButton("🔙 Mavzular", callback_data=f"vocab_level_{level}")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    await query.edit_message_text(
        f"📖 *{topic} - {level.upper()}*\n\n{words}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return VOICE_VOCAB_LEARN


async def voice_vocab_all_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = context.user_data.get("vocab_topic", "")
    level = context.user_data.get("vocab_level", "a1")

    await query.message.reply_text("🔊 So'zlar ovozi tayyorlanmoqda...")

    system = f"Faqat nemischa so'zlar ro'yxatini ber. {level.upper()} uchun '{topic}' mavzusidan 5 ta eng muhim so'z. Faqat nemischa so'zlarni, vergul bilan ajratib yoz."
    words_str = await _ask_ai(system, topic, max_tokens=100)

    for word in words_str.split(",")[:5]:
        word = word.strip()
        if word:
            audio = await (lambda: __import__('voice_engine').speak_text(word))()
            if audio:
                await query.message.reply_voice(
                    voice=io.BytesIO(audio),
                    caption=f"🔊 *{word}*",
                    parse_mode="Markdown"
                )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Test", callback_data="vocab_test")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])
    await query.message.reply_text("✅ Tinglash tugadi!", reply_markup=keyboard)
    return VOICE_VOCAB_LEARN


async def voice_vocab_words_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await voice_vocab_all_words(update, context)


async def voice_vocab_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = context.user_data.get("vocab_topic", "")
    level = context.user_data.get("vocab_level", "a1")

    system = (
        f"{level.upper()} darajasi '{topic}' mavzusidan bitta test savol ber. "
        "Format: Savol yozing. 4 ta variant A, B, C, D. To'g'ri javobni so'ngida ayt."
    )
    question = await _ask_ai(system, "Test savoli", max_tokens=200)
    context.user_data["current_test"] = question

    await query.edit_message_text(
        f"📝 *Test:*\n\n{question}\n\nJavobingizni yozing (A/B/C/D):",
        parse_mode="Markdown"
    )
    return VOICE_VOCAB_TEST


async def voice_vocab_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    question = context.user_data.get("current_test", "")

    system = "Foydalanuvchi test savoliga javob berdi. To'g'ri yoki noto'g'riligini ayt va izohla. Uzbek tilida."
    result = await _ask_ai(system, f"Savol: {question}\nJavob: {answer}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yana test", callback_data="vocab_test")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    await update.message.reply_text(
        f"✅ *Natija:*\n\n{result}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def voice_vocab_sprechen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = context.user_data.get("vocab_topic", "")
    await query.edit_message_text(
        f"🎤 *Sprechen mashqi - {topic}*\n\n"
        "Mavzu haqida nemischa gapiring va ovoz yuboring:",
    )
    return VOICE_VOCAB_SPRECHEN


async def voice_vocab_sprechen_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menyu", callback_data="menu")]])
    await query.edit_message_text("✅ Mashq tugadi!", reply_markup=keyboard)
    return ConversationHandler.END


async def start_roleplay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 A2", callback_data="rp_level_a2"),
         InlineKeyboardButton("🟠 B1", callback_data="rp_level_b1")],
        [InlineKeyboardButton("🔴 B2", callback_data="rp_level_b2")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])
    await query.edit_message_text(
        "🎭 *Rolli o'yin*\n\nDarajangizni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ROLEPLAY_MENU


ROLEPLAY_TOPICS = {
    "a2": ["Do'konda xarid", "Shifokorga borish", "Yo'l so'rash", "Restoranda buyurtma"],
    "b1": ["Ish suhbati", "Kvartira ijarasi", "Bank xizmati", "Mehmonxona bronlash"],
    "b2": ["Konferentsiyada taqdimot", "Muzokaralar", "Shikoyat", "Sug'urta"],
}


async def roleplay_level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = query.data.replace("rp_level_", "")
    context.user_data["rp_level"] = level
    topics = ROLEPLAY_TOPICS.get(level, [])
    buttons = [[InlineKeyboardButton(t, callback_data=f"rp_topic_{i}")] for i, t in enumerate(topics)]
    buttons.append([InlineKeyboardButton("🏠 Menyu", callback_data="menu")])
    await query.edit_message_text(
        f"🎭 *{level.upper()} - Vaziyat tanlang:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return ROLEPLAY_TOPIC


async def roleplay_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("rp_topic_", ""))
    level = context.user_data.get("rp_level", "a2")
    topic = ROLEPLAY_TOPICS[level][idx]
    context.user_data["rp_topic"] = topic
    context.user_data["rp_history"] = []

    system = (
        f"Sen nemis tili {level.upper()} suhbat partnéryisan. "
        f"Vaziyat: {topic}. Suhbatni boshlang. Faqat nemischa gapiring."
    )
    opening = await _ask_ai(system, "Suhbatni boshlang", max_tokens=150)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Tugatish", callback_data="rp_end")],
    ])
    await query.edit_message_text(
        f"🎭 *{topic}*\n\n🤖 _{opening}_\n\nJavob bering:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    context.user_data["rp_history"].append({"role": "assistant", "content": opening})
    return ROLEPLAY_CONVERSATION


async def roleplay_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        user_text = await _transcribe_voice(update, context)
        if not user_text:
            await update.message.reply_text("❌ Ovozni tanib bo'lmadi.")
            return ROLEPLAY_CONVERSATION
    else:
        user_text = update.message.text

    level = context.user_data.get("rp_level", "a2")
    topic = context.user_data.get("rp_topic", "")
    history = context.user_data.get("rp_history", [])
    history.append({"role": "user", "content": user_text})

    messages = [
        {"role": "system", "content": f"Sen {level.upper()} nemis tili suhbat partnéryisan. Vaziyat: {topic}. Faqat nemischa gapir."}
    ] + history[-6:]

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=200,
        )
        ai_reply = response.choices[0].message.content.strip()
    except Exception as e:
        ai_reply = "Entschuldigung, ich verstehe nicht."

    history.append({"role": "assistant", "content": ai_reply})
    context.user_data["rp_history"] = history

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Tugatish", callback_data="rp_end")],
    ])
    await update.message.reply_text(
        f"🤖 _{ai_reply}_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ROLEPLAY_CONVERSATION


async def roleplay_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    history = context.user_data.get("rp_history", [])
    user_lines = [m["content"] for m in history if m["role"] == "user"]

    system = "Sen nemis tili murabbiysan. Suhbatni tahlil qil va xatolarni ko'rsat. Uzbek tilida."
    analysis = await _ask_ai(system, f"Foydalanuvchi gaplari: {'. '.join(user_lines)}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Qayta o'ynash", callback_data="roleplay")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])
    await query.edit_message_text(
        f"📊 *Suhbat tahlili:*\n\n{analysis}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def roleplay_memorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await roleplay_end(update, context)


# ============ XATO BANKI ============
async def start_mistake_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    import database
    mistakes = database.get_user_mistakes(update.effective_user.id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Barcha xatolar", callback_data="mb_list_all")],
        [InlineKeyboardButton("🔄 Qayta test", callback_data="mb_start_retest")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    await query.edit_message_text(
        f"📋 *Xato banki*\n\nJami xatolar: {len(mistakes)} ta",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return MISTAKE_BANK


async def mistake_list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    import database
    mistakes = database.get_user_mistakes(update.effective_user.id)

    if not mistakes:
        await query.edit_message_text(
            "✅ Xato bank bo'sh! Siz hali xato qilmadingiz.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menyu", callback_data="menu")]])
        )
        return ConversationHandler.END

    text = "📋 *Xatolaringiz:*\n\n"
    for i, m in enumerate(mistakes[:10], 1):
        text += f"{i}. {m.get('wrong', '')} → {m.get('correct', '')}\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Qayta test", callback_data="mb_start_retest")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    return MISTAKE_BANK


async def mistake_retest_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    import database
    mistakes = database.get_user_mistakes(update.effective_user.id)

    if not mistakes:
        await query.edit_message_text(
            "✅ Qayta test uchun xato yo'q!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menyu", callback_data="menu")]])
        )
        return ConversationHandler.END

    import random
    mistake = random.choice(mistakes)
    context.user_data["current_mistake"] = mistake

    await query.edit_message_text(
        f"🔄 *Qayta test*\n\n"
        f"❌ Xato: *{mistake.get('wrong', '')}*\n\n"
        f"To'g'risini yozing:",
        parse_mode="Markdown"
    )
    return MISTAKE_RETEST


async def check_mistake_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        answer = await _transcribe_voice(update, context)
    else:
        answer = update.message.text

    mistake = context.user_data.get("current_mistake", {})
    correct = mistake.get("correct", "")

    is_correct = answer.strip().lower() == correct.strip().lower()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Keyingisi", callback_data="mb_start_retest")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])

    if is_correct:
        await update.message.reply_text(
            f"✅ *To'g'ri!* `{correct}`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ *Noto'g'ri*\nSiz: `{answer}`\nTo'g'risi: `{correct}`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    return ConversationHandler.END


async def mistake_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await mistake_retest_start(update, context)


# ============ AKTIV/PASSIV LUG'AT ============
AKTIV_PASSIV_DATA = {
    "b1": ["Arbeit (ish)", "Reise (sayohat)", "Familie (oila)", "Gesundheit (sog'liq)"],
    "b2": ["Politik (siyosat)", "Wirtschaft (iqtisodiyot)", "Umwelt (atrof-muhit)", "Technologie (texnologiya)"],
}

async def start_aktiv_passiv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟠 B1", callback_data="ap_level_b1"),
         InlineKeyboardButton("🔴 B2", callback_data="ap_level_b2")],
        [InlineKeyboardButton("🏠 Menyu", callback_data="menu")],
    ])
    await query.edit_message_text(
        "📖 *Aktiv/Passiv lug'at*\n\nDarajangizni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return AKTIV_PASSIV_LEVEL


async def aktiv_passiv_level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    level = query.data.replace("ap_level_", "")
    context.user_data["ap_level"] = level
    topics = AKTIV_PASSIV_DATA.get(level, [])
    buttons = [[InlineKeyboardButton(t, callback_data=f"ap_topic_{i}")] for i, t in enumerate(topics)]
    buttons.append([InlineKeyboardButton("🏠 Menyu", callback_data="menu")])
    await query.edit_message_text(
        f"📖 *{level.upper()} - Mavzu tanlang:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return AKTIV_PASSIV_TOPIC


async def aktiv_passiv_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("ap_topic_", ""))
    level = context.user_data.get("ap_level", "b1")
    topic = AKTIV_PASSIV_DATA[level][idx]
    context.user_data["ap_topic"] = topic

    system = (
        f"Sen nemis tili {level.upper()} darajasi uchun lug'at o'qituvchisan. "
        f"'{topic}' mavzusidan 5 ta AKTIV so'z va 5 ta PASSIV so'z ber. "
        "Aktiv = tez-tez ishlatiladi, Passiv = kamdan-kam. Uzbek tarjimasi bilan."
    )
    words = await _ask_ai(system, topic, max_tokens=400)

    buttons = [[InlineKeyboardButton(f"🔊 So'z {i+1}", callback_data=f"ap_listen_{i}")] for i in range(5)]
    buttons.append([InlineKeyboardButton("🏠 Menyu", callback_data="menu")])

    await query.edit_message_text(
        f"📖 *{topic} - {level.upper()}*\n\n{words}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return AKTIV_PASSIV_LEARN


async def aktiv_passiv_listen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = context.user_data.get("ap_topic", "")

    system = f"'{topic}' mavzusidan bitta muhim nemis so'zini yoz. Faqat nemischa so'z."
    word = await _ask_ai(system, topic, max_tokens=20)
    word = word.strip().split("\n")[0]

    from voice_engine import speak_text
    audio = await speak_text(word)
    if audio:
        await query.message.reply_voice(
            voice=io.BytesIO(audio),
            caption=f"🔊 *{word}*",
            parse_mode="Markdown"
        )
    else:
        await query.message.reply_text(f"🔊 {word}")

    return AKTIV_PASSIV_LEARN
