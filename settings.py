#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - Sozlamalar Moduli
Foydalanuvchi sozlamalari: daraja, ovoz, tezlik, xatolar ko'rsatish
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import LEVEL_LABELS
from database import get_db


def esc_md(text: str) -> str:
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def settings_menu_keyboard(user_data: dict):
    """Sozlamalar menyusi"""
    current_level = user_data.get("current_level", "a1")
    voice_pref = user_data.get("voice_preference", "female")
    tts_speed = user_data.get("tts_speed", 1.0)
    show_mistakes = user_data.get("show_mistakes", 1)

    voice_icon = "👩" if voice_pref == "female" else "👨"
    speed_label = f"{tts_speed}x"
    mistakes_label = "✅ Ko'rsatish" if show_mistakes else "❌ Yashirish"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"📊 Daraja: {LEVEL_LABELS.get(current_level, current_level)}",
            callback_data="set_level"
        )],
        [InlineKeyboardButton(
            f"{voice_icon} Ovoz: {voice_pref.capitalize()}",
            callback_data="set_voice"
        )],
        [InlineKeyboardButton(
            f"⏩ TTS Tezlik: {speed_label}",
            callback_data="set_speed"
        )],
        [InlineKeyboardButton(
            f"🔧 Xatolar: {mistakes_label}",
            callback_data="set_mistakes"
        )],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
    ])


def level_select_keyboard():
    """Daraja tanlash"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 A1", callback_data="set_level_a1")],
        [InlineKeyboardButton("🟢 A2", callback_data="set_level_a2")],
        [InlineKeyboardButton("🟡 B1", callback_data="set_level_b1")],
        [InlineKeyboardButton("🟡 B2", callback_data="set_level_b2")],
        [InlineKeyboardButton("🔴 C1", callback_data="set_level_c1")],
        [InlineKeyboardButton("↩️ Sozlamalarga qaytish", callback_data="settings_menu")],
    ])


def voice_select_keyboard():
    """Ovoz tanlash"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👩 Ayol (Katja)", callback_data="set_voice_female")],
        [InlineKeyboardButton("👨 Erkak (Conrad)", callback_data="set_voice_male")],
        [InlineKeyboardButton("↩️ Sozlamalarga qaytish", callback_data="settings_menu")],
    ])


def speed_select_keyboard():
    """TTS tezlik tanlash"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐌 0.7x (Sekin)", callback_data="set_speed_0.7")],
        [InlineKeyboardButton("🚶 0.9x (O'rtacha)", callback_data="set_speed_0.9")],
        [InlineKeyboardButton("🏃 1.0x (Normal)", callback_data="set_speed_1.0")],
        [InlineKeyboardButton("⚡ 1.2x (Tez)", callback_data="set_speed_1.2")],
        [InlineKeyboardButton("🚀 1.5x (Juda tez)", callback_data="set_speed_1.5")],
        [InlineKeyboardButton("↩️ Sozlamalarga qaytish", callback_data="settings_menu")],
    ])


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sozlamalar menyusi"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    user = db.get_or_create_user(user_id)

    await query.edit_message_text(
        "⚙️ *Sozlamalar*\n\n"
        "Quyidagi sozlamalarni o'zgartiring:\n\n"
        "📊 *Daraja* \\- Joriy darajangiz\n"
        "👩 *Ovoz* \\- TTS ovozi (ayol/erkak)\n"
        "⏩ *TTS Tezlik* \\- Gapirish tezligi\n"
        "🔧 *Xatolar* \\- Xatolarni ko'rsatish/yashirish\n\n"
        "Tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=settings_menu_keyboard(user),
    )
    return -1


async def settings_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Daraja tanlash menyusi"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📊 *Daraja tanlash*\n\n"
        "O'z darajangizni tanlang:\n"
        "🟢 A1\\-A2: Boshlang'ich\n"
        "🟡 B1\\-B2: O'rta\n"
        "🔴 C1: Yuqori\n\n"
        "*Eslatma:* Darajani oshirish test va XP orqali avtomatik bo'ladi.",
        parse_mode="MarkdownV2",
        reply_markup=level_select_keyboard(),
    )
    return -1


async def settings_set_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Darajani o'rnatish"""
    query = update.callback_query
    await query.answer()

    level = query.data.replace("set_level_", "")
    user_id = query.from_user.id
    db = get_db()
    db.update_user(user_id, current_level=level)

    user = db.get_or_create_user(user_id)
    await query.edit_message_text(
        f"✅ *Daraja o'zgartirildi\\!*\n\n"
        f"Joriy daraja: {esc_md(LEVEL_LABELS.get(level, level))}",
        parse_mode="MarkdownV2",
        reply_markup=settings_menu_keyboard(user),
    )
    return -1


