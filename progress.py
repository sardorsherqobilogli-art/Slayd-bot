#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - Progress Moduli
XP tizimi, Level Up, Daily Missions, Stats vizualizatsiya
"""

import os
import io
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    logger, XP_REWARDS, LEVEL_REQUIREMENTS, LEVEL_LABELS,
)
from database import get_db


def esc_md(text: str) -> str:
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ==================== PROGRESS MENU ====================

async def progress_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Progress menyusini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    stats = db.get_user_stats(user_id)

    if not stats:
        await query.edit_message_text(
            "❌ Ma'lumot topilmadi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
            ])
        )
        return -1  # No specific state

    current_level = stats.get("current_level", "a1")
    total_xp = stats.get("total_xp", 0)
    streak = stats.get("streak_days", 0)
    speaking = stats.get("speaking_score", 0)

    # Keyingi daraja uchun XP
    level_order = ["a1", "a2", "b1", "b2", "c1"]
    current_idx = level_order.index(current_level) if current_level in level_order else 0
    next_level = level_order[current_idx + 1] if current_idx < len(level_order) - 1 else None

    xp_needed = 0
    xp_progress = 100
    if next_level:
        reqs = LEVEL_REQUIREMENTS.get(next_level, {})
        xp_needed = reqs.get("xp", 0)
        xp_progress = min(100, int((total_xp / xp_needed) * 100)) if xp_needed > 0 else 100

    # Kunlik vazifalar
    missions = db.get_today_missions(user_id)
    completed = sum(1 for m in missions if m["is_completed"])
    total_missions = len(missions)

    text = (
        f"📊 *Mening Progressim*\n\n"
        f"📈 *Daraja:* {esc_md(LEVEL_LABELS.get(current_level, current_level))}\n"
        f"⭐ *XP:* {total_xp}\n"
    )

    if next_level:
        text += f"📊 *Keyingi darajagacha:* {total_xp}/{xp_needed} XP \\({xp_progress}%\\)\n"
    else:
        text += "🏆 *Eng yuqori daraja\\!*\n"

    text += (
        f"🔥 *Streak:* {streak} kun\n"
        f"🎤 *Speaking balli:* {speaking}/10\n"
        f"📚 *Bajarilgan lektsiyalar:* {stats.get('completed_lektions', 0)}\n"
        f"❌ *Faol xatolar:* {stats.get('active_mistakes', 0)}\n"
        f"📋 *Bugungi vazifalar:* {completed}/{total_missions}\n\n"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 Grafiklar", callback_data="progress_charts")],
            [InlineKeyboardButton("📋 Kunlik vazifalar", callback_data="progress_missions")],
            [InlineKeyboardButton("🎯 Level Up shartlari", callback_data="progress_levelup")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ])
    )
    return -1


# ==================== CHARTS ====================

async def progress_charts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Progress grafiklarini yaratish va yuborish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()

    # 1. XP tarixi (oxirgi 7 kun)
    xp_history = db.get_xp_history(user_id, days=7)
    
    # 2. Speaking tarixi
    speaking_history = db.get_speaking_history(user_id, limit=10)

    # Grafik yaratish
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("📊 Deutsch Meister Pro - Progress", fontsize=14, fontweight="bold")

    # --- Grafik 1: XP dinamikasi ---
    ax1 = axes[0, 0]
    if xp_history:
        dates = []
        amounts = []
        date_map = {}
        
        for entry in xp_history:
            date = entry["created_at"][:10]  # YYYY-MM-DD
            date_map[date] = date_map.get(date, 0) + entry["amount"]
        
        # So'nggi 7 kun
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            dates.append(date[5:])  # MM-DD
            amounts.append(date_map.get(date, 0))

        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(dates)))
        bars = ax1.bar(dates, amounts, color=colors, edgecolor='white', linewidth=0.5)
        ax1.set_title("📈 Kunlik XP", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Sana", fontsize=9)
        ax1.set_ylabel("XP", fontsize=9)
        ax1.tick_params(axis='x', rotation=45, labelsize=8)
        ax1.grid(axis='y', alpha=0.3)

        # Bar ustiga qiymat qo'shish
        for bar, val in zip(bars, amounts):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'{int(val)}', ha='center', va='bottom', fontsize=8)
    else:
        ax1.text(0.5, 0.5, "Hali ma'lumot yo'q", ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title("📈 Kunlik XP", fontsize=11)

    # --- Grafik 2: Daraja progressi ---
    ax2 = axes[0, 1]
    stats = db.get_user_stats(user_id)
    total_xp = stats.get("total_xp", 0)
    current_level = stats.get("current_level", "a1")

    level_order = ["a1", "a2", "b1", "b2", "c1"]
    level_names = ["A1", "A2", "B1", "B2", "C1"]
    level_xps = [LEVEL_REQUIREMENTS.get(l, {}).get("xp", 0) for l in level_order]

    # Progressni ko'rsatish
    current_idx = level_order.index(current_level) if current_level in level_order else 0
    progress_values = []
    colors_progress = []
    for i, req_xp in enumerate(level_xps):
        if i < current_idx:
            progress_values.append(100)
            colors_progress.append('#4CAF50')
        elif i == current_idx:
            next_req = LEVEL_REQUIREMENTS.get(level_order[min(i+1, 4)], {}).get("xp", total_xp + 100)
            prev_req = level_xps[i]
            progress = min(100, max(0, ((total_xp - prev_req) / (next_req - prev_req)) * 100)) if (next_req - prev_req) > 0 else 100
            progress_values.append(progress)
            colors_progress.append('#2196F3')
        else:
            progress_values.append(0)
            colors_progress.append('#E0E0E0')

    bars2 = ax2.barh(level_names, progress_values, color=colors_progress, edgecolor='white', height=0.5)
    ax2.set_title("📊 Daraja Progressi", fontsize=11, fontweight="bold")
    ax2.set_xlabel("%", fontsize=9)
    ax2.set_xlim(0, 100)
    ax2.grid(axis='x', alpha=0.3)

    for bar, val in zip(bars2, progress_values):
        if val > 0:
            ax2.text(val + 2, bar.get_y() + bar.get_height()/2.,
                    f'{int(val)}%', ha='left', va='center', fontsize=9, fontweight='bold')

    # --- Grafik 3: Speaking balli ---
    ax3 = axes[1, 0]
    if speaking_history:
        sessions = list(range(1, len(speaking_history) + 1))
        scores = [s["score"] for s in speaking_history]
        topics = [s.get("topic", "N/A")[:10] for s in speaking_history]

        ax3.plot(sessions[::-1], scores[::-1], marker='o', linewidth=2, markersize=8,
                color='#FF5722', markerfacecolor='#FF8A65', markeredgecolor='#FF5722', markeredgewidth=2)
        ax3.fill_between(sessions[::-1], scores[::-1], alpha=0.2, color='#FF5722')
        ax3.set_title("🎤 Speaking Balli", fontsize=11, fontweight="bold")
        ax3.set_xlabel("Session", fontsize=9)
        ax3.set_ylabel("Ball (0-10)", fontsize=9)
        ax3.set_ylim(0, 10)
        ax3.grid(alpha=0.3)

        # Nuqtalar ustiga ball qo'shish
        for x, y in zip(sessions[::-1], scores[::-1]):
            ax3.annotate(f'{y}', (x, y), textcoords="offset points", xytext=(0, 10),
                        ha='center', fontsize=8, fontweight='bold', color='#FF5722')
    else:
        ax3.text(0.5, 0.5, "Hali ma'lumot yo'q", ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title("🎤 Speaking Balli", fontsize=11)

    # --- Grafik 4: Faoliyat taqsimoti (pie chart) ---
    ax4 = axes[1, 1]
    activity_labels = ['Flashcard', 'AI Suhbat', 'Pomodoro', 'Xato tuzatish', 'Voice']
    activity_values = [
        stats.get("total_flashcards", 0) * 10,
        stats.get("total_conversations", 0) * 50,
        stats.get("total_pomodoro_minutes", 0),
        (stats.get("mastered_mistakes", 0)) * 20,
        0,  # Voice practice count would need separate query
    ]

    if sum(activity_values) > 0:
        colors_pie = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63']
        wedges, texts, autotexts = ax4.pie(
            activity_values, labels=activity_labels, autopct='%1.0f%%',
            colors=colors_pie, startangle=90, textprops={'fontsize': 9}
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        ax4.set_title("📊 Faoliyat Taqsimoti", fontsize=11, fontweight="bold")
    else:
        ax4.text(0.5, 0.5, "Hali ma'lumot yo'q", ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title("📊 Faoliyat Taqsimoti", fontsize=11)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Grafikni saqlash va yuborish
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    await query.edit_message_text("📊 *Progress grafiklari yuklanmoqda...*", parse_mode="MarkdownV2")
    
    import telegram
    photo = telegram.InputFile(buf, filename="progress.png")
    
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    await query.message.reply_photo(
        photo=photo,
        caption="📊 *Sizning Progress Grafiklaringiz*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Kunlik vazifalar", callback_data="progress_missions")],
            [InlineKeyboardButton("🎯 Level Up shartlari", callback_data="progress_levelup")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ])
    )

    return -1


# ==================== DAILY MISSIONS ====================

async def progress_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kunlik vazifalarni ko'rsatish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    missions = db.generate_daily_missions(user_id)

    if not missions:
        await query.edit_message_text(
            "📋 *Kunlik vazifalar*\n\nBugun vazifalar yo'q.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
            ])
        )
        return -1

    text = "📋 *Kunlik vazifalar*\n\n"
    total_xp = 0
    completed_count = 0

    for i, m in enumerate(missions, 1):
        status = "✅" if m["is_completed"] else "⬜"
        progress = f"({m['current_count']}/{m['target_count']})"
        xp = m["xp_reward"]
        total_xp += xp
        if m["is_completed"]:
            completed_count += 1

        text += f"{status} *{i}\\.* {esc_md(m['description'])} {progress} \\+{xp} XP\n"

    text += f"\n📊 *Jami:* {completed_count}/{len(missions)} bajarildi\n"
    text += f"🎁 *Mumkin bo'lgan XP:* {total_xp}"

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Progress", callback_data="progress_menu")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ])
    )
    return -1


# ==================== LEVEL UP REQUIREMENTS ====================

async def progress_levelup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Level Up shartlarini ko'rsatish"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = get_db()
    stats = db.get_user_stats(user_id)
    current_level = stats.get("current_level", "a1")

    level_order = ["a1", "a2", "b1", "b2", "c1"]
    current_idx = level_order.index(current_level) if current_level in level_order else 0

    if current_idx >= len(level_order) - 1:
        await query.edit_message_text(
            "🏆 *Tabriklaymiz\\!*\n\n"
            "Siz eng yuqori C1 darajadasiz\\! 🎉\n\n"
            "Davom eting! Yangi mavzular qo'shilmoqda...",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
            ])
        )
        return -1

    next_level = level_order[current_idx + 1]
    reqs = LEVEL_REQUIREMENTS.get(next_level, {})
    total_xp = stats.get("total_xp", 0)
    speaking = stats.get("speaking_score", 0)
    completed = stats.get("completed_lektions", 0)

    text = (
        f"🎯 *{esc_md(LEVEL_LABELS.get(current_level, current_level))}* \\→ "
        f"*{esc_md(LEVEL_LABELS.get(next_level, next_level))}*\n\n"
        f"*Shartlar:*\n\n"
    )

    # XP sharti
    xp_req = reqs.get("xp", 0)
    xp_done = min(total_xp, xp_req)
    xp_icon = "✅" if total_xp >= xp_req else "⏳"
    text += f"{xp_icon} *XP:* {xp_done}/{xp_req}\n"

    # Lektsiya sharti
    lekt_req = reqs.get("lektion", 0)
    lekt_done = min(completed, lekt_req)
    lekt_icon = "✅" if completed >= lekt_req else "⏳"
    text += f"{lekt_icon} *Lektsiyalar:* {lekt_done}/{lekt_req}\n"

    # Speaking sharti
    speak_req = reqs.get("speaking_score", 0)
    speak_done = min(speaking, speak_req)
    speak_icon = "✅" if speaking >= speak_req else "⏳"
    text += f"{speak_icon} *Speaking balli:* {speak_done}/{speak_req}\n"

    text += (
        f"\n📊 *Joriy progress:*\n"
        f"⭐ XP: {total_xp}\n"
        f"📚 Lektsiyalar: {completed}\n"
        f"🎤 Speaking: {speaking}/10\n"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Grafiklar", callback_data="progress_charts")],
            [InlineKeyboardButton("📋 Kunlik vazifalar", callback_data="progress_missions")],
            [InlineKeyboardButton("🏠 Asosiy menu", callback_data="main_menu")],
        ])
    )
    return -1
