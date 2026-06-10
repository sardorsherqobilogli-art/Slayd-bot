"""
Voice Engine - Ovoz moduli
EdgeTTS (bepul, Microsoft) + Groq Whisper (bepul tier)
"""
import os
import io
import asyncio
import edge_tts


class EdgeTTS:
    """Microsoft Edge TTS - nemis ovozi (BEPUL)"""

    VOICES = {
        "female": "de-DE-KatjaNeural",
        "male": "de-DE-ConradNeural",
    }

    @staticmethod
    async def text_to_speech(text: str, gender: str = "female", speed: float = 1.0) -> bytes:
        """Matnni ovozga aylantirish"""
        try:
            voice = EdgeTTS.VOICES.get(gender, EdgeTTS.VOICES["female"])
            rate = f"+{int((speed - 1) * 100)}%" if speed != 1.0 else "+0%"

            communicate = edge_tts.Communicate(text, voice, rate=rate)
            audio_bytes = io.BytesIO()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.write(chunk["data"])

            audio_bytes.seek(0)
            return audio_bytes.read()
        except Exception as e:
            print(f"EdgeTTS xatolik: {e}")
            return b""


class WhisperSTT:
    """Groq Whisper STT - ovozni matnga aylantirish (BEPUL tier)"""

    @staticmethod
    async def speech_to_text(voice_file_path: str, language: str = "de") -> str:
        """Ovoz faylini matnga aylantirish - faqat Groq Whisper ishlatadi"""
        try:
            groq_key = os.getenv("GROQ_API_KEY", "")
            if not groq_key:
                print("WhisperSTT: GROQ_API_KEY topilmadi")
                return ""

            from groq import Groq
            groq_client = Groq(api_key=groq_key)

            with open(voice_file_path, "rb") as f:
                transcription = groq_client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=f,
                    language=language
                )
            return transcription.text

        except Exception as e:
            print(f"WhisperSTT xatolik: {e}")
            return ""


async def speak_text(text: str, gender: str = "female") -> bytes:
    """Qisqa ovoz yaratish"""
    return await EdgeTTS.text_to_speech(text, gender)


async def listen_to_voice(file_path: str) -> str:
    """Ovozni tinglash"""
    return await WhisperSTT.speech_to_text(file_path)
