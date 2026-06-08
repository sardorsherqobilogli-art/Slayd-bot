#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deutsch Booster - Telegram Bot
python-telegram-bot v20+
Railway: BOT_TOKEN environment variable kerak
"""

import logging
import os
import random
import datetime
import json
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ==================== KONFIGURATSIYA ====================
TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== STATES ====================
(
    MAIN_MENU,
    LEVEL_SELECT,
    A1_MENU, A2_MENU, B1_MENU, B2_MENU, C1_MENU,
    BOOK_MENU,
    LEKTION_PAGE,
    TRANSLATOR,
    QUIZ_STATE,
    POMODORO_STATE,
    UZB_DEU_INPUT,
    DEU_UZB_INPUT,
) = range(14)

# ==================== CALLBACKS ====================
class CB:
    MAIN_MENU     = "main_menu"
    LEVEL_SELECT  = "level_select"
    LEVEL_A1      = "level_a1"
    LEVEL_A2      = "level_a2"
    LEVEL_B1      = "level_b1"
    LEVEL_B2      = "level_b2"
    LEVEL_C1      = "level_c1"
    B1_PREP       = "b1_prep"
    B2_PREP       = "b2_prep"
    C1_PREP       = "c1_prep"
    TRANSLATOR    = "translator"
    UZB_DEU       = "uzb_deu"
    DEU_UZB       = "deu_uzb"
    TRANSLATOR_AGAIN = "translator_again"
    HELP          = "help"
    QUIZ_KNOW     = "quiz_know"
    QUIZ_DONTKNOW = "quiz_dontknow"
    QUIZ_REPEAT   = "quiz_repeat"
    POMODORO_25   = "pomodoro_25"
    POMODORO_STOP = "pomodoro_stop"


# ==================== LEKTION RANGE CONFIG ====================
BOOK_LEKTIONS = {
    "a1_motive":   (1, 8),
    "a1_schritte": (1, 14),
    "a1_menschen": (1, 24),

    "a2_motive":   (9, 18),
    "a2_schritte": (1, 14),
    "a2_menschen": (1, 24),

    "b1_motive":   (19, 30),
    "b1_schritte": (1, 14),
    "b1_menschen": (1, 24),

    "b2_sicher":      (1, 12),
    "b2_kompassdaf":  (1, 10),
    "b2_aspekte":     (1, 10),

    "c1_sicher":      (1, 12),
    "c1_kompassdaf":  (1, 10),
    "c1_aspekte":     (1, 10),
}

BOOK_LABELS = {
    "motive":     "📗 MOTIVE",
    "schritte":   "📙 SCHRITTE",
    "menschen":   "📕 MENSCHEN",
    "sicher":     "📗 Sicher",
    "kompassdaf": "📙 KompassDaF",
    "aspekte":    "📕 Aspekte",
}

LEVEL_BOOKS = {
    "a1": ["motive", "schritte", "menschen"],
    "a2": ["motive", "schritte", "menschen"],
    "b1": ["motive", "schritte", "menschen"],
    "b2": ["sicher", "kompassdaf", "aspekte"],
    "c1": ["sicher", "kompassdaf", "aspekte"],
}

LEVEL_LABELS = {
    "a1": "🟢 A1 \\- Beginner",
    "a2": "🟢 A2 \\- Elementary",
    "b1": "🟡 B1 \\- Intermediate",
    "b2": "🟡 B2 \\- Upper\\-Intermediate",
    "c1": "🔴 C1 \\- Advanced",
}


# ==================== A1 MOTIVE LUGATLARI ====================

A1_MOTIVE_LEKTIONS = {
    1: r"""🇩🇪 *A1 • MOTIVE • Lektion 1*

🔸 der Buchstabe \- harf
🔹 das Wiedersehen \- ko'rishguncha
🔸 buchstabieren \- harflab aytmoq
🔹 willkommen \- xush kelibsiz
🔸 Auf Wiedersehen \- xayr
🔹 der Automat \- avtomat
🔸 das Baby \- chaqaloq
🔹 die Banane \- banan
🔸 der Computer \- kompyuter
🔹 der Film \- film
🔸 das Foto \- fotosurat
🔹 der Geldautomat \- bankomat
🔸 das Hotel \- mehmonxona
🔹 das Internet \- internet
🔸 der Kaffee \- qahva
🔹 das Museum \- muzey
🔸 die Post \- pochta
🔹 das Radio \- radio
🔸 die SMS \- sms
🔹 das Taxi \- taksi
🔸 das Telefon \- telefon
🔹 die Universität \- universitet
🔸 das Wort \- so'z
🔹 deutsch \- nemischa
🔸 international \- xalqaro
🔹 das Beispiel \- misol
🔸 die Entscheidung \- qaror
🔹 der Familienname \- familiya
🔸 die Frau \- ayol
🔹 der Herr \- janob
🔸 der Name \- ism
🔹 die Person \- shaxs
🔸 der Teil \- qism
🔹 der Vorname \- ism
🔸 heißen \- nomlanmoq
🔹 lesen \- o'qimoq
🔸 du \- sen
🔹 Sie \- siz
🔸 wie \- qanday
🔹 das Handy \- telefon
🔸 neu \- yangi
🔹 falsch \- noto'g'ri
🔸 richtig \- to'g'ri
🔹 wichtig \- muhim
🔸 acht \- sakkiz
🔹 bitte \- iltimos
🔸 dann \- keyin
🔹 drei \- uch
🔸 eins \- bir
🔹 fünf \- besh
🔸 nein \- yo'q
🔹 neun \- to'qqiz
🔸 sechs \- olti
🔹 sieben \- yetti
🔸 vier \- to'rt
🔹 von \- dan
🔸 zwei \- ikki
🔹 zehn \- o'n
🔸 zwölf \- o'n ikki
🔹 das Café \- kafe
🔸 Deutschland \- Germaniya
🔹 die Uhr \- soat
🔸 kommen \- kelmoq
🔹 vergleichen \- solishtirmoq
🔸 auch \- ham
🔹 aus \- dan
🔸 ihr \- sizlar
🔹 in \- ichida
🔸 nicht \- emas
🔹 sie \- ular
🔸 wir \- biz
🔹 der Abend \- kech
🔸 die Frage \- savol
🔹 der Mittag \- peshin
🔸 der Morgen \- ertalab
🔹 der Nachmittag \- tushdan keyin
🔸 die Nacht \- tun
🔹 der Vormittag \- tushgacha
🔸 spät \- kech
🔹 elf \- o'n bir
🔸 es \- u neutrum
🔹 das Bild \- rasm
🔸 der Dienstag \- seshanba
🔹 der Montag \- dushanba
🔸 die Tabelle \- jadval
🔹 glauben \- ishonmoq
🔸 haben \- ega bo'lmoq
🔹 sein \- bo'lmoq
🔸 frei \- bo'sh
🔹 aber \- lekin
🔸 am \- da
🔹 am Morgen \- ertalab
🔸 da \- u yerda
🔹 dort \- u yerda
🔸 in der Nacht \- tunda
🔹 morgen \- ertaga
🔸 oder \- yoki
🔹 wann \- qachon
🔸 wo \- qayerda
🔹 der Donnerstag \- payshanba
🔸 der Freitag \- juma
🔹 der Mittwoch \- chorshanba
🔸 der Samstag \- shanba
🔹 der Sonntag \- yakshanba
🔸 der Wochentag \- hafta kuni
🔹 antworten \- javob bermoq
🔸 fragen \- so'ramoq
🔹 heute \- bugun
🔸 was \- nima
🔹 ja \- ha
🔸 der Bleistift \- qalam
🔹 das Buch \- kitob
🔸 die CD \- disk
🔹 das Fenster \- deraza
🔸 das Heft \- daftarcha
🔹 der Kugelschreiber \- ruchka
🔸 die Lampe \- chiroq
🔹 die Nummer \- raqam
🔸 das Papier \- qog'oz
🔹 der Stuhl \- stul
🔸 der Tisch \- stol
🔹 man \- odam
🔸 schreiben \- yozmoq
🔹 denn \- chunki
🔸 ein \- bir
🔹 das Auto \- avtomobil
🔸 der Bus \- avtobus
🔹 der Hamburger \- gamburger
🔸 die Pizza \- pizza
🔹 die Polizei \- politsiya
🔸 der Satz \- gap
🔹 die Seite \- sahifa
🔸 das WC \- hojatxona
🔹 kennen \- bilmoq
🔸 doch \- baribir
🔹 kein \- hech qanday""",

    2: r"""🇩🇪 *A1 • MOTIVE • Lektion 2*

