"""
AI German Mentor - Konfiguratsiya
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ============ ASOSIY SOZLAMALAR ============
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "german_mentor.db")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ============ LOGGING ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ DARAJALAR ============
LEVEL_XP_REQUIREMENTS = {
    "a1": 0,
    "a2": 500,
    "b1": 1000,
    "b2": 2000,
}

XP_REWARDS = {
    "vocab_learned": 20,
    "test_passed": 30,
    "roleplay_complete": 60,
    "mistake_fixed": 10,
    "voice_practice": 40,
}
