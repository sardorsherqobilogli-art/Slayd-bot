# 🇩🇪 Deutsch Meister PRO — Telegram Bot

Nemis tili o'rgatuvchi AI-powered Telegram bot.

## 📦 O'rnatish

```bash
pip install -r requirements.txt
```

## ⚙️ Sozlash

```bash
cp .env.example .env
# .env faylini oching va tokenlarni kiriting
```

## 🚀 Ishga tushirish

```bash
python main.py
```

## 🌐 Railway Deploy

Environment Variables:
- `BOT_TOKEN` — Telegram bot token (@BotFather dan)
- `GROQ_API_KEY` — Groq API key (groq.com dan)

## 📁 Modullar

| Fayl | Vazifa |
|------|--------|
| `main.py` | Asosiy bot, barcha handlerlar (1349 satr) |
| `ai_mentor.py` | AI Mentor — daraja, vorstellen, roleplay (1455 satr) |
| `database.py` | SQLite ma'lumotlar bazasi (732 satr) |
| `config.py` | Konfiguratsiya, XP, levels (266 satr) |
| `voice_engine.py` | Edge TTS + Groq Whisper STT (273 satr) |
| `progress.py` | XP tizimi, grafiklar (401 satr) |
| `settings.py` | Foydalanuvchi sozlamalari (244 satr) |
| `lektion_data.py` | A1 Motive lektsiyalari (718 satr) |

## 🔧 Tuzatilgan buglar

1. `ai_mentor.py` — `db._connect()` noto'g'ri ishlatilgan → `with db._connect()` ga tuzatildi
2. `main.py` — `LEKTION_PAGE` state ConversationHandler'ga qo'shildi
3. `main.py` — `translator_ai_analysis` callback handler qo'shildi
4. `config.py` — Windows CRLF (`\r\n`) tozalandi
5. `voice_engine.py` — `None` audio xatoligi xavfsiz usulda ushlandi