🔸 das Ausland \- chet el
🔹 der/die Bekannte \- tanish
🔸 die E\-Mail \- elektron pochta
🔹 der Tag \- kun
🔸 telefonieren \- telefonlashmoq
🔹 gut \- yaxshi
🔸 jetzt \- hozir
🔹 sehr \- juda
🔸 die Antwort \- javob
🔹 die Familie \- oila
🔸 die Musik \- musiqa
🔹 der Punkt \- nuqta
🔸 das Quiz \- viktorina
🔹 der Schauspieler \- aktyor
🔸 finden \- topmoq
🔹 spielen \- o'ynamoq
🔸 surfen \- internetda kezmoq
🔹 Tennis spielen \- tennis o'ynamoq
🔸 wandern \- sayr qilmoq
🔹 schön \- chiroyli
🔸 für \- uchun
🔹 gern \- yoqtirib
🔸 Lieblings\- \- sevimli
🔹 die Sprache \- til
🔸 arbeiten \- ishlamoq
🔹 kochen \- ovqat pishirmoq
🔸 lernen \- o'rganmoq
🔹 machen \- qilmoq
🔸 schwimmen \- suzmoq
🔹 tanzen \- raqs tushmoq
🔸 das Fernsehen \- televideniye
🔹 der Fußball \- futbol
🔸 der Jazz \- jazz
🔹 die Mathematik \- matematika
🔸 Österreich \- Avstriya
🔹 interessant \- qiziqarli
🔸 langweilig \- zerikarli
🔹 schrecklich \- dahshatli
🔸 toll \- ajoyib
🔹 das Land \- mamlakat
🔸 die Schauspielerin \- aktrisa
🔹 der Sportler \- sportchi
🔸 die Stadt \- shahar
🔹 die Zahl \- son
🔸 meinen \- o'ylamoq
🔹 dein \- sening
🔸 Ihr \- sizning
🔹 wie bitte \- uzr, nima dedingiz?""",

    3: r"""🇩🇪 *A1 • MOTIVE • Lektion 3*

🔸 der Beruf \- kasb
🔹 der Bruder \- aka, uka
🔸 die Eltern \- ota\-ona
🔹 die Frau \- ayol
🔸 der Freund \- do'st
🔹 die Geschwister \- aka\-uka, opa\-singil
🔸 das Kind \- bola
🔹 der Cousin \- amakivachcha o'g'il
🔸 die Cousine \- amakivachcha qiz
🔹 die Großeltern \- bobo va buvi
🔸 die Großmutter \- buvi
🔹 der Großvater \- bobo
🔸 die Mutter \- ona
🔹 die Oma \- buvi
🔸 der Onkel \- amaki, tog'a
🔹 der Opa \- bobo
🔸 die Tante \- xola, amma
🔹 der Vater \- ota
🔸 ihr \- ularning
🔹 das Leben \- hayot
🔸 die Liebe \- sevgi
🔹 der Mann \- erkak
🔸 der Partner \- sherik
🔹 die Schwester \- opa, singil
🔸 der Sohn \- o'g'il
🔹 das Thema \- mavzu
🔸 die Tochter \- qiz farzand
🔹 leben \- yashamoq
🔸 lieben \- sevmoq
🔹 sagen \- aytmoq
🔸 wohnen \- yashamoq
🔹 allein \- yolg'iz
🔸 einfach \- oddiy
🔹 geschieden \- ajrashgan
🔸 groß \- katta
🔹 klein \- kichik
🔸 verheiratet \- turmush qurgan
🔹 als \- sifatida
🔸 immer \- har doim
🔹 noch \- hali ham
🔸 sein \- uning
🔹 viel \- ko'p
🔸 wie viele \- nechta?""",

    4: r"""🇩🇪 *A1 • MOTIVE • Lektion 4*

🔸 die Arbeit \- ish
🔹 der Arzt \- shifokor erkak
🔸 die Ärztin \- shifokor ayol
🔹 das Essen \- ovqat
🔸 die Form \- shakl
🔹 Frankreich \- Fransiya
🔸 der Friseur \- sartarosh erkak
🔹 die Friseurin \- sartarosh ayol
🔸 Griechenland \- Gretsiya
🔹 Großbritannien \- Buyuk Britaniya
🔸 das Heim \- uy
🔹 der Ingenieur \- muhandis erkak
🔸 die Ingenieurin \- muhandis ayol
🔹 Italien \- Italiya
🔸 das Jahr \- yil
🔹 der Job \- ish
🔸 die Kabine \- kabina
🔹 der Kellner \- ofitsiant erkak
🔸 die Kellnerin \- ofitsiant ayol
🔹 der Koch \- oshpaz erkak
🔸 die Köchin \- oshpaz ayol
🔹 der Krankenpfleger \- hamshira erkak
🔸 die Krankenschwester \- hamshira ayol
🔹 die Liste \- ro'yxat
🔸 der Manager \- menejer
🔹 die Managerin \- menejer ayol
🔸 das Meer \- dengiz
🔹 der Musiker \- musiqachi erkak
🔸 die Musikerin \- musiqachi ayol
🔹 Rumänien \- Ruminiya
🔸 das Schiff \- kema
🔹 die Sonne \- quyosh
🔸 Spanien \- Ispaniya
🔹 der Steward \- bort kuzatuvchisi erkak
🔸 die Stewardess \- bort kuzatuvchisi ayol
🔹 die Stunde \- soat
🔸 das Team \- jamoa
🔹 die Türkei \- Turkiya
🔸 die Ukraine \- Ukraina
🔹 die Woche \- hafta
🔸 alt \- eski
🔹 männlich \- erkak jinsli
🔸 schlecht \- yomon
🔹 weiblich \- ayol jinsli
🔸 auf \- ustida
🔹 geboren \- tug'ilgan
🔸 manchmal \- ba'zan
🔹 schon \- allaqachon
🔸 dreizehn \- o'n uch
🔹 hundert \- yuz
🔸 zwanzig \- yigirma
🔹 das Alter \- yosh
🔸 Schweden \- Shvetsiya
🔹 der Tourist \- sayyoh erkak
🔸 die Touristin \- sayyoh ayol
🔹 selbstständig \- mustaqil""",

    5: r"""🇩🇪 *A1 • MOTIVE • Lektion 5*

