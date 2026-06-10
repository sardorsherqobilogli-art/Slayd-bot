#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - Ovoz Dvigateli
Edge TTS (matn→ovoz) + Groq Whisper (ovoz→matn)
"""

import os
import io
import asyncio
import tempfile
import httpx
import edge_tts

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    logger, GROQ_API_KEY, GROQ_WHISPER_URL, WHISPER_MODEL,
    TTS_VOICES, DEFAULT_AI_MODEL, GROQ_API_URL,
)


# ==================== EDGE TTS ====================

class EdgeTTS:
    """Microsoft Edge TTS — bepul, German neural ovoz"""

    @staticmethod
    async def text_to_speech(text: str, voice: str = None, speed: float = 1.0) -> bytes:
        """
        Matnni ovozga aylantirish (mp3 bytes qaytaradi)
        voice: 'female' → de-DE-KatjaNeural, 'male' → de-DE-ConradNeural
        speed: 0.5 (sekin) → 2.0 (tez)
        """
        voice_key = voice if voice in TTS_VOICES else "female"
        voice_name = TTS_VOICES[voice_key]

        # Tezlikni edge_tts formatiga o'tkazish: 1.0 → "+0%", 1.5 → "+50%", 0.5 → "-50%"
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        # 403 xatosida 2 marta qayta urinish
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                if not audio_chunks:
                    logger.error("Edge TTS: audio chunk kelmadi")
                    return None
                return b"".join(audio_chunks)
            except Exception as e:
                logger.error(f"Edge TTS xato (urinish {attempt+1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                else:
                    return None

    @staticmethod
    async def send_voice_message(update: Update, text: str, voice: str = "female",
                                  speed: float = 1.0, caption: str = None):
        """
        Telegram voice xabar yuborish (TTS orqali)
        CallbackQuery yoki Message orqali ham ishlaydi.
        """
        import telegram

        # CallbackQuery yoki Message dan to'g'ri message objectini olish
        if update.callback_query:
            message = update.callback_query.message
        elif update.message:
            message = update.message
        else:
            logger.error("send_voice_message: message topilmadi")
            return False

        audio_bytes = await EdgeTTS.text_to_speech(text, voice, speed)
        if not audio_bytes:
            await message.reply_text("❌ Ovoz yaratishda xato yuz berdi.")
            return False

        try:
            voice_file = telegram.InputFile(io.BytesIO(audio_bytes), filename="voice.mp3")
            await message.reply_voice(
                voice=voice_file,
                caption=caption or text[:200],
            )
            return True
        except Exception as e:
            logger.error(f"Voice xabar yuborish xatosi: {e}")
            await message.reply_text(
                f"🔊 *{text}*\n\n_(Ovozli xabar yuborishda xato)_",
            )
            return False


# ==================== GROQ WHISPER STT ====================

class WhisperSTT:
    """Groq Whisper — ovozni matnga o'girish"""

    @staticmethod
    async def speech_to_text(audio_file_path: str, language: str = "de") -> str:
        """
        Audio faylni matnga o'girish
        audio_file_path: .oga, .mp3, .wav fayl
        language: 'de' (nemis), 'uz' (o'zbek)
        """
        if not GROQ_API_KEY:
            return "❌ Groq API kaliti sozlanmagan."

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(audio_file_path, "rb") as f:
                    files = {"file": ("audio.ogg", f, "audio/ogg")}
                    data = {
                        "model": WHISPER_MODEL,
                        "language": language,
                        "response_format": "text",
                    }
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

                    resp = await client.post(
                        GROQ_WHISPER_URL,
                        headers=headers,
                        files=files,
                        data=data,
                    )

                if resp.status_code == 200:
                    return resp.text.strip()
                else:
                    logger.error(f"Whisper xatosi: {resp.status_code} - {resp.text}")
                    return f"❌ Ovozni tanishda xato ({resp.status_code})"

        except Exception as e:
            logger.error(f"Whisper STT xato: {e}")
            return f"❌ Ovozni qayta ishlashda xato: {str(e)}"

    @staticmethod
    async def process_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     language: str = "de") -> str:
        """
        Telegram voice xabarini qabul qilib matnga o'girish
        """
        voice = update.message.voice or update.message.audio
        if not voice:
            return "❌ Ovoz xabari topilmadi."

        # File ni yuklab olish
        file_obj = await voice.get_file()

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
            await file_obj.download_to_drive(tmp_path)

        try:
            text = await WhisperSTT.speech_to_text(tmp_path, language)
            return text
        finally:
            # Vaqtinchalik faylni o'chirish
            try:
                os.unlink(tmp_path)
            except:
                pass


# ==================== PRONUNCIATION ANALYSIS ====================

class PronunciationAnalyzer:
    """Talaffuzni tahlil qilish (Groq LLM orqali)"""

    @staticmethod
    async def analyze_pronunciation(german_word: str, user_text: str) -> dict:
        """
        Foydalanuvchi talaffuzini tahlil qilish
        Qaytaradi: {"score": float, "feedback": str, "correct": bool}
        """
        if not GROQ_API_KEY:
            return {"score": 0, "feedback": "AI tahlir o'chirilgan", "correct": False}

        prompt = f"""Siz nemis tili o'qituvchisisiz. Quyidagi so'zning talaffuzini tahlil qiling:

So'z: "{german_word}"
Foydalanuvchi aytdi: "{user_text}"

Quyidagi formatda javob bering (faqat JSON):
{{
    "score": 0-10 (talaffuz aniqligi),
    "feedback": "qisqa tahlil o'zbek tilida",
    "correct": true/false,
    "tips": "yaxshilash uchun maslahat"
}}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": DEFAULT_AI_MODEL,
                        "max_tokens": 512,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                    },
                )

                data = resp.json()
                result_text = data["choices"][0]["message"]["content"]
                import json
                result = json.loads(result_text)
                return result

        except Exception as e:
            logger.error(f"Talaffuz tahlili xatosi: {e}")
            # Oddiy solishtirish
            similarity = PronunciationAnalyzer._simple_similarity(german_word.lower(), user_text.lower())
            return {
                "score": similarity,
                "feedback": f"'{user_text}' aytdingiz. To'g'ri: '{german_word}'",
                "correct": similarity >= 7,
                "tips": "So'zni bo'g'inlab, uzoq talaffuz qilib ayting",
            }

    @staticmethod
    def _simple_similarity(word1: str, word2: str) -> float:
        """Oddiy o'xshashlik balli (0-10)"""
        if word1 == word2:
            return 10.0

        # Levenshtein masofasi
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if word1[i - 1] == word2[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

        max_len = max(m, n)
        if max_len == 0:
            return 10.0

        similarity = (1 - dp[m][n] / max_len) * 10
        return round(max(0, min(10, similarity)), 1)


# ==================== CONVENIENCE FUNCTIONS ====================

async def speak_text(update: Update, text: str, voice: str = "female",
                     speed: float = 1.0, caption: str = None):
    """Qulay funksiya - matnni ovozli xabar sifatida yuborish"""
    return await EdgeTTS.send_voice_message(update, text, voice, speed, caption)


async def listen_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE = None,
                          language: str = "de") -> str:
    """Qulay funksiya - ovoz xabarini matnga o'girish"""
    return await WhisperSTT.process_voice_message(update, context, language)


async def analyze_pronunciation(german_word: str, user_text: str) -> dict:
    """Qulay funksiya - talaffuzni tahlil qilish"""
    return await PronunciationAnalyzer.analyze_pronunciation(german_word, user_text)
