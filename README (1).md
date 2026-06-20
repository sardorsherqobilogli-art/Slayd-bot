# 🇩🇪 Deutsch Meister PRO - Telegram Bot

Nemis tilini o'rganish uchun professional AI-powered Telegram bot.

## 🚀 Imkoniyatlar

### 1. 🤖 AI Mentor
- 🎯 **Darajani aniqlash** - 5 ta savol bilan A1-C1 darajani aniqlash
- 🎤 **Vorstellen** - O'zingizni taqdim etish mashqi (Goethe/TELC uslubi)
- 💬 **Erfahrungen** - B2/C1 mavzularida suhbatlashish
- 🔧 **Xato banki** - Xatolaringizni saqlash va mini-darslar
- 📚 **Ovozli lug'at** - A1-B2, 20 mavzu, 25 so'z
- 🎭 **Rolli o'yinlar** - TELC/Goethe imtihoniga tayyorgarlik

### 2. 📖 Lug'at
- Darajaga qarab so'zlar (A1-C1)
- Admin tomonidan yuklanadigan kitoblar va bo'limlar
- Ovozda eshitish va test qilish

### 3. 🌐 Tarjimon
- UZB ↔ DEU tarjima
- AI grammatika tushuntirish bilan

### 4. 📚 Sayfa
- Kitob va audio materiallar
- PDF va audio fayllar

### 5. 📚 Kitob Materiallar
- A1-C2 darajalarida kitoblar
- PDF, audio, video fayllar
- Admin tomonidan yuklanadi

### 6. 📖 Kunlik so'z
- Har kuni yangi so'z
- AI generatsiyasi

## 📦 O'rnatish

```bash
pip install -r requirements.txt
```

## ⚙️ Sozlash

```bash
cp .env.example .env
# .env faylini oching va tokenlarni kiriting
```

### Environment Variables:
- `BOT_TOKEN` - Telegram bot token (@BotFather dan)
- `GROQ_API_KEY` - Groq API key (groq.com dan)
- `ADMIN_IDS` - Admin ID lar (vergul bilan ajratilgan)

## 🚀 Ishga tushirish

```bash
python main.py
```

## 📁 Fayllar Tuzilishi

```
.
├── main.py              # Asosiy bot
├── ai_mentor_work.py    # AI Mentor moduli
├── database.py          # Ma'lumotlar bazasi
├── config.py            # Konfiguratsiya
├── voice_engine.py      # Ovoz (TTS/STT)
├── progress.py          # XP va progress
├── settings.py          # Foydalanuvchi sozlamalari
├── admin.py             # Admin panel
├── requirements.txt     # Kutubxonalar
└── materials/           # Materiallar papkasi
    ├── sayfa/
    └── kitob/
```

## 🛠️ Admin Panel

Adminlar quyidagilarni qo'shishlari mumkin:
- 📖 Lug'at kitoblari (JSON fayl orqali)
- 📚 Sayfa materiallari (PDF + Audio)
- 📚 Kitob materiallari (PDF, Audio, Video)

## 📝 Litsenziya

MIT License

## 👨‍💻 Muallif

Sardor Sherqobilov

---

*Deutsch Meister PRO - Nemis tilini o'rganishning eng yaxshi yo'li!*