🔸 die Kommunikation \- kommunikatsiya
🔹 der Konsum \- iste'mol
🔸 das Lebensmittel \- oziq\-ovqat
🔹 das Restaurant \- restoran
🔸 der Sport \- sport
🔹 der Urlaub \- ta'til
🔸 die Ferien \- ta'til
🔹 die Wohnung \- kvartira
🔸 chatten \- chatlashmoq
🔹 fahren \- haydamoq
🔸 etwas \- nimadir
🔹 nichts \- hech narsa
🔸 so \- shunday
🔹 zweimal \- ikki marta
🔸 die Blume \- gul
🔹 die Briefmarke \- marka
🔸 das Fahrrad/das Velo \- velosiped
🔹 der Fernseher \- televizor
🔸 die Hose \- shim
🔹 der Kühlschrank \- muzlatkich
🔸 der Schrank \- shkaf
🔹 das Spiel \- o'yin
🔸 mehr \- ko'proq
🔹 der Cent \- sent
🔸 der Euro \- yevro
🔹 der Preis \- narx
🔸 billig \- arzon
🔹 teuer \- qimmat
🔸 nur \- faqat
🔹 wie viel \- qancha
🔸 der Apfel \- olma
🔹 die Birne \- nok
🔸 das Brot \- non
🔹 das Brötchen \- bulochka
🔸 die Butter \- sariyog'
🔹 die Cola \- kola
🔸 das Ei \- tuxum
🔹 das Eis \- muzqaymoq
🔸 der Fisch \- baliq
🔹 das Fleisch \- go'sht
🔸 das Joghurt \- yogurt
🔹 die Karotte \- sabzi
🔸 die Kartoffel \- kartoshka
🔹 der Käse \- pishloq
🔸 die Milch \- sut
🔹 die Nudel \- makaron
🔸 die Orange \- apelsin
🔹 der Reis \- guruch
🔸 der Salat \- salat
🔹 der Tee \- choy
🔸 die Tomate \- pomidor
🔹 die Wurst \- kolbasa
🔸 leer \- bo'sh
🔹 der Supermarkt \- supermarket
🔸 mögen \- yoqtirmoq
🔹 schmecken \- ta'mi yoqmoq
🔸 trinken \- ichmoq
🔹 nie \- hech qachon
🔸 der Appetit \- ishtaha
🔹 das Frühstück \- nonushta
🔸 das Gemüse \- sabzavot
🔹 der Hunger \- ochlik
🔸 die Kantine \- oshxona
🔹 der Kuchen \- pirog
🔸 die Pommes frites \- kartoshka fri
🔹 die Sahne \- qaymoq
🔸 einkaufen \- xarid qilmoq
🔹 geöffnet \- ochiq
🔸 geschlossen \- yopiq
🔹 halb \- yarmi
🔸 wenig \- oz
🔹 mit \- bilan
🔸 nach \- keyin
🔹 um \- da vaqtda
🔸 vor \- oldin
🔹 zu Mittag \- tushlik vaqtida
🔸 nehmen \- olmoq
🔹 treffen \- uchrashmoq
🔸 leider \- afsuski
🔹 meistens \- ko'pincha
🔸 vielleicht \- balki
🔹 zusammen \- birga""",

    6: r"""🇩🇪 *A1 • MOTIVE • Lektion 6*

🔸 der Alltag \- kundalik hayot
🔹 das Büro \- ofis
🔸 die Freizeit \- bo'sh vaqt
🔹 der Künstler \- rassom, san'atkor
🔸 der Kurs \- kurs
🔹 das Lied \- qo'shiq
🔸 der Student \- talaba
🔹 das Studium \- o'qish universitetda
🔸 frühstücken \- nonushta qilmoq
🔹 hören \- eshitmoq
🔸 studieren \- o'qimoq
🔹 verkaufen \- sotmoq
🔸 verlieren \- yo'qotmoq
🔹 verstehen \- tushunmoq
🔸 warten \- kutmoq
🔹 allmählich \- asta\-sekin
🔸 manche \- ba'zi
🔹 sicher \- ishonchli
🔸 virtuell \- virtual
🔹 niemand \- hech kim
🔸 schnell \- tez
🔹 die Bank \- bank
🔸 der Fan \- muxlis
🔹 das Gefühl \- his
🔸 das Interview \- intervyu
🔹 der Journalist \- jurnalist
🔸 der Spaß \- zavq
🔹 der Trainer \- murabbiy
🔸 das Training \- mashg'ulot
🔹 ankommen \- yetib kelmoq
🔸 anrufen \- qo'ng'iroq qilmoq
🔹 anziehen \- kiymoq
🔸 aussehen \- ko'rinmoq
🔹 mitmachen \- qatnashmoq
🔸 durstig \- chanqoq
🔹 hungrig \- och
🔸 lustig \- qiziqarli
🔹 müde \- charchagan
🔸 nervös \- asabiy
🔹 traurig \- qayg'uli
🔸 wütend \- g'azablangan
🔹 zufrieden \- mamnun
🔸 genug \- yetarli
🔹 wieder \- yana
🔸 die Hausaufgabe \- uy vazifasi
🔹 das Konzert \- konsert
🔸 aufmachen \- ochmoq
🔹 kennenlernen \- tanishmoq
🔸 mieten \- ijaraga olmoq
🔹 reisen \- sayohat qilmoq
🔸 suchen \- qidirmoq
🔹 verdienen \- topmoq
🔸 wollen \- xohlamoq
🔹 ganz \- butunlay
🔸 normal \- normal
🔹 sogar \- hattoki
🔸 die Firma \- firma
🔹 die Stelle \- ish joyi
🔸 aufhören \- to'xtatmoq
🔹 dürfen \- ruxsat bo'lmoq
🔸 grillen \- grilda pishirmoq
🔹 mitbringen \- olib kelmoq
🔸 rauchen \- chekish
🔹 fit \- baquvvat
🔸 laut \- baland ovozli""",

    7: r"""🇩🇪 *A1 • MOTIVE • Lektion 7*

