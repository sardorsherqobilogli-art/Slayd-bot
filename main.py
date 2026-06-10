"""
AI German Mentor - Telegram Bot
Barcha handler va conversation larni boshqaruvchi asosiy fayl
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

import database
import ai_mentor
from config import TELEGRAM_BOT_TOKEN, GROQ_API_KEY

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation holatlari - ai_mentor dan import
from ai_mentor import (
    LEVEL_DETECT, LEVEL_RESPONSE,
    VORSTELLEN, VORSTELLEN_RESPONSE,
    VOICE_VOCAB_LEVEL, VOICE_VOCAB_TOPIC, VOICE_VOCAB_LEARN,
    VOICE_VOCAB_TEST, VOICE_VOCAB_SPRECHEN, VOICE_VOCAB_ROLEPLAY,
    ROLEPLAY_MENU, ROLEPLAY_TOPIC, ROLEPLAY_CONVERSATION,
    MISTAKE_BANK, MISTAKE_RETEST,
    AKTIV_PASSIV_LEVEL, AKTIV_PASSIV_TOPIC, AKTIV_PASSIV_LEARN,
    MENU
)


def main():
    """Botni ishga tushirish"""
    print("🚀 AI German Mentor bot ishga tushmoqda...")

    # Ma'lumotlar bazasini yaratish
    database.init_db()

    # API kalitlarini sozlash
    ai_mentor.set_api_key(GROQ_API_KEY)

    # Application yaratish
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ============================================================
    # CONVERSATION HANDLER: Darajani aniqlash
    # ============================================================
    level_detect_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor.start_level_detection, pattern="^level_detect$")
        ],
        states={
            LEVEL_DETECT: [
                MessageHandler(filters.TEXT | filters.VOICE, ai_mentor.process_level_input),
            ],
            LEVEL_RESPONSE: [
                CallbackQueryHandler(ai_mentor.level_response_handler, pattern="^level_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor.menu_handler, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("cancel", ai_mentor.cancel),
        ],
        allow_reentry=True,
    )

    # ============================================================
    # CONVERSATION HANDLER: Vorstellen
    # ============================================================
    vorstellen_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor.start_vorstellen, pattern="^vorstellen$")
        ],
        states={
            VORSTELLEN: [
                MessageHandler(filters.TEXT | filters.VOICE, ai_mentor.process_vorstellen),
            ],
            VORSTELLEN_RESPONSE: [
                CallbackQueryHandler(ai_mentor.vorstellen_response_handler, pattern="^vorst_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor.menu_handler, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("cancel", ai_mentor.cancel),
        ],
        allow_reentry=True,
    )

    # ============================================================
    # CONVERSATION HANDLER: Ovozli lug'at
    # ============================================================
    voice_vocab_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor.start_voice_vocab, pattern="^voice_vocab$")
        ],
        states={
            VOICE_VOCAB_LEVEL: [
                CallbackQueryHandler(ai_mentor.voice_vocab_level_handler, pattern="^vocab_level_"),
            ],
            VOICE_VOCAB_TOPIC: [
                CallbackQueryHandler(ai_mentor.voice_vocab_topic_handler, pattern="^vocab_topic_"),
            ],
            VOICE_VOCAB_LEARN: [
                CallbackQueryHandler(ai_mentor.voice_vocab_all_words, pattern="^vocab_all_words$"),
                CallbackQueryHandler(ai_mentor.voice_vocab_words_page, pattern="^vocab_words_"),
                CallbackQueryHandler(ai_mentor.voice_vocab_test, pattern="^vocab_test$"),
                CallbackQueryHandler(ai_mentor.voice_vocab_sprechen, pattern="^vocab_sprechen$"),
                CallbackQueryHandler(ai_mentor.voice_vocab_sprechen_done, pattern="^sprechen_done$"),
                CallbackQueryHandler(ai_mentor.start_roleplay, pattern="^vocab_roleplay$"),
                CallbackQueryHandler(ai_mentor.voice_vocab_topic_handler, pattern="^vocab_topic_"),
                CallbackQueryHandler(ai_mentor.voice_vocab_level_handler, pattern="^vocab_level_"),
                MessageHandler(filters.TEXT | filters.VOICE, ai_mentor.process_level_input),
            ],
            VOICE_VOCAB_TEST: [
                MessageHandler(filters.TEXT | filters.VOICE, ai_mentor.voice_vocab_test_answer),
            ],
            VOICE_VOCAB_SPRECHEN: [
                CallbackQueryHandler(ai_mentor.voice_vocab_sprechen_done, pattern="^sprechen_done$"),
                CallbackQueryHandler(ai_mentor.voice_vocab_sprechen, pattern="^sprechen_listen_again$"),
                CallbackQueryHandler(ai_mentor.voice_vocab_level_handler, pattern="^vocab_level_"),
            ],
            VOICE_VOCAB_ROLEPLAY: [
                # Rolli o'yin alohida handler da
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor.menu_handler, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("cancel", ai_mentor.cancel),
        ],
        allow_reentry=True,
    )

    # ============================================================
    # CONVERSATION HANDLER: Rolli o'yin
    # ============================================================
    roleplay_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor.start_roleplay, pattern="^roleplay$")
        ],
        states={
            ROLEPLAY_MENU: [
                CallbackQueryHandler(ai_mentor.roleplay_level_handler, pattern="^rp_level_"),
            ],
            ROLEPLAY_TOPIC: [
                CallbackQueryHandler(ai_mentor.roleplay_topic_handler, pattern="^rp_topic_"),
            ],
            ROLEPLAY_CONVERSATION: [
                MessageHandler(filters.TEXT | filters.VOICE, ai_mentor.roleplay_conversation),
                CallbackQueryHandler(ai_mentor.roleplay_end, pattern="^rp_end$"),
                CallbackQueryHandler(ai_mentor.roleplay_memorized, pattern="^rp_memorized_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor.menu_handler, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("cancel", ai_mentor.cancel),
        ],
        allow_reentry=True,
    )

    # ============================================================
    # CONVERSATION HANDLER: Xato banki
    # ============================================================
    mistake_bank_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor.start_mistake_bank, pattern="^mistake_bank$")
        ],
        states={
            MISTAKE_BANK: [
                CallbackQueryHandler(ai_mentor.mistake_retest_start, pattern="^mb_start_retest$"),
                CallbackQueryHandler(ai_mentor.mistake_list_all, pattern="^mb_list_all$"),
            ],
            MISTAKE_RETEST: [
                MessageHandler(filters.TEXT | filters.VOICE, ai_mentor.check_mistake_answer),
                CallbackQueryHandler(ai_mentor.mistake_skip, pattern="^mb_skip$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor.menu_handler, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("cancel", ai_mentor.cancel),
        ],
        allow_reentry=True,
    )

    # ============================================================
    # CONVERSATION HANDLER: Aktiv/Passiv lug'at
    # ============================================================
    aktiv_passiv_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ai_mentor.start_aktiv_passiv, pattern="^aktiv_passiv$")
        ],
        states={
            AKTIV_PASSIV_LEVEL: [
                CallbackQueryHandler(ai_mentor.aktiv_passiv_level_handler, pattern="^ap_level_"),
            ],
            AKTIV_PASSIV_TOPIC: [
                CallbackQueryHandler(ai_mentor.aktiv_passiv_topic_handler, pattern="^ap_topic_"),
            ],
            AKTIV_PASSIV_LEARN: [
                CallbackQueryHandler(ai_mentor.aktiv_passiv_listen, pattern="^ap_listen_"),
                CallbackQueryHandler(ai_mentor.aktiv_passiv_level_handler, pattern="^ap_level_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(ai_mentor.menu_handler, pattern="^menu$"),
            CommandHandler("start", start),
            CommandHandler("cancel", ai_mentor.cancel),
        ],
        allow_reentry=True,
    )

    # ============================================================
    # HANDLER LARNI QO'SHISH
    # ============================================================
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_menu_command))
    application.add_handler(CommandHandler("cancel", ai_mentor.cancel))

    # Conversation handlerlarni qo'shish
    application.add_handler(level_detect_conv)
    application.add_handler(vorstellen_conv)
    application.add_handler(voice_vocab_conv)
    application.add_handler(roleplay_conv)
    application.add_handler(mistake_bank_conv)
    application.add_handler(aktiv_passiv_conv)

    # Umumiy callback handler (eng oxirida)
    application.add_handler(CallbackQueryHandler(ai_mentor.menu_handler))

    print("✅ Bot tayyor! Polling boshlanmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    user = database.get_or_create_user(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name
    )

    text = (
        f"👋 *Salom, {user['first_name'] or 'dostim'}!*\n\n"
        f"🤖 *AI German Mentor*ga xush kelibsiz!\n\n"
        f"Bu bot sizga nemis tilini o'rganishda yordam beradi:\n"
        f"🇩🇪 Darajani aniqlash\n"
        f"🎤 Vorstellen (O'zingizni taqdim etish)\n"
        f"📚 Ovozli lug'at (80 ta mavzu, 2000 ta so'z)\n"
        f"🎭 Rolli o'yin (TELC/Goethe tayyorgarlik)\n"
        f"📋 Xato banki\n"
        f"📖 Aktiv/Passiv so'zlar (B1/B2)\n\n"
        f"Boshlash uchun quyidagi menyudan tanlang:"
    )

    keyboard = [
        [InlineKeyboardButton("🎯 Darajani aniqlash", callback_data="level_detect")],
        [InlineKeyboardButton("🎤 Vorstellen", callback_data="vorstellen")],
        [InlineKeyboardButton("📚 Ovozli lug'at", callback_data="voice_vocab")],
        [InlineKeyboardButton("🎭 Rolli o'yin", callback_data="roleplay")],
        [InlineKeyboardButton("📋 Xato banki", callback_data="mistake_bank")],
        [InlineKeyboardButton("📖 Aktiv/Passiv (B1/B2)", callback_data="aktiv_passiv")],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/menu komandasi"""
    await ai_mentor.show_menu(update, context)


if __name__ == "__main__":
    main()