async def settings_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovoz tanlash menyusi"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👩 *Ovoz tanlash*\n\n"
        "TTS \\(matn \\-\\> ovoz\\) uchun ovoz tanlang:\n\n"
        "👩 *Katja* \\- Ayol ovozi\n"
        "👨 *Conrad* \\- Erkak ovozi",
        parse_mode="MarkdownV2",
        reply_markup=voice_select_keyboard(),
    )
    return -1


async def settings_set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovozni o'rnatish"""
    query = update.callback_query
    await query.answer()

    voice = query.data.replace("set_voice_", "")
    user_id = query.from_user.id
    db = get_db()
    db.update_user(user_id, voice_preference=voice)

    user = db.get_or_create_user(user_id)
    icon = "👩" if voice == "female" else "👨"
    await query.edit_message_text(
        f"{icon} *Ovoz o'zgartirildi\\!*\n\n"
        f"TTS ovozi: *{voice.capitalize()}*",
        parse_mode="MarkdownV2",
        reply_markup=settings_menu_keyboard(user),
    )
    return -1


async def settings_speed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """TTS tezlik tanlash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "⏩ *TTS Tezlik tanlash*\n\n"
        "Gapirish tezligini tanlang:\n\n"
        "🐌 *0\\.7x* \\- Sekin \\- yangi o'rganuvchilar uchun\n"
        "🚶 *0\\.9x* \\- O'rtacha sekin\n"
        "🏃 *1\\.0x* \\- Normal \\- standart\n"
        "⚡ *1\\.2x* \\- Tez \\- mashq qilganlar uchun\n"
        "🚀 *1\\.5x* \\- Juda tez \\- sinov uchun",
        parse_mode="MarkdownV2",
        reply_markup=speed_select_keyboard(),
    )
    return -1


async def settings_set_speed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """TTS tezlikni o'rnatish"""
    query = update.callback_query
    await query.answer()

    speed = float(query.data.replace("set_speed_", ""))
    user_id = query.from_user.id
    db = get_db()
    db.update_user(user_id, tts_speed=speed)

    user = db.get_or_create_user(user_id)
    await query.edit_message_text(
        f"⏩ *Tezlik o'zgartirildi\\!*\n\n"
        f"TTS tezlik: *{speed}x*",
        parse_mode="MarkdownV2",
        reply_markup=settings_menu_keyboard(user),
    )
    return -1


async def settings_mistakes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xatolar ko'rsatish/yashirish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    user = db.get_or_create_user(user_id)
    current = user.get("show_mistakes", 1)
    new_value = 0 if current == 1 else 1

    db.update_user(user_id, show_mistakes=new_value)
    user = db.get_or_create_user(user_id)

    label = "✅ Ko'rsatish" if new_value else "❌ Yashirish"
    await query.edit_message_text(
        f"🔧 *Xatolar: {esc_md(label)}*\n\n"
        f"AI Mentor suhbatlarida xatolaringiz {'ko\'rsatiladi' if new_value else 'yashiriladi'}.",
        parse_mode="MarkdownV2",
        reply_markup=settings_menu_keyboard(user),
    )
    return -1