🔸 einladen \- taklif qilmoq
🔹 die Ampel \- svetofor
🔸 die Apotheke \- dorixona
🔹 der Dieb \- o'g'ri
🔸 der Experte \- ekspert
🔹 die Freiheit \- erkinlik
🔸 die Kontrolle \- nazorat
🔹 der Polizist \- politsiyachi
🔸 die Straße \- ko'cha
🔹 der Weg \- yo'l
🔸 das Ziel \- maqsad, manzil
🔹 ausgehen \- tashqariga chiqmoq
🔸 gehen \- yurmoq, ketmoq
🔹 beschreiben \- tasvirlamoq
🔸 einschalten \- yoqmoq
🔹 geben \- bermoq
🔸 holen \- olib kelmoq
🔹 kontrollieren \- tekshirmoq
🔸 mitnehmen \- o'zi bilan olib ketmoq
🔹 stehen \- turmoq
🔸 tragen \- kiyib yurmoq
🔹 wissen \- bilmoq
🔸 zeigen \- ko'rsatmoq
🔹 zuhören \- tinglamoq
🔸 blind \- ko'r
🔹 grün \- yashil
🔸 links \- chap
🔹 rechts \- o'ng
🔸 bald \- tez orada
🔹 geradeaus \- to'g'ri
🔸 hinter \- orqasida
🔹 neben \- yonida
🔸 vor \- oldida
🔹 warum \- nega
🔸 weg \- uzoq
🔹 zuerst \- avval
🔸 der Bahnhof \- vokzal
🔹 die Bar \- bar
🔸 die Disco \- diskoteka
🔹 die Fabrik \- fabrika
🔸 der Flughafen \- aeroport
🔹 das Geschäft \- do'kon
🔸 die Haltestelle \- bekat
🔹 das Kino \- kino
🔸 das Krankenhaus \- shifoxona
🔹 der Park \- park
🔸 der Parkplatz \- avtoturargoh
🔹 das Schwimmbad \- suzish havzasi
🔸 der Plan \- reja
🔹 fremd \- begona
🔸 die Badewanne \- vanna
🔹 das Bett \- karavot
🔸 die Dusche \- dush
🔹 der Flur \- koridor
🔸 der Herd \- gaz plitasi
🔹 die Küche \- oshxona
🔸 das Regal \- javon
🔹 der Sessel \- kreslo
🔸 das Sofa \- divan
🔹 der Teppich \- gilam
🔸 die Toilette \- hojatxona
🔹 das Waschbecken \- rakovina
🔸 die Waschmaschine \- kir yuvish mashinasi
🔹 das Wohnzimmer \- yashash xonasi
🔸 das Zimmer \- xona
🔹 zurück \- orqaga
🔸 der Boden \- pol
🔹 die Brille \- ko'zoynak
🔸 die Ecke \- burchak
🔹 der Pass \- pasport
🔸 der Schlüssel \- kalit
🔹 die Tür \- eshik
🔸 die Wand \- devor
🔹 hängen \- osmoq
🔸 liegen \- yotmoq
🔹 an \- da/ustida
🔸 über \- ustida
🔹 unter \- tagida
🔸 zwischen \- orasida""",

    8: r"""🇩🇪 *A1 • MOTIVE • Lektion 8*

🔸 der Einwohner \- aholi
🔹 der Fluss \- daryo
🔸 die Insel \- orol
🔹 das Rathaus \- shahar hokimiyati
🔸 der See \- ko'l
🔹 die Sehenswürdigkeit \- diqqatga sazovor joy
🔸 der Balkon \- balkon
🔹 die Brücke \- ko'prik
🔸 der Gruß \- salom
🔹 das Kaufhaus \- universal do'kon
🔸 das Zentrum \- markaz
🔹 denken \- o'ylamoq
🔸 direkt \- to'g'ridan\-to'g'ri
🔹 lieb \- yoqimli
🔸 besonders \- ayniqsa
🔹 die Bibliothek \- kutubxona
🔸 der Einkauf \- xarid
🔹 der Sänger \- qo'shiqchi
🔸 das Theater \- teatr
🔹 die U\-Bahn \- metro
🔸 fein \- nafis
🔹 nachts \- tunda
🔸 das Fundbüro \- yo'qolgan narsalar byurosi
🔹 der Kursleiter \- kurs rahbari
🔸 der Mechaniker \- mexanik
🔹 ander \- boshqa
🔸 kaputt \- buzilgan
🔹 überall \- hamma joyda
🔸 der Doktor \- doktor
🔹 das Fieber \- isitma
🔸 der Grad \- daraja
🔹 der Kollege \- hamkasb
🔸 die Kollegin \- hamkasb ayol
🔹 der Schmerz \- og'riq
🔸 der Zahn \- tish
🔹 krank \- kasal
🔸 der April \- aprel
🔹 der August \- avgust
🔸 der Dezember \- dekabr
🔹 der Februar \- fevral
🔸 das Gespräch \- suhbat
🔹 der Januar \- yanvar
🔸 der Juni \- iyun
🔹 der Juli \- iyul
🔸 der Mai \- may
🔹 der März \- mart
🔸 der Monat \- oy
🔹 der November \- noyabr
🔸 der Oktober \- oktyabr
🔹 der September \- sentabr
🔸 wiederholen \- takrorlamoq
🔹 früher \- oldin
🔸 später \- keyin
🔹 besser \- yaxshiroq
🔸 hoffentlich \- umid qilamanki
🔹 natürlich \- albatta
🔸 unbedingt \- shubhasiz
🔹 das Bier \- pivo
🔸 die Flasche \- shisha
🔹 die Gesundheit \- sog'liq
🔸 der Vorschlag \- taklif
🔹 der Wein \- vino
🔸 lachen \- kulmoq
🔹 schlafen \- uxlamoq
🔸 gesund \- sog'lom
🔹 lang \- uzun
🔸 modern \- zamonaviy
🔹 verschieden \- turli
🔸 weiß \- oq
🔹 jeder \- har biri
🔸 seit \- dan beri
🔹 das Auge \- ko'z
🔸 der Bauch \- qorin
🔹 das Bein \- oyoq
🔸 die Brust \- ko'krak
🔹 der Finger \- barmoq
🔸 der Fuß \- oyoq kafti
🔹 das Gesicht \- yuz
🔸 der Hals \- bo'yin
🔹 die Hand \- qo'l
🔸 der Kopf \- bosh
🔹 der Körper \- tana
🔸 der Mund \- og'iz
🔹 die Nase \- burun
🔸 das Ohr \- quloq
🔹 der Rücken \- bel
🔸 das Tier \- hayvon
🔹 die Farbe \- rang
🔸 der Frühling \- bahor
🔹 der Herbst \- kuz
🔸 die Kleidung \- kiyim
🔹 der Sommer \- yoz
🔸 der Winter \- qish
🔹 kalt \- sovuq
🔸 beide \- ikkala
🔹 deshalb \- shuning uchun
🔸 übrigens \- aytgancha
🔹 blau \- ko'k
🔸 braun \- jigar rang
🔹 gelb \- sariq
🔸 grau \- kulrang
🔹 lila \- binafsha
🔸 orange \- to'q sariq
🔹 rosa \- pushti
🔸 schwarz \- qora
🔹 violett \- siyoh rang
🔸 der Ausweis \- guvohnoma
🔹 die Brieftasche \- hamyon
🔸 die Kreditkarte \- kredit karta
🔹 langsam \- sekin
🔸 gestern \- kecha
🔹 die Tasche \- sumka
🔸 der Brief \- xat
🔹 die Einladung \- taklifnoma
🔸 die Fahrkarte \- yo'l chiptasi
🔹 der Führerschein \- haydovchilik guvohnomasi
🔸 das Fest \- bayram
🔹 das Geschenk \- sovg'a
🔸 der Zucker \- shakar
🔹 fertig \- tayyor
🔸 bitter \- achchiq
🔹 schlimm \- yomon
🔸 der Flug \- parvoz
🔹 die Reise \- sayohat
🔸 der Krimi \- detektiv
🔹 die Kunst \- san'at
🔸 die Mode \- moda
🔹 die Politik \- siyosat
🔸 erzählen \- hikoya qilmoq
🔹 die Diskussion \- muhokama
🔸 die Meinung \- fikr
🔹 die Pause \- tanaffus
🔸 die Regel \- qoida
🔹 die Zeitung \- gazeta
🔸 erlauben \- ruxsat bermoq
🔹 fernsehen \- televizor ko'rmoq
🔸 verboten \- taqiqlangan
🔹 das Glück \- baxt
🔸 das Verbot \- taqiq
🔹 erlaubt \- ruxsat etilgan
🔸 der Fasching \- karnaval
🔹 der Hut \- shlyapa
🔸 also \- demak
🔹 anders \- boshqacha
🔸 bis \- gacha
🔹 ein paar \- bir necha
🔸 das Neujahr \- Yangi yil
🔹 das Silvester \- Yangi yil arafasi
🔸 das Sonderangebot \- maxsus taklif
🔹 das Weihnachten \- Rojdestvo
🔸 gefallen \- yoqmoq
🔹 gehören \- tegishli bo'lmoq
🔸 das Hemd \- ko'ylak
🔹 die Jacke \- kurtka
🔸 die Jeans \- jinsi shim
🔹 das Kleid \- ko'ylak
🔸 der Mantel \- palto
🔹 der Pullover \- jemper
🔸 der Schuh \- tufli
🔹 das T\-Shirt \- futbolka
🔸 kurz \- qisqa
🔹 das Hobby \- sevimli mashg'ulot
🔸 welch \- qaysi
🔹 der Rucksack \- ryukzak
🔸 laufen \- yugurmoq
🔹 schenken \- sovg'a qilmoq
🔸 sitzen \- o'tirmoq
🔹 danken \- minnatdorlik bildirmoq
🔸 öffnen \- ochmoq
🔹 sollen \- kerak bo'lmoq
🔸 freundlich \- do'stona
🔹 gemeinsam \- birgalikda
🔸 die Hilfe \- yordam
🔹 der Baum \- daraxt
🔸 halten \- ushlamoq
🔹 speichern \- saqlamoq
🔸 die Kamera \- kamera
🔹 ab \- dan boshlab""",
}

# Boshqa kitoblar uchun placeholder — keyinchalik to'ldirish mumkin
def get_lektion_text(level: str, book: str, n: int) -> str:
    """Lektion matnini qaytaradi"""
    if level == "a1" and book == "motive":
        text = A1_MOTIVE_LEKTIONS.get(n)
        if text:
            return text

    # Boshqa barcha lektion va kitoblar uchun
    label = BOOK_LABELS[book]
    level_label = LEVEL_LABELS[level]
    return (
        f"{level_label} \\| {label}\n"
        f"📖 *Lektion {n}*\n\n"
        "⏳ Bu lektion materiallari tez orada qo'shiladi\\!\n\n"
        "📌 Hozircha A1 Motive lektsiyalari to'liq mavjud\\."
    )


def parse_words(level: str, book: str, n: int) -> list:
    """Lug'at matnidan (german, uzbek) juftliklarini oladi"""
    if level == "a1" and book == "motive":
        raw = A1_MOTIVE_LEKTIONS.get(n, "")
    else:
        return []

    words = []
    for line in raw.split("\n"):
        line = line.strip()
        # Emoji va backslash larni tozalash
        for emoji in ["🔸", "🔹"]:
            line = line.replace(emoji, "").strip()
        # "der Buchstabe \- harf" shaklini ajratamiz
        if " \\- " in line:
            parts = line.split(" \\- ", 1)
            if len(parts) == 2:
                german = parts[0].strip()
                uzbek = parts[1].strip()
                if german and uzbek:
                    words.append((german, uzbek))
    return words


