#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - Markaziy Konfiguratsiya
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
DATABASE_PATH = os.environ.get("DATABASE_PATH", "deutsch_meister.db")

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
    "c1": "🔴 C1 - Advanced",
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
        "a1_sign": "Men... yoshdaman gap tuzilishi",
        "b1_sign": "25-jahre alt emas, 25 Jahre alt",
    },
    {
        "question": "🎯 *Savol 2/5*\n\nQuyidagi so'zlarni ko'plikka o'zgartiring:\n\n*das Buch → ?\nder Stuhl → ?\ndie Frau → ?*",
        "check": lambda ans: all(w in ans.lower() for w in ["bücher", "stühle", "frauen"]),
        "hints": ["die Bücher", "die Stühle", "die Frauen"],
        "a1_sign": "-s qo'shish xatosi (Buchs)",
        "b1_sign": "Umlaut + -e/-er (Bücher, Stühle)",
    },
    {
        "question": "🎯 *Savol 3/5*\n\nPerfekt zamon yasang:\n\n*Ich (essen) ein Brot*",
        "check": lambda ans: "habe" in ans.lower() and "gegessen" in ans.lower(),
        "hints": ["ich habe", "gegessen"],
        "a1_sign": "'geessen' yoki 'essen' xatosi",
        "b1_sign": "habe + gegessen (Partizip II)",
    },
    {
        "question": "🎯 *Savol 4/5*\n\nPassiv zamon yasang:\n\n*Das Haus (bauen) → ?*",
        "check": lambda ans: "wird" in ans.lower() and "gebaut" in ans.lower(),
        "hints": ["Das Haus wird", "gebaut"],
        "a1_sign": "Passiv umuman bilmaydi",
        "a2_sign": "'ist gebaut' (Zustandspassiv xatosi)",
        "b1_sign": "'wird gebaut' (Vorgangspassiv)",
    },
    {
        "question": "🎯 *Savol 5/5*\n\nKonjunktiv II yasang:\n\n*Wenn ich Zeit (haben), ...*",
        "check": lambda ans: "hätte" in ans.lower(),
        "hints": ["hätte", "würde"],
        "a1_sign": "'habe' ishlatish (Konjunktiv bilmaydi)",
        "b2_sign": "'hätte' (Konjunktiv II)",
    },
]

VORSTELLEN_PROMPTS = {
    "intro": (
        "Siz nemis tilini o'rganuvchi sifatida o'zingizni taqdim eting. "
        "Quyidagi mavzularni qamrab oling: ismingiz, yoshingiz, millatingiz, "
        "kasbingiz/hobbiyingiz, nemis tilini nega o'rganayotganingiz."
        "O'zbek tilida yoki nemis tilida javob bering."
    ),
    "follow_up": [
        "Qiziqarli! Endi nemis tilida qisqacha ayting: Was machst du gern in deiner Freizeit?",
        "Juda yaxshi! Wie heißt du und woher kommst du? (Ismingiz va qayerdaligingizni ayting)",
        "Super! Warum lernst du Deutsch? (Nima uchun nemis tilini o'rganmoqdasiz?)",
    ],
}

ERFAHRUNGEN_TOPICS = {
    "freizeit": {
        "name": "🎯 Freizeit (Bo'sh vaqt)",
        "easy": "Was machst du gern in deiner Freizeit?",
        "medium": "Wie hat sich dein Hobby in den letzten 10 Jahren verändert?",
        "hard": "Können Hobbys die Gesellschaft beeinflussen? Diskutieren Sie!",
    },
    "reisen": {
        "name": "✈️ Reisen (Sayohat)",
        "easy": "Wo warst du zuletzt im Urlaub?",
        "medium": "Was sind die Vorteile und Nachteile von Reisen allein?",
        "hard": "Ist Tourismus eher ein Segen oder ein Fluch für lokale Kulturen?",
    },
    "arbeit": {
        "name": "💼 Arbeit (Ish)",
        "easy": "Was ist dein Traumberuf?",
        "medium": "Wie wichtig ist Work-Life-Balance für dich?",
        "hard": "Sollte die Woche vier Arbeitstage haben? Argumentieren Sie!",
    },
    "bildung": {
        "name": "📚 Bildung (Ta'lim)",
        "easy": "Welches Fach hast du am liebsten in der Schule?",
        "medium": "Sind Online-Kurse genauso effektiv wie Präsenzunterricht?",
        "hard": "Sollte das Studium kostenlos sein? Diskutieren Sie!",
    },
    "technologie": {
        "name": "📱 Technologie (Texnologiya)",
        "easy": "Welche Apps benutzt du täglich?",
        "medium": "Wie hat das Smartphone unser Leben verändert?",
        "hard": "Sollte künstliche Intelligenz reguliert werden?",
    },
    "umwelt": {
        "name": "🌍 Umwelt (Atrof-muhit)",
        "easy": "Was tust du für die Umwelt?",
        "medium": "Sollte jeder Mensch vegan leben, um die Umwelt zu schützen?",
        "hard": "Ist der Klimawandel das größte Problem der Menschheit?",
    },
    "gesundheit": {
        "name": "🏥 Gesundheit (Sog'liq)",
        "easy": "Wie oft sportelst du?",
        "medium": "Sollte der Staat für gesunde Ernährung sorgen?",
        "hard": "Ist die Mental Health in der modernen Gesellschaft unterschätzt?",
    },
    "kultur": {
        "name": "🎭 Kultur (Madaniyat)",
        "easy": "Welche Filme oder Bücher magst du?",
        "medium": "Sind Streaming-Dienste gut für die Kultur?",
        "hard": "Kann man Kultur überhaupt bewerten? Diskutieren Sie!",
    },
    "familie": {
        "name": "👨‍👩‍👧 Familie (Oila)",
        "easy": "Wie groß ist deine Familie?",
        "medium": "Sollten Großeltern bei der Kindererziehung helfen?",
        "hard": "Ist die traditionelle Familie heute noch zeitgemäß?",
    },
    "zukunft": {
        "name": "🔮 Zukunft (Kelajak)",
        "easy": "Wo siehst du dich in 5 Jahren?",
        "medium": "Würdest du ins Ausland ziehen, wenn du eine gute Jobangebot bekommst?",
        "hard": "Wird die Welt in 50 Jahren besser oder schlechter sein?",
    },
}

