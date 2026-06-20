#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - Markaziy Konfiguratsiya
YANGILANGAN VERSION
"""

import os
import logging

# ==================== LOGGING ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== ENVIRONMENT ====================
TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3"
DEFAULT_AI_MODEL = "llama3-70b-8192"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "deutsch_meister.db")

# ==================== TTS VOICES (Edge TTS) ====================
TTS_VOICES = {
    "female": "de-DE-KatjaNeural",
    "male": "de-DE-ConradNeural",
}

# ==================== XP SYSTEM ====================
XP_REWARDS = {
    "flashcard_correct": 10,
    "flashcard_complete": 50,
    "ai_conversation": 50,
    "mistake_corrected": 20,
    "pomodoro_25min": 30,
    "level_up_bonus": 100,
    "daily_mission_complete": 100,
    "voice_practice": 25,
    "roleplay_complete": 40,
    "quiz_perfect": 75,
    "vorstellen": 30,
    "vocab_test_correct": 5,
    "vocab_sprechen": 30,
}

# ==================== LEVEL UP REQUIREMENTS ====================
LEVEL_REQUIREMENTS = {
    "a1": {"xp": 0, "lektion": 0, "speaking_score": 0},
    "a2": {"xp": 500, "lektion": 8, "speaking_score": 7},
    "b1": {"xp": 1200, "lektion": 16, "speaking_score": 8},
    "b2": {"xp": 2500, "lektion": 24, "speaking_score": 9},
    "c1": {"xp": 4500, "lektion": 32, "speaking_score": 10},
}

# ==================== LEVEL LABELS ====================
LEVEL_LABELS = {
    "a1": "🟢 A1 - Beginner",
    "a2": "🟢 A2 - Elementary",
    "b1": "🟡 B1 - Intermediate",
    "b2": "🟡 B2 - Upper-Intermediate",
    "c1": "🔵 C1 - Advanced",
    "c2": "🔴 C2 - Mastery",
}

# ==================== BOOK CONFIG ====================
BOOK_LABELS = {
    "motive": "📗 MOTIVE",
    "schritte": "📙 SCHRITTE",
    "menschen": "📕 MENSCHEN",
    "sicher": "📗 Sicher",
    "kompassdaf": "📙 KompassDaF",
    "aspekte": "📕 Aspekte",
}

LEVEL_BOOKS = {
    "a1": ["motive", "schritte", "menschen"],
    "a2": ["motive", "schritte", "menschen"],
    "b1": ["motive", "schritte", "menschen"],
    "b2": ["sicher", "kompassdaf", "aspekte"],
    "c1": ["sicher", "kompassdaf", "aspekte"],
}

BOOK_LEKTIONS = {
    "a1_motive": (1, 8),
    "a1_schritte": (1, 14),
    "a1_menschen": (1, 24),
    "a2_motive": (9, 18),
    "a2_schritte": (1, 14),
    "a2_menschen": (1, 24),
    "b1_motive": (19, 30),
    "b1_schritte": (1, 14),
    "b1_menschen": (1, 24),
    "b2_sicher": (1, 12),
    "b2_kompassdaf": (1, 10),
    "b2_aspekte": (1, 10),
    "c1_sicher": (1, 12),
    "c1_kompassdaf": (1, 10),
    "c1_aspekte": (1, 10),
}

# ==================== AI MENTOR TOPICS ====================
LEVEL_DETECTION_QUESTIONS = [
    {
        "question": "🎯 *Savol 1/5*\n\nQuyidagi gapni nemischa tarjima qiling:\n\n*'Men 25 yoshdaman va Germaniyada yashayman'*",
        "check": lambda ans: any(w in ans.lower() for w in ["ich bin", "jahre alt", "wohne", "lebe", "deutschland", "in deutschland"]),
        "hints": ["ich bin", "jahre alt", "wohne", "Deutschland"],
    },
    {
        "question": "🎯 *Savol 2/5*\n\nQaysi variant to'g'ri?\n\n*'Ich ___ ein Student.'*",
        "check": lambda ans: "bin" in ans.lower(),
        "hints": ["bin", "bist", "ist", "sind"],
    },
    {
        "question": "🎯 *Savol 3/5*\n\nNemis tilida 'Men kechqurun kitob o'qiyman' ni yozing:",
        "check": lambda ans: any(w in ans.lower() for w in ["abends", "lese", "buch", "lese ein buch"]),
        "hints": ["Abends", "lese", "ein Buch"],
    },
    {
        "question": "🎯 *Savol 4/5*\n\nQuyidagi gapni to'ldiring:\n\n*'Gestern ___ ich ins Kino gegangen.'*",
        "check": lambda ans: "bin" in ans.lower() or "war" in ans.lower(),
        "hints": ["war", "bin", "habe", "ist"],
    },
    {
        "question": "🎯 *Savol 5/5*\n\nKonjunktiv II shaklida gap tuzing:\n\n*'Agar vaqtim bo'lsa, Germaniyaga borardim.'*",
        "check": lambda ans: any(w in ans.lower() for w in ["wenn", "hätte", "würde", "fahren", "gehen"]),
        "hints": ["Wenn ich Zeit hätte", "würde"],
    },
]

VORSTELLEN_PROMPTS = {
    "intro": "Stellen Sie sich vor! Erzählen Sie über sich.",
    "followup": "Sehr gut! Erzählen Sie mehr über Ihre Familie und Ihren Beruf.",
}

ERFAHRUNGEN_TOPICS = {
    "arbeit": {"name": "💼 Arbeit und Beruf", "easy": "Erzählen Sie von Ihrem Beruf.", "medium": "Was gefällt Ihnen an Ihrer Arbeit?", "hard": "Wie stellen Sie sich Ihre berufliche Zukunft vor?"},
    "reisen": {"name": "✈️ Reisen und Urlaub", "easy": "Erzählen Sie von Ihrem letzten Urlaub.", "medium": "Welche Reiseziele möchten Sie besuchen?", "hard": "Was bedeutet Reisen für Sie persönlich?"},
    "bildung": {"name": "🎓 Bildung und Lernen", "easy": "Erzählen Sie von Ihrer Schule.", "medium": "Warum lernen Sie Deutsch?", "hard": "Wie verändert sich das Bildungssystem?"},
    "gesellschaft": {"name": "🏙️ Gesellschaft und Kultur", "easy": "Erzählen Sie von Ihrem Land.", "medium": "Welche kulturellen Unterschiede gibt es?", "hard": "Wie beeinflusst Globalisierung die Kultur?"},
    "umwelt": {"name": "🌍 Umwelt und Nachhaltigkeit", "easy": "Was machen Sie für die Umwelt?", "medium": "Welche Umweltprobleme gibt es?", "hard": "Wie kann man Nachhaltigkeit fördern?"},
    "technologie": {"name": "💻 Technologie und Digitalisierung", "easy": "Welche Technologien nutzen Sie?", "medium": "Wie verändert Technologie unser Leben?", "hard": "Ist künstliche Intelligenz gefährlich?"},
    "gesundheit": {"name": "🏥 Gesundheit und Sport", "easy": "Wie halten Sie sich fit?", "medium": "Was ist wichtig für Gesundheit?", "hard": "Wie sollte das Gesundheitssystem verbessert werden?"},
    "familie": {"name": "👨‍👩‍👧 Familie und Beziehungen", "easy": "Erzählen Sie von Ihrer Familie.", "medium": "Was ist wichtig in einer Beziehung?", "hard": "Wie verändert sich die Familie in der modernen Gesellschaft?"},
    "kunst": {"name": "🎨 Kunst und Literatur", "easy": "Welche Kunst mögen Sie?", "medium": "Welches Buch haben Sie zuletzt gelesen?", "hard": "Welche Rolle spielt Kunst in der Gesellschaft?"},
    "politik": {"name": "🏛️ Politik und Wirtschaft", "easy": "Was interessiert Sie an Politik?", "medium": "Wie beeinflusst Politik das tägliche Leben?", "hard": "Welche wirtschaftlichen Herausforderungen gibt es?"},
}