# ==================== QUIZ HELPERS ====================

def get_quiz_state(context) -> dict:
    return context.user_data.get("quiz", {})

def set_quiz_state(context, data: dict):
    context.user_data["quiz"] = data

def quiz_card_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Bildim", callback_data=CB.QUIZ_KNOW),
            InlineKeyboardButton("❌ Bilmadim", callback_data=CB.QUIZ_DONTKNOW),
        ],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])

def quiz_result_keyboard(level: str, book: str, n: int, has_wrong: bool):
    rows = []
    if has_wrong:
        rows.append([InlineKeyboardButton(
            "🔁 Bilmaganlarni takrorlash", callback_data=CB.QUIZ_REPEAT
        )])
    rows.append([InlineKeyboardButton(
        "↩️ Lektsiyaga qaytish",
        callback_data=f"lekt_{level}_{book}_{n}"
    )])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


async def show_quiz_card(query, context):
    """Navbatdagi flashcard kartani ko'rsatadi"""
    q = get_quiz_state(context)
    words = q["words"]
    idx = q["index"]

    if idx >= len(words):
        # Test tugadi
        wrong = q["wrong"]
        total = q["total"]
        correct = total - len(wrong)

        level = q["level"]
        book  = q["book"]
        n     = q["n"]

        def esc_result(s):
            for ch in r"\_*[]()~`>#+-=|{}.!":
                s = s.replace(ch, f"\\{ch}")
            return s

        wrong_text = ""
        if wrong:
            wrong_lines = "\n".join([f"• {esc_result(g)} — {esc_result(u)}" for g, u in wrong])
            wrong_text = f"\n\n❌ *Bilmaganlar:*\n{wrong_lines}"

        text = (
            f"🏁 *Test tugadi\\!*\n\n"
            f"✅ Bildim: {correct}/{total}\n"
            f"❌ Bilmadim: {len(wrong)}/{total}"
            + wrong_text
        )
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=quiz_result_keyboard(level, book, n, bool(wrong))
        )
        return QUIZ_STATE

    german, uzbek = words[idx]
    total = q["total"]
    # MarkdownV2 uchun xavfli belgilarni escape qilamiz
    def esc(s):
        for ch in r"\_*[]()~`>#+-=|{}.!":
            s = s.replace(ch, f"\\{ch}")
        return s

    text = (
        f"🧠 *Yodlash testi* \\— {idx+1}/{total}\n\n"
        f"🇩🇪 *{esc(german)}*\n\n"
        f"O'zbekcha tarjimasi qanday?"
    )
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=quiz_card_keyboard()
    )
    return QUIZ_STATE