ROLEPLAY_SCENARIOS = {
    "restaurant": {
        "name": "🍽️ Restoranda",
        "setup": "Siz restorandasiz. Ofitsiant (AI) sizga keladi. Buyurtma bering!",
        "ai_role": "Sie sind ein freundlicher Kellner/Kellnerin in einem deutschen Restaurant. Begrüßen Sie den Gast, erklären Sie die Tagesgerichte und nehmen Sie die Bestellung auf. Sprechen Sie natürlich und höflich.",
        "vocab": ["die Speisekarte", "die Bestellung", "die Rechnung", "das Trinkgeld", "schmecken"],
    },
    "arzt": {
        "name": "🏥 Shifokor qabulida",
        "setup": "Siz shifokor qabulidasiz. Shifokor (AI) sizga sog'liqingiz haqida so'raydi.",
        "ai_role": "Sie sind ein freundlicher Arzt/Ärztin. Fragen Sie den Patienten nach Symptomen, Schmerzen und medizinischer Vorgeschichte. Geben Sie medizinische Ratschläge.",
        "vocab": ["die Symptome", "der Schmerz", "das Fieber", "die Grippe", "die Apotheke"],
    },
    "hotel": {
        "name": "🏨 Mehmonxonada",
        "setup": "Siz mehmonxonadasiz. Resepsionist (AI) sizga xona beradi.",
        "ai_role": "Sie sind ein Hotel-Rezeptionist. Begrüßen Sie den Gast, fragen Sie nach dem Aufenthalt, bieten Sie Zimmeroptionen an und erklären Sie die Hotelregeln.",
        "vocab": ["die Reservierung", "das Zimmer", "der Schlüssel", "das Frühstück", "auschecken"],
    },
    "bahnhof": {
        "name": "🚉 Vokzalda",
        "setup": "Siz vokzaldasiz. Kassir (AI) sizga chipta sotadi.",
        "ai_role": "Sie sind ein Mitarbeiter am deutschen Bahnhofsschalter. Helfen Sie dem Kunden bei der Fahrplanauskunft und verkaufen Sie ein Ticket.",
        "vocab": ["die Fahrkarte", "der Zug", "der Bahnsteig", "die Ankunft", "die Abfahrt"],
    },
    "einkaufen": {
        "name": "🛍️ Do'konda",
        "setup": "Siz kiyim do'konidasiz. Sotuvchi (AI) sizga yordam beradi.",
        "ai_role": "Sie sind ein Verkäufer/Verkäuferin in einem Kleidungsgeschäft. Begrüßen Sie den Kunden, fragen Sie nach der Größe und dem Geschmack und zeigen Sie passende Artikel.",
        "vocab": ["die Größe", "die Farbe", "die Umkleidekabine", "der Preis", "die Rabatt"],
    },
    "bewerbung": {
        "name": "📄 Ish intervyu",
        "setup": "Siz ish intervyusidasiz. HR menejeri (AI) sizga savollar beradi.",
        "ai_role": "Sie sind ein HR-Manager und führen ein Vorstellungsgespräch auf Deutsch. Stellen Sie Fragen zur Qualifikation, Erfahrung und Motivation des Bewerbers.",
        "vocab": ["die Bewerbung", "das Vorstellungsgespräch", "die Erfahrung", "die Qualifikation", "das Gehalt"],
    },
}

VOICE_VOCAB_CATEGORIES = {
    "alltag": "Kundalik hayot (Alltag)",
    "essen": "Oziq-ovqat (Essen)",
    "reisen": "Sayohat (Reisen)",
    "familie": "Oila (Familie)",
    "arbeit": "Ish (Arbeit)",
    "gefuehle": "His-hayajon (Gefühle)",
}

# ==================== GROQ API ====================
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

DEFAULT_AI_MODEL = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3"

# ==================== TTS VOICES ====================
TTS_VOICES = {
    "female": "de-DE-KatjaNeural",  # Microsoft Edge TTS
    "male": "de-DE-ConradNeural",
}