async def quiz_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """quiz_start_{level}_{book}_{n} callback"""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    # quiz_start_a1_motive_1 → ['quiz','start','a1','motive','1']
    level = parts[2]
    n     = int(parts[-1])
    book  = "_".join(parts[3:-1])

    words = parse_words(level, book, n)
    if not words:
        await query.edit_message_text(
            "⏳ Bu lektion uchun test hali mavjud emas\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_to_main_keyboard()
        )
        return BOOK_MENU

    random.shuffle(words)

    set_quiz_state(context, {
        "words": words,
        "index": 0,
        "wrong": [],
        "total": len(words),
        "level": level,
        "book": book,
        "n": n,
    })
    return await show_quiz_card(query, context)


async def quiz_know_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer("✅ Zo'r!")
    q = get_quiz_state(context)
    q["index"] += 1
    set_quiz_state(context, q)
    return await show_quiz_card(query, context)


async def quiz_dontknow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    q = get_quiz_state(context)
    words = q["words"]
    idx = q["index"]
    # Javobni ko'rsatamiz
    german, uzbek = words[idx]

    def esc(s):
        for ch in r"\_*[]()~`>#+-=|{}.!":
            s = s.replace(ch, f"\\{ch}")
        return s

    await query.answer(f"❌ {uzbek}", show_alert=True)
    q["wrong"].append((german, uzbek))
    q["index"] += 1
    set_quiz_state(context, q)
    return await show_quiz_card(query, context)


async def quiz_repeat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bilmaganlarni qayta boshlash"""
    query = update.callback_query
    await query.answer()
    q = get_quiz_state(context)
    wrong = q["wrong"]

    random.shuffle(wrong)

    set_quiz_state(context, {
        "words": wrong,
        "index": 0,
        "wrong": [],
        "total": len(wrong),
        "level": q["level"],
        "book":  q["book"],
        "n":     q["n"],
    })
    return await show_quiz_card(query, context)


# ==================== POMODORO ====================

async def pomodoro_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """pomodoro_start_{level}_{book}_{n}"""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    level = parts[2]
    n     = int(parts[-1])
    book  = "_".join(parts[3:-1])

    end_time = datetime.datetime.now() + datetime.timedelta(minutes=25)
    end_str  = end_time.strftime("%H:%M")

    context.user_data["pomodoro"] = {
        "level": level, "book": book, "n": n, "end": end_str
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏹ To'xtatish", callback_data=CB.POMODORO_STOP)],
        [InlineKeyboardButton(
            "↩️ Lektsiyaga qaytish",
            callback_data=f"lekt_{level}_{book}_{n}"
        )],
    ])

    await query.edit_message_text(
        f"🍅 *Pomodoro boshlandi\\!*\n\n"
        f"⏱ 25 daqiqa o'qish vaqti\n"
        f"🏁 Tugash: *{end_str}*\n\n"
        f"Diqqatni jamlang va o'rganing\\! 💪\n"
        f"25 daqiqa o'tgach qaytib keling va To'xtatish tugmasini bosing\\.",
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    return POMODORO_STATE


async def pomodoro_stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    p = context.user_data.get("pomodoro", {})

    level = p.get("level", "a1")
    book  = p.get("book", "motive")
    n     = p.get("n", 1)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "↩️ Lektsiyaga qaytish",
            callback_data=f"lekt_{level}_{book}_{n}"
        )],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])

    await query.edit_message_text(
        "⏹ *Pomodoro to'xtatildi*\n\nYaxshi harakat\\! Davom eting 💪",
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
    return MAIN_MENU


# ==================== KEYBOARD HELPERS ====================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Daraja tanlash", callback_data=CB.LEVEL_SELECT)],
        [
            InlineKeyboardButton("📗 B1 Vorbereitung", callback_data=CB.B1_PREP),
            InlineKeyboardButton("📙 B2 Vorbereitung", callback_data=CB.B2_PREP),
        ],
        [
            InlineKeyboardButton("📕 C1 Vorbereitung", callback_data=CB.C1_PREP),
            InlineKeyboardButton("🌐 Tarjimon",         callback_data=CB.TRANSLATOR),
        ],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data=CB.HELP)],
    ])


def level_select_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 A1 - Beginner",      callback_data=CB.LEVEL_A1),
            InlineKeyboardButton("🟢 A2 - Elementary",    callback_data=CB.LEVEL_A2),
        ],
        [
            InlineKeyboardButton("🟡 B1 - Intermediate",  callback_data=CB.LEVEL_B1),
            InlineKeyboardButton("🟡 B2 - Upper-Interm.", callback_data=CB.LEVEL_B2),
        ],
        [InlineKeyboardButton("🔴 C1 - Advanced",         callback_data=CB.LEVEL_C1)],
        [InlineKeyboardButton("🏠 Asosiy menu",           callback_data=CB.MAIN_MENU)],
    ])


def books_keyboard(level: str):
    books = LEVEL_BOOKS[level]
    rows = []
    for book in books:
        rows.append([InlineKeyboardButton(
            BOOK_LABELS[book],
            callback_data=f"book_{level}_{book}"
        )])
    rows.append([InlineKeyboardButton("↩️ Darajaga qaytish", callback_data=CB.LEVEL_SELECT)])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu",      callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def lektions_keyboard(level: str, book: str):
    key = f"{level}_{book}"
    start, end = BOOK_LEKTIONS[key]
    nums = list(range(start, end + 1))

    rows = []
    for i in range(0, len(nums), 2):
        pair = nums[i:i+2]
        row = [
            InlineKeyboardButton(
                f"Lektion {n}",
                callback_data=f"lekt_{level}_{book}_{n}"
            )
            for n in pair
        ]
        rows.append(row)

    rows.append([InlineKeyboardButton(
        "↩️ Kitobga qaytish",
        callback_data=f"back_book_{level}"
    )])
    rows.append([InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def back_to_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)]
    ])


def translator_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 UZB ➡️ 🇩🇪 DEU", callback_data=CB.UZB_DEU),
            InlineKeyboardButton("🇩🇪 DEU ➡️ 🇺🇿 UZB", callback_data=CB.DEU_UZB),
        ],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])


# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "🎉 *Sprechen mit Spaß\\! Willkommen\\!* 🇩🇪\n\n"
        "Siz oddiy botga emas, nemis tilini *raketa tezligida* o'rgatuvchi shaxsiy murabbiyingiz safiga qo'shildingiz\\! 🚀\n\n"
        "✨ *Bu yerda sizni nimalar kutmoqda:*\n"
        "• Har kuni atigi 15 daqiqada yangi daraja\\! 🔥\n"
        "• Miyani charchatmaydigan intellektual Quiz testlar\\! 🧠\n"
        "• Fokusni 100% ga oshiruvchi Pomodoro taymer\\! 🍅\n\n"
        "Tayyormisiz? Maqsadni tanlang va g'alaba sari yuring\\! 👇"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="MarkdownV2",
                                        reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="MarkdownV2",
                                                      reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 *Asosiy Menu*\n\nBo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN_MENU


async def level_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📚 *Daraja tanlash*\n\nO'z darajangizni tanlang:\n"
        "🟢 A1\\-A2: Boshlang'ich\n"
        "🟡 B1\\-B2: O'rta\n"
        "🔴 C1: Yuqori",
        parse_mode="MarkdownV2",
        reply_markup=level_select_keyboard(),
    )
    return LEVEL_SELECT


async def _show_books(query, level: str):
    label = LEVEL_LABELS[level]
    await query.edit_message_text(
        f"{label}\n\nKitob tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=books_keyboard(level),
    )
    state_map = {"a1": A1_MENU, "a2": A2_MENU, "b1": B1_MENU, "b2": B2_MENU, "c1": C1_MENU}
    return state_map[level]


async def level_a1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "a1")

async def level_a2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "a2")

async def level_b1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b1")

async def level_b2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b2")

async def level_c1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "c1")

async def b1_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b1")

async def b2_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "b2")

async def c1_prep_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await _show_books(query, "c1")


async def book_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, level, book = query.data.split("_", 2)

    key = f"{level}_{book}"
    start, end = BOOK_LEKTIONS[key]
    label = BOOK_LABELS[book]
    level_label = LEVEL_LABELS[level]

    await query.edit_message_text(
        f"{level_label} \\| {label}\n\nLektion tanlang \\({start}\\-{end}\\):",
        parse_mode="MarkdownV2",
        reply_markup=lektions_keyboard(level, book),
    )
    return BOOK_MENU


async def back_book_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level = query.data.split("_")[-1]
    return await _show_books(query, level)


async def lektion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """lekt_{level}_{book}_{n} callback — haqiqiy lug'atni ko'rsatadi"""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    # lekt_a1_motive_3  → ['lekt','a1','motive','3']
    level = parts[1]
    n     = int(parts[-1])
    book  = "_".join(parts[2:-1])

    label       = BOOK_LABELS[book]
    level_label = LEVEL_LABELS[level]

    # Haqiqiy lug'at matnini olish
    content = get_lektion_text(level, book, n)

    # Agar matn allaqachon sarlavhali bo'lsa (A1 Motive), shundayligicha yuboramiz
    # Aks holda — sarlavha qo'shamiz
    if content.startswith("🇩🇪"):
        text = content
    else:
        text = f"{level_label} \\| {label}\n📖 *Lektion {n}*\n\n{content}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧠 Yodlash", callback_data=f"quiz_start_{level}_{book}_{n}"),
            InlineKeyboardButton("🍅 Pomodoro", callback_data=f"pomodoro_start_{level}_{book}_{n}"),
        ],
        [InlineKeyboardButton(
            "↩️ Lektsiyalarga qaytish",
            callback_data=f"book_{level}_{book}"
        )],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])

    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    return BOOK_MENU


# ==================== TARJIMON ====================

def build_dictionary() -> dict:
    """
    Barcha lug'atlardan ikki tomonlama qidiruv lug'atini yaratadi.
    { "de_uz": {"der buchstabe": "harf", ...},
      "uz_de": {"harf": "der Buchstabe", ...} }
    """
    de_uz = {}
    uz_de = {}
    for level in ["a1"]:
        for book in ["motive"]:
            for n in range(1, 9):
                for german, uzbek in parse_words(level, book, n):
                    de_uz[german.lower()] = (german, uzbek)
                    uz_de[uzbek.lower()] = (german, uzbek)
    return {"de_uz": de_uz, "uz_de": uz_de}

# Global lug'at — bot ishga tushganda bir marta quriladi
_DICTIONARY: dict | None = None

def get_dictionary() -> dict:
    global _DICTIONARY
    if _DICTIONARY is None:
        _DICTIONARY = build_dictionary()
    return _DICTIONARY


async def ai_translate(word: str, direction: str) -> str:
    """
    Groq API orqali tarjima qiladi (so'z va uzun gaplar uchun).
    direction: "uzb_deu" yoki "deu_uzb"
    """
    if not GROQ_API_KEY:
        return "❌ AI tarjimon sozlanmagan\\. GROQ\\_API\\_KEY kerak\\."

    # So'z yoki gap ekanini aniqlash (3 so'zdan ko'p bo'lsa — gap)
    is_sentence = len(word.strip().split()) > 3

    if direction == "uzb_deu":
        if is_sentence:
            prompt = (
                f"O'zbek tilidan nemis tiliga tarjima qil:\n\"{word}\"\n\n"
                "Faqat tarjimani yoz. "
                "To'liq, grammatik to'g'ri nemischa tarjima bo'lsin. "
                "Hech qanday izoh, qo'shimcha matn yoki tirnoq yozma."
            )
        else:
            prompt = (
                f"O'zbek tilidan nemis tiliga tarjima qil: \"{word}\"\n"
                "Faqat tarjimani yoz, grammatik artikl (der/die/das) bilan birga. "
                "Misol: \"kitob\" → \"das Buch\". "
                "Hech qanday izoh, qo'shimcha matn yozma."
            )
    else:
        if is_sentence:
            prompt = (
                f"Nemis tilidan o'zbek tiliga tarjima qil:\n\"{word}\"\n\n"
                "Faqat tarjimani yoz. "
                "To'liq, tabiiy o'zbekcha tarjima bo'lsin. "
                "Hech qanday izoh, qo'shimcha matn yoki tirnoq yozma."
            )
        else:
            prompt = (
                f"Nemis tilidan o'zbek tiliga tarjima qil: \"{word}\"\n"
                "Faqat tarjimani yoz. "
                "Misol: \"das Buch\" → \"kitob\". "
                "Hech qanday izoh, qo'shimcha matn yozma."
            )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        data = resp.json()
        result = data["choices"][0]["message"]["content"].strip()
        return result
    except Exception as e:
        logger.error(f"AI tarjima xatosi: {e}")
        return "❌ AI tarjimada xato yuz berdi\\. Qayta urinib ko'ring\\."


def esc_md(text: str) -> str:
    """MarkdownV2 uchun barcha maxsus belgilarni escape qiladi."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


async def do_translate(word: str, direction: str) -> str:
    """
    Avval lug'atdan qidiradi, topilmasa AI ga murojaat qiladi.
    Tayyor MarkdownV2 matnini qaytaradi.
    """
    d = get_dictionary()
    key = word.strip().lower()

    if direction == "uzb_deu":
        flag_from, flag_to = "🇺🇿", "🇩🇪"
        label = "O'zbekcha → Nemischa"
        hit = d["uz_de"].get(key)
    else:
        flag_from, flag_to = "🇩🇪", "🇺🇿"
        label = "Nemischa → O'zbekcha"
        hit = d["de_uz"].get(key)

    header = f"{flag_from}➡️{flag_to} *{esc_md(label)}*\n\n"
    word_line = f"📝 So'z: *{esc_md(word)}*\n\n"

    if hit:
        german, uzbek = hit
        if direction == "uzb_deu":
            result_line = f"✅ *Lug'atdan:* {esc_md(german)}"
        else:
            result_line = f"✅ *Lug'atdan:* {esc_md(uzbek)}"
        return header + word_line + result_line
    else:
        # AI dan tarjima
        ai_result = await ai_translate(word, direction)
        ai_safe = esc_md(ai_result)
        return header + word_line + f"🤖 *AI tarjima:* {ai_safe}"


async def translator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌐 *Tarjimon*\n\nQaysi yo'nalishda tarjima qilmoqchisiz?",
        parse_mode="MarkdownV2",
        reply_markup=translator_keyboard(),
    )
    return TRANSLATOR


async def uzb_deu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["translator_dir"] = "uzb_deu"
    await query.edit_message_text(
        "🇺🇿➡️🇩🇪 *O'zbekcha \\-\\> Nemischa*\n\n"
        "Menga xohlagan tarjima qilmoqchi bo'lgan so'zlarni yoki matnlarni yuboring\\! ⚡",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return UZB_DEU_INPUT


async def deu_uzb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["translator_dir"] = "deu_uzb"
    await query.edit_message_text(
        "🇩🇪➡️🇺🇿 *Nemischa \\-\\> O'zbekcha*\n\n"
        "Menga xohlagan tarjima qilmoqchi bo'lgan so'zlarni yoki matnlarni yuboring\\! ⚡",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return DEU_UZB_INPUT


def translator_result_keyboard(direction: str) -> InlineKeyboardMarkup:
    """Tarjima natijasi ostida ko'rsatiladigan tugmalar."""
    other = "deu_uzb" if direction == "uzb_deu" else "uzb_deu"
    other_label = "🇩🇪➡️🇺🇿 Nemischa→O'zbek" if direction == "uzb_deu" else "🇺🇿➡️🇩🇪 O'zbek→Nemis"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yana tarjima", callback_data=CB.UZB_DEU if direction == "uzb_deu" else CB.DEU_UZB)],
        [InlineKeyboardButton(other_label, callback_data=CB.DEU_UZB if direction == "uzb_deu" else CB.UZB_DEU)],
        [InlineKeyboardButton("🌐 Tarjimon", callback_data=CB.TRANSLATOR)],
        [InlineKeyboardButton("🏠 Asosiy menu", callback_data=CB.MAIN_MENU)],
    ])


async def translation_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi so'z yuborgan paytda chaqiriladi."""
    word = update.message.text.strip()
    if not word:
        await update.message.reply_text("❗ Iltimos so'z yuboring\\.", parse_mode="MarkdownV2")
        return context.user_data.get("translator_state", UZB_DEU_INPUT)

    direction = context.user_data.get("translator_dir", "uzb_deu")

    # Yuklanmoqda...
    loading_msg = await update.message.reply_text("⏳ Tarjima qilinmoqda\\.\\.\\.", parse_mode="MarkdownV2")

    result_text = await do_translate(word, direction)

    await loading_msg.delete()
    await update.message.reply_text(
        result_text,
        parse_mode="MarkdownV2",
        reply_markup=translator_result_keyboard(direction),
    )

    # Xuddi shu yo'nalishda davom etish uchun state saqlanadi
    return UZB_DEU_INPUT if direction == "uzb_deu" else DEU_UZB_INPUT


# ==================== YORDAM ====================

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "ℹ️ *Yordam*\n\n"
        "/start \\— Botni ishga tushirish\n"
        "/menu \\— Asosiy menyu\n\n"
        "📚 *Darajalar:* A1, A2, B1, B2, C1\n"
        "📗 A1/A2/B1 \\— Motive, Schritte, Menschen\n"
        "📙 B2/C1 \\— Sicher, KompassDaF, Aspekte\n"
        "🌐 Tarjimon \\— UZB↔DEU\n\n"
        "✅ *Hozirda mavjud:* A1 Motive 1\\-8 lektsiyalar",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )
    return MAIN_MENU

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🏠 *Asosiy Menu*\n\nBo'limni tanlang:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n/start \\— Boshlash\n/menu \\— Menyu",
        parse_mode="MarkdownV2",
        reply_markup=back_to_main_keyboard(),
    )


# ==================== MAIN ====================

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    common_handlers = [
        CallbackQueryHandler(main_menu_handler,    pattern=f"^{CB.MAIN_MENU}$"),
        CallbackQueryHandler(level_select_handler, pattern=f"^{CB.LEVEL_SELECT}$"),
        CallbackQueryHandler(level_a1_handler,     pattern=f"^{CB.LEVEL_A1}$"),
        CallbackQueryHandler(level_a2_handler,     pattern=f"^{CB.LEVEL_A2}$"),
        CallbackQueryHandler(level_b1_handler,     pattern=f"^{CB.LEVEL_B1}$"),
        CallbackQueryHandler(level_b2_handler,     pattern=f"^{CB.LEVEL_B2}$"),
        CallbackQueryHandler(level_c1_handler,     pattern=f"^{CB.LEVEL_C1}$"),
        CallbackQueryHandler(b1_prep_handler,      pattern=f"^{CB.B1_PREP}$"),
        CallbackQueryHandler(b2_prep_handler,      pattern=f"^{CB.B2_PREP}$"),
        CallbackQueryHandler(c1_prep_handler,      pattern=f"^{CB.C1_PREP}$"),
        CallbackQueryHandler(translator_handler,   pattern=f"^{CB.TRANSLATOR}$"),
        CallbackQueryHandler(uzb_deu_handler,      pattern=f"^{CB.UZB_DEU}$"),
        CallbackQueryHandler(deu_uzb_handler,      pattern=f"^{CB.DEU_UZB}$"),
        CallbackQueryHandler(help_handler,         pattern=f"^{CB.HELP}$"),
        CallbackQueryHandler(book_select_handler,  pattern=r"^book_(a1|a2|b1|b2|c1)_\w+$"),
        CallbackQueryHandler(back_book_handler,    pattern=r"^back_book_(a1|a2|b1|b2|c1)$"),
        CallbackQueryHandler(lektion_handler,      pattern=r"^lekt_(a1|a2|b1|b2|c1)_\w+_\d+$"),
        # Quiz
        CallbackQueryHandler(quiz_start_handler,   pattern=r"^quiz_start_(a1|a2|b1|b2|c1)_\w+_\d+$"),
        CallbackQueryHandler(quiz_know_handler,    pattern=f"^{CB.QUIZ_KNOW}$"),
        CallbackQueryHandler(quiz_dontknow_handler,pattern=f"^{CB.QUIZ_DONTKNOW}$"),
        CallbackQueryHandler(quiz_repeat_handler,  pattern=f"^{CB.QUIZ_REPEAT}$"),
        # Pomodoro
        CallbackQueryHandler(pomodoro_start_handler, pattern=r"^pomodoro_start_(a1|a2|b1|b2|c1)_\w+_\d+$"),
        CallbackQueryHandler(pomodoro_stop_handler,  pattern=f"^{CB.POMODORO_STOP}$"),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU:    common_handlers,
            LEVEL_SELECT: common_handlers,
            A1_MENU:      common_handlers,
            A2_MENU:      common_handlers,
            B1_MENU:      common_handlers,
            B2_MENU:      common_handlers,
            C1_MENU:      common_handlers,
            BOOK_MENU:    common_handlers,
            TRANSLATOR:   common_handlers,
            QUIZ_STATE:   common_handlers,
            POMODORO_STATE: common_handlers,
            UZB_DEU_INPUT: common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translation_input_handler),
            ],
            DEU_UZB_INPUT: common_handlers + [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translation_input_handler),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu",  menu_command),
            CommandHandler("help",  help_command),
        ],
        per_message=False,
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))

    print("🤖 Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
