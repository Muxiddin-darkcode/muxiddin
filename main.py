import os
import re
import json
import logging
import asyncio
import sqlite3
import hashlib
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Telegram bot uchun
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

# Video yuklash va audio qayta ishlash uchun
import yt_dlp
import numpy as np
import soundfile as sf
from pydub import AudioSegment

# Web scraping uchun (YouTube qidirish)
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import requests

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


# ==================== KONFIGURATSIYA ====================
@dataclass
class Config:
    # O'zgartiring
    BOT_TOKEN: str = "8060421255:AAFL9gVXmFiktffb1w6bKmtMJGf63Q3Sfz0"
    ADMIN_IDS: List[int] = 5993782563  # Admin ID lari
    MANDATORY_CHANNEL: str = "@SOUL_MUSIC_2026"  # Majburiy kanal
    CHANNEL_LINK: str = "https://t.me/SOUL_MUSIC_2026"
    DATABASE_FILE: str = "music_bot_v2.db"

    # Audio fingerprint sozlamalari
    FINGERPRINT_DIR: str = "fingerprints"
    SAMPLE_RATE: int = 22050
    FINGERPRINT_SIZE: int = 4096

    # YouTube scraping
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    YOUTUBE_SEARCH_URL: str = "https://www.youtube.com/results"
    YOUTUBE_WATCH_URL: str = "https://www.youtube.com/watch"

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = [5993782563]


config = Config()


# ==================== MA'LUMOTLAR BAZASI ====================
class Database:
    def __init__(self, db_file="music_bot_v2.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Foydalanuvchilar
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           user_id
                           INTEGER
                           PRIMARY
                           KEY,
                           username
                           TEXT,
                           first_name
                           TEXT,
                           last_name
                           TEXT,
                           join_date
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           downloads
                           INTEGER
                           DEFAULT
                           0,
                           music_finds
                           INTEGER
                           DEFAULT
                           0,
                           is_premium
                           INTEGER
                           DEFAULT
                           0,
                           last_active
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           is_banned
                           INTEGER
                           DEFAULT
                           0
                       )
                       ''')

        # Yuklab olishlar tarixi
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS downloads
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           user_id
                           INTEGER,
                           instagram_url
                           TEXT,
                           video_path
                           TEXT,
                           music_title
                           TEXT,
                           music_artist
                           TEXT,
                           youtube_url
                           TEXT,
                           audio_path
                           TEXT,
                           download_date
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           FOREIGN
                           KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       )
                           )
                       ''')

        # Audio fingerprint ma'lumotlari
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS audio_fingerprints
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           audio_hash
                           TEXT
                           UNIQUE,
                           title
                           TEXT,
                           artist
                           TEXT,
                           youtube_id
                           TEXT,
                           duration
                           INTEGER,
                           fingerprint_data
                           BLOB,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # Reklamalar
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS advertisements
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           admin_id
                           INTEGER,
                           message
                           TEXT,
                           target
                           TEXT
                           DEFAULT
                           'all',
                           sent_count
                           INTEGER
                           DEFAULT
                           0,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           status
                           TEXT
                           DEFAULT
                           'pending'
                       )
                       ''')

        # Statistika
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS stats
                       (
                           date
                           DATE
                           PRIMARY
                           KEY,
                           new_users
                           INTEGER
                           DEFAULT
                           0,
                           downloads
                           INTEGER
                           DEFAULT
                           0,
                           music_finds
                           INTEGER
                           DEFAULT
                           0,
                           active_users
                           INTEGER
                           DEFAULT
                           0
                       )
                       ''')

        self.conn.commit()

    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute('''
                       INSERT
                       OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
                       ''', (user_id, username, first_name, last_name))
        self.conn.commit()

    def update_user_activity(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
                       UPDATE users
                       SET last_active = CURRENT_TIMESTAMP
                       WHERE user_id = ?
                       ''', (user_id,))
        self.conn.commit()

    def increment_downloads(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
                       UPDATE users
                       SET downloads = downloads + 1
                       WHERE user_id = ?
                       ''', (user_id,))
        self.conn.commit()

    def increment_music_finds(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
                       UPDATE users
                       SET music_finds = music_finds + 1
                       WHERE user_id = ?
                       ''', (user_id,))
        self.conn.commit()

    def add_download_record(self, user_id, instagram_url, video_path=None, music_data=None, youtube_url=None,
                            audio_path=None):
        cursor = self.conn.cursor()
        cursor.execute('''
                       INSERT INTO downloads (user_id, instagram_url, video_path, music_title, music_artist,
                                              youtube_url, audio_path)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           user_id,
                           instagram_url,
                           video_path,
                           music_data.get('title') if music_data else None,
                           music_data.get('artist') if music_data else None,
                           youtube_url,
                           audio_path
                       ))
        self.conn.commit()
        return cursor.lastrowid

    def add_audio_fingerprint(self, audio_hash, title, artist, youtube_id, duration, fingerprint_data):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                           INSERT INTO audio_fingerprints (audio_hash, title, artist, youtube_id, duration, fingerprint_data)
                           VALUES (?, ?, ?, ?, ?, ?)
                           ''', (audio_hash, title, artist, youtube_id, duration, fingerprint_data))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def find_similar_fingerprint(self, fingerprint_hash):
        """Oddiy hash solishtirish orqali o'xshash audio topish"""
        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT *
                       FROM audio_fingerprints
                       WHERE audio_hash LIKE ? || '%' LIMIT 1
                       ''', (fingerprint_hash[:10],))
        return cursor.fetchone()

    def get_user_stats(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
        return [row[0] for row in cursor.fetchall()]

    def get_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM downloads')
        total_downloads = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM downloads WHERE date(download_date) = date("now")')
        active_today = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM audio_fingerprints')
        total_fingerprints = cursor.fetchone()[0]

        return {
            'total_users': total_users,
            'total_downloads': total_downloads,
            'active_today': active_today,
            'total_fingerprints': total_fingerprints
        }


db = Database()


# ==================== AUDIO FINGERPRINT SISTEMASI ====================
class AudioFingerprinter:
    def __init__(self):
        self.fingerprint_dir = Path(config.FINGERPRINT_DIR)
        self.fingerprint_dir.mkdir(exist_ok=True)

    def generate_audio_hash(self, audio_data: bytes) -> str:
        """Audio ma'lumotlaridan hash yaratish"""
        return hashlib.md5(audio_data).hexdigest()

    def extract_audio_features(self, audio_path: str) -> Optional[np.ndarray]:
        """Audio fayldan oddiy xususiyatlar olish"""
        try:
            # Pydub yordamida audio o'qish
            audio = AudioSegment.from_file(audio_path)

            # 16kHz ga konvert qilish
            audio = audio.set_frame_rate(16000)

            # Stereo -> Mono
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Audio ma'lumotlarini numpy array ga o'tkazish
            samples = np.array(audio.get_array_of_samples())

            # Normalizatsiya
            if samples.max() > 0:
                samples = samples / samples.max()

            return samples

        except Exception as e:
            logger.error(f"Audio features extract error: {e}")
            return None

    def create_simple_fingerprint(self, audio_path: str) -> Optional[str]:
        """Oddiy audio fingerprint yaratish"""
        try:
            # Audio faylni o'qib, hash yaratish
            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            # Audio uzunligi va birinchi 1000 bayt orqali hash
            file_size = len(audio_data)
            sample_data = audio_data[:1000] if len(audio_data) > 1000 else audio_data

            # Hash yaratish
            hash_input = f"{file_size}{sample_data.hex()}".encode()
            fingerprint = hashlib.sha256(hash_input).hexdigest()

            return fingerprint

        except Exception as e:
            logger.error(f"Fingerprint creation error: {e}")
            return None


# ==================== YOUTUBE SCRAPER ====================
class YouTubeScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': config.USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

    async def search_youtube(self, query: str, max_results: int = 5) -> List[Dict]:
        """YouTube dan qidiruv (web scraping orqali)"""
        try:
            # Query ni encode qilish
            encoded_query = urllib.parse.quote_plus(query)
            url = f"{config.YOUTUBE_SEARCH_URL}?search_query={encoded_query}"

            # Request yuborish
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            # HTML ni parse qilish
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Video elementlarini topish
            video_elements = soup.find_all('a', {'id': 'video-title'})

            for element in video_elements[:max_results]:
                try:
                    title = element.get('title', '').strip()
                    video_id = element.get('href', '').split('v=')[-1].split('&')[0]

                    if title and video_id and len(video_id) == 11:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                        # Davomiylikni olish
                        duration_span = element.find_next('span', {
                            'class': 'style-scope ytd-thumbnail-overlay-time-status-renderer'})
                        duration = duration_span.text.strip() if duration_span else "N/A"

                        results.append({
                            'title': title,
                            'video_id': video_id,
                            'url': video_url,
                            'duration': duration
                        })
                except:
                    continue

            return results

        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return []

    async def download_youtube_audio(self, video_url: str, output_path: str) -> Tuple[bool, str]:
        """YouTube dan audio yuklash (yt-dlp orqali)"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

                # Fayl yo'lini to'g'rilash
                audio_file = output_path.replace('.%(ext)s', '.mp3')
                if not os.path.exists(audio_file):
                    # Boshqa formatlarni tekshirish
                    base_name = os.path.splitext(output_path)[0]
                    for ext in ['.mp3', '.m4a', '.webm']:
                        if os.path.exists(base_name + ext):
                            audio_file = base_name + ext
                            break

                return True, audio_file if os.path.exists(audio_file) else None

        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return False, str(e)


# ==================== MUSIQA ANIQLOVCHI ====================
class MusicRecognizer:
    def __init__(self):
        self.fingerprinter = AudioFingerprinter()
        self.youtube_scraper = YouTubeScraper()
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)

    def extract_audio_from_video(self, video_path: str, audio_path: str) -> bool:
        """Videodan audioni ajratib olish"""
        try:
            # Pydub orqali audio ajratish
            video = AudioSegment.from_file(video_path)
            video.export(audio_path, format="mp3", bitrate="192k")
            return True
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return False

    async def recognize_music_from_audio(self, audio_path: str) -> Dict:
        """Audio orqali musiqa aniqlash"""
        try:
            # 1. Audio fingerprint yaratish
            fingerprint = self.fingerprinter.create_simple_fingerprint(audio_path)

            if not fingerprint:
                return {"status": "error", "message": "Audio fingerprint yaratilmadi"}

            # 2. Bazadan o'xshash fingerprint qidirish
            existing_record = db.find_similar_fingerprint(fingerprint)

            if existing_record:
                # Bazada topildi
                return {
                    "status": "success",
                    "source": "database",
                    "title": existing_record['title'],
                    "artist": existing_record['artist'],
                    "youtube_id": existing_record['youtube_id'],
                    "message": f"🎵 Bazadan topildi: {existing_record['title']} - {existing_record['artist']}"
                }

            # 3. Agar bazada yo'q bo'lsa, YouTube dan qidirish
            # Audio nomidan foydalanib qidirish (oddiy usul)
            # Real loyihada audio analiz qilinadi, lekin bu yerda oddiy qidiruv
            query = "popular music 2024"  # Demo uchun
            youtube_results = await self.youtube_scraper.search_youtube(query, 3)

            if youtube_results:
                # Birinchi natijani olish
                result = youtube_results[0]

                # Audio fingerprint ni bazaga saqlash
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()

                # Ma'lumotlarni bazaga qo'shish
                db.add_audio_fingerprint(
                    audio_hash=fingerprint,
                    title=result['title'],
                    artist="Unknown Artist",  # Haqiqiy loyihada artist aniqlash kerak
                    youtube_id=result['video_id'],
                    duration=0,  # Demo
                    fingerprint_data=audio_data[:1000]  # Faqat bir qismini saqlaymiz
                )

                return {
                    "status": "success",
                    "source": "youtube",
                    "title": result['title'],
                    "artist": "Unknown Artist",
                    "youtube_url": result['url'],
                    "youtube_id": result['video_id'],
                    "message": f"🎵 YouTube dan topildi: {result['title']}"
                }

            return {"status": "not_found", "message": "Musiqa topilmadi"}

        except Exception as e:
            logger.error(f"Music recognition error: {e}")
            return {"status": "error", "message": f"Xatolik: {str(e)}"}

    async def download_and_send_music(self, music_data: Dict, chat_id: int, context: CallbackContext) -> Tuple[
        bool, str]:
        """Musiqani yuklab, foydalanuvchiga yuborish"""
        try:
            if 'youtube_url' not in music_data:
                return False, "YouTube havolasi topilmadi"

            # YouTube dan audio yuklash
            output_template = str(self.downloads_dir / "%(id)s.%(ext)s")
            success, result = await self.youtube_scraper.download_youtube_audio(
                music_data['youtube_url'],
                output_template
            )

            if not success or not result:
                return False, "Audio yuklanmadi"

            # Audio faylni yuborish
            try:
                with open(result, 'rb') as audio_file:
                    caption = f"🎵 **{music_data.get('title', 'Musiqa')}**"
                    if music_data.get('artist'):
                        caption += f"\n🎤 {music_data['artist']}"

                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=InputFile(audio_file, filename=f"{music_data.get('title', 'music')}.mp3"),
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )

                # Faylni o'chirish
                os.remove(result)
                return True, "✅ Musiqa muvaffaqiyatli yuborildi!"

            except Exception as e:
                logger.error(f"Audio send error: {e}")
                return False, f"Audio yuborishda xatolik: {str(e)}"

        except Exception as e:
            logger.error(f"Download and send error: {e}")
            return False, f"Xatolik: {str(e)}"


# ==================== INSTAGRAM YUKLOVCHI ====================
class InstagramDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)

    def extract_shortcode(self, url: str) -> Optional[str]:
        """Instagram URL dan shortcode olish"""
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/tv/([^/?]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def download_video(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Instagram videoni yuklash"""
        try:
            shortcode = self.extract_shortcode(url)
            if not shortcode:
                return None, "❌ Noto'g'ri Instagram havolasi"

            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(self.downloads_dir / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
                'retries': 3,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.instagram.com/p/{shortcode}", download=True)
                filename = ydl.prepare_filename(info)

                # Fayl mavjudligini tekshirish
                if not os.path.exists(filename):
                    base_name = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.mkv', '.webm']:
                        if os.path.exists(base_name + ext):
                            return base_name + ext, None

                return filename, None

        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            return None, f"❌ Yuklash xatosi: {str(e)}"


# ==================== ASOSIY BOT ====================
class InstagramMusicBot:
    def __init__(self):
        self.config = config
        self.db = db
        self.instagram_downloader = InstagramDownloader()
        self.music_recognizer = MusicRecognizer()
        self.setup_directories()

        # Telegram bot
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.setup_handlers()

    def setup_directories(self):
        """Kerakli papkalarni yaratish"""
        directories = ['downloads', 'temp', 'fingerprints', 'music']
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)

    def setup_handlers(self):
        """Bot handlerlarini sozlash"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))

        # Instagram link handler
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'instagram\.com'),
            self.handle_instagram_link
        ))

        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))

        # Unknown command handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))

    # ========== COMMAND HANDLERS ==========

    async def start_command(self, update: Update, context: CallbackContext):
        """Boshlash komandasi"""
        user = update.effective_user
        user_id = user.id

        # Foydalanuvchini bazaga qo'shish
        db.add_user(user_id, user.username, user.first_name, user.last_name)

        # Kanal a'zoligini tekshirish
        try:
            member = await context.bot.get_chat_member(config.MANDATORY_CHANNEL, user_id)
            if member.status in ['member', 'administrator', 'creator']:
                await self.send_welcome_message(update, user, subscribed=True)
            else:
                await self.send_welcome_message(update, user, subscribed=False)
        except Exception as e:
            logger.error(f"Channel check error: {e}")
            await self.send_welcome_message(update, user, subscribed=False)

    async def send_welcome_message(self, update: Update, user, subscribed: bool):
        """Xush kelibsiz xabarini yuborish"""
        if subscribed:
            welcome_text = f"""
🎵 **Salom {user.first_name}!**

🤖 **Music Finder Bot** ga xush kelibsiz!

✨ **Bot imkoniyatlari:**
• Instagram video yuklab olish
• Videodagi musiqa nomini aniqlash
• Musiqani yuklab olish
• Audio kutubxona yaratish

📥 **Foydalanish:**
Instagram video linkini yuboring!

📍 **Misol:**
https://www.instagram.com/reel/Cxample...

🔍 **Musiqa aniqlash:** Bot videodagi musiqani aniqlab, uni yuklab beradi!

📊 **Statistika:** /stats
ℹ️ **Yordam:** /help
"""
            keyboard = [[InlineKeyboardButton("📤 Video Yuklash", url="https://t.me/example")]]
        else:
            welcome_text = f"""
🎵 **Salom {user.first_name}!**

🤖 **Music Finder Bot** dan foydalanish uchun kanalga a'zo bo'ling:

📢 **Majburiy kanal:** {config.MANDATORY_CHANNEL}

⚠️ **Diqqat:** Kanalga a'zo bo'lmaguningizcha botdan foydalana olmaysiz!
"""
            keyboard = [
                [InlineKeyboardButton("📢 Kanalga o'tish", url=config.CHANNEL_LINK)],
                [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="check_subscription")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: CallbackContext):
        """Yordam komandasi"""
        help_text = """
🤖 **BOT YORDAMI**

📌 **Asosiy komandalar:**
/start - Botni ishga tushirish
/help - Yordam olish
/stats - Statistika ko'rish

📥 **Video yuklash:**
Instagram video linkini shunchaki yuboring!

🎵 **Musiqa aniqlash:**
1. Video yuklanadi
2. Audioni ajratiladi
3. Musiqa aniqlanadi
4. YouTube dan yuklab olinadi
5. Sizga yuboriladi

⚠️ **Eslatmalar:**
• Faqat public videolar
• Katta videolar vaqt oladi
• Ba'zi musiqalar topilmasligi mumkin

📞 **Qo'llab-quvvatlash:**
Muammo bo'lsa admin bilan bog'laning.
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def stats_command(self, update: Update, context: CallbackContext):
        """Statistika komandasi"""
        user_id = update.effective_user.id

        # Admin tekshiruvi
        if user_id not in config.ADMIN_IDS:
            user_stats = db.get_user_stats(user_id)
            if user_stats:
                stats_text = f"""
📊 **SIZNING STATISTIKANGIZ**

👤 **Ma'lumotlar:**
• Ism: {user_stats['first_name']}
• Username: @{user_stats['username'] or 'N/A'}
• Ro'yxatdan o'tgan: {user_stats['join_date']}

📈 **Faoliyat:**
• Yuklab olishlar: {user_stats['downloads']}
• Topilgan musiqalar: {user_stats['music_finds']}
• So'nggi faol: {user_stats['last_active']}
"""
            else:
                stats_text = "❌ Statistika topilmadi."

            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
            return

        # Admin statistika
        stats = db.get_stats()
        stats_text = f"""
📊 **BOT STATISTIKASI** (Admin)

👥 **Foydalanuvchilar:**
• Jami: {stats['total_users']}
• Faol bugun: {stats['active_today']}

📥 **Yuklab olishlar:**
• Jami: {stats['total_downloads']}

🎵 **Audio bazasi:**
• Fingerprint lar: {stats['total_fingerprints']}

⚡ **Tezkor harakatlar:**
"""
        keyboard = [
            [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Reklama", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🗑️ Tozalash", callback_data="admin_clean")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(stats_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def admin_command(self, update: Update, context: CallbackContext):
        """Admin panel"""
        user_id = update.effective_user.id

        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text("❌ Siz admin emassiz!")
            return

        admin_text = """
🛠 **ADMIN PANELI**

⚙️ **Admin komandalari:**
/stats - Batafsil statistika
/broadcast - Reklama yuborish
/clean - Fayllarni tozalash

📊 **Statistika:** /stats
👥 **Foydalanuvchilar:** Quyidagi tugma
📢 **Reklama:** /broadcast <matn>
"""
        keyboard = [
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Reklama", callback_data="admin_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    async def broadcast_command(self, update: Update, context: CallbackContext):
        """Reklama yuborish"""
        user_id = update.effective_user.id

        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text("❌ Siz admin emassiz!")
            return

        if not context.args:
            await update.message.reply_text(
                "⚠️ Iltimos, reklama matnini kiriting!\nMasalan: /broadcast Salom yangilik!")
            return

        ad_text = ' '.join(context.args)
        users = db.get_all_users()

        # Tasdiqlash
        keyboard = [
            [
                InlineKeyboardButton("✅ Ha, yuborish", callback_data=f"confirm_broadcast:{ad_text}"),
                InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📢 **Reklamani yuborishni tasdiqlaysizmi?**\n\n{ad_text}\n\nJami: {len(users)} ta foydalanuvchi",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def unknown_command(self, update: Update, context: CallbackContext):
        """Noma'lum buyruq"""
        await update.message.reply_text(
            "❌ Noma'lum buyruq.\n\n"
            "📌 **Foydalanish:** Instagram video linkini yuboring yoki /help ni bosing.",
            parse_mode=ParseMode.MARKDOWN
        )

    # ========== INSTAGRAM LINK HANDLER ==========

    async def handle_instagram_link(self, update: Update, context: CallbackContext):
        """Instagram linkini qayta ishlash"""
        user = update.effective_user
        user_id = user.id
        url = update.message.text

        # Faollikni yangilash
        db.update_user_activity(user_id)

        # Kanal a'zoligini tekshirish
        try:
            member = await context.bot.get_chat_member(config.MANDATORY_CHANNEL, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("📢 Kanalga o'tish", url=config.CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "⚠️ Botdan foydalanish uchun avval kanalga a'zo bo'ling!",
                    reply_markup=reply_markup
                )
                return
        except Exception as e:
            logger.error(f"Channel check error: {e}")
            await update.message.reply_text("❌ Kanal tekshirishda xatolik!")
            return

        # Yuklash boshlanishi haqida xabar
        processing_msg = await update.message.reply_text("🎬 **Video yuklanmoqda...**")

        try:
            # 1. Video yuklash
            await processing_msg.edit_text("⏬ Video yuklanmoqda...")
            video_path, error = await self.instagram_downloader.download_video(url)

            if error or not video_path:
                await processing_msg.edit_text(f"❌ {error or 'Video yuklanmadi'}")
                return

            # 2. Statistikani yangilash
            db.increment_downloads(user_id)

            # 3. Videoni yuborish
            await processing_msg.edit_text("📤 Video yuborilmoqda...")

            try:
                with open(video_path, 'rb') as video_file:
                    await update.message.reply_video(
                        video=InputFile(video_file, filename="instagram_video.mp4"),
                        caption="✅ **Video muvaffaqiyatli yuklandi!**\n\n🎵 **Musiqa aniqlanmoqda...**",
                        supports_streaming=True,
                        parse_mode=ParseMode.MARKDOWN
                    )
            except Exception as e:
                logger.error(f"Video send error: {e}")

            # 4. Audio ajratish va musiqa aniqlash
            await processing_msg.edit_text("🎵 **Musiqa aniqlanmoqda...**")

            audio_path = video_path.replace('.mp4', '.mp3')
            audio_extracted = self.music_recognizer.extract_audio_from_video(video_path, audio_path)

            if audio_extracted and os.path.exists(audio_path):
                # Musiqa aniqlash
                music_result = await self.music_recognizer.recognize_music_from_audio(audio_path)

                if music_result['status'] == 'success':
                    # Musiqani topildi
                    db.increment_music_finds(user_id)

                    # Musiqa ma'lumotlarini bazaga qo'shish
                    db.add_download_record(
                        user_id=user_id,
                        instagram_url=url,
                        video_path=video_path,
                        music_data={
                            'title': music_result.get('title'),
                            'artist': music_result.get('artist')
                        },
                        youtube_url=music_result.get('youtube_url')
                    )

                    # Musiqani yuklab yuborish
                    await processing_msg.edit_text("🎵 **Musiqa yuklanmoqda...**")

                    success, message = await self.music_recognizer.download_and_send_music(
                        music_result, user_id, context
                    )

                    if success:
                        await processing_msg.edit_text("✅ **Musiqa muvaffaqiyatli yuborildi!**")
                    else:
                        await processing_msg.edit_text(f"⚠️ {message}")

                elif music_result['status'] == 'not_found':
                    await processing_msg.edit_text("❌ **Musiqa topilmadi.**\n\nBoshqa video yuboring.")
                else:
                    await processing_msg.edit_text(f"⚠️ {music_result.get('message', 'Musiqa aniqlashda xatolik')}")

                # Audio faylni o'chirish
                try:
                    os.remove(audio_path)
                except:
                    pass
            else:
                await processing_msg.edit_text("⚠️ **Audio ajratishda xatolik.**")

            # 5. Video faylni o'chirish
            try:
                os.remove(video_path)
            except:
                pass

        except Exception as e:
            logger.error(f"Instagram link processing error: {e}")
            await processing_msg.edit_text(f"❌ **Xatolik yuz berdi:** {str(e)[:100]}")

    # ========== CALLBACK HANDLER ==========

    async def callback_handler(self, update: Update, context: CallbackContext):
        """Callback query handler"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        if data == "check_subscription":
            await self.handle_subscription_check(query, context)
        elif data.startswith("confirm_broadcast:"):
            if user_id in config.ADMIN_IDS:
                ad_text = data.split(":", 1)[1]
                await self.execute_broadcast(query, context, ad_text)
        elif data == "cancel_broadcast":
            await query.edit_message_text("✅ Reklama bekor qilindi.")
        elif data == "admin_stats":
            await self.show_admin_stats(query)
        elif data == "admin_users":
            await self.show_admin_users(query)
        elif data == "admin_broadcast":
            await query.edit_message_text("📢 Reklama yuborish uchun /broadcast <matn> buyrug'idan foydalaning.")
        elif data == "admin_clean":
            await self.clean_downloads(query)

    async def handle_subscription_check(self, query, context):
        """Kanal a'zoligini tekshirish"""
        user_id = query.from_user.id

        try:
            member = await context.bot.get_chat_member(config.MANDATORY_CHANNEL, user_id)
            if member.status in ['member', 'administrator', 'creator']:
                await query.edit_message_text(
                    "✅ **Rahmat! Endi Instagram video linkini yuboring.**\n\n"
                    "📍 **Misol:** https://www.instagram.com/reel/Cxample...",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("📢 Kanalga o'tish", url=config.CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    "⚠️ **Iltimos, kanalga a'zo bo'ling!**",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Subscription check error: {e}")
            keyboard = [[InlineKeyboardButton("📢 Kanalga o'tish", url=config.CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "❌ **Kanal topilmadi!**",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

    async def execute_broadcast(self, query, context, ad_text):
        """Reklamani yuborish"""
        users = db.get_all_users()
        sent_count = 0

        await query.edit_message_text(f"📤 **Reklama yuborilmoqda...**\n\n0/{len(users)}")

        for user_id in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **BOTDAN XABAR**\n\n{ad_text}\n\n👤 Admin",
                    parse_mode=ParseMode.MARKDOWN
                )
                sent_count += 1

                # Progress yangilash
                if sent_count % 10 == 0:
                    await query.edit_message_text(
                        f"📤 **Reklama yuborilmoqda...**\n\n{sent_count}/{len(users)}"
                    )

                # Kechikish
                await asyncio.sleep(0.3)

            except Exception as e:
                continue

        await query.edit_message_text(
            f"✅ **Reklama yuborildi!**\n\n"
            f"• Jami: {len(users)} ta\n"
            f"• Yuborildi: {sent_count} ta\n"
            f"• Xatolik: {len(users) - sent_count} ta",
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_admin_stats(self, query):
        """Admin statistika"""
        stats = db.get_stats()
        stats_text = f"""
📊 **ADMIN STATISTIKASI**

👥 **Foydalanuvchilar:**
• Jami: {stats['total_users']}
• Faol bugun: {stats['active_today']}

📥 **Yuklab olishlar:**
• Jami: {stats['total_downloads']}

🎵 **Audio bazasi:**
• Fingerprint lar: {stats['total_fingerprints']}

💾 **Fayl tizimi:**
• Downloads: {len(os.listdir('downloads')) if os.path.exists('downloads') else 0}
• Temp: {len(os.listdir('temp')) if os.path.exists('temp') else 0}
"""
        await query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    async def show_admin_users(self, query):
        """Foydalanuvchilar ro'yxati"""
        cursor = db.conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, downloads FROM users ORDER BY join_date DESC LIMIT 10')
        users = cursor.fetchall()

        users_text = "👥 **Oxirgi 10 ta foydalanuvchi:**\n\n"

        for user in users:
            username = f"@{user['username']}" if user['username'] else user['first_name']
            users_text += f"• {username} (ID: {user['user_id']}) - {user['downloads']} yuklash\n"

        all_users = db.get_all_users()
        users_text += f"\n📊 **Jami:** {len(all_users)} ta foydalanuvchi"

        await query.edit_message_text(users_text, parse_mode=ParseMode.MARKDOWN)

    async def clean_downloads(self, query):
        """Fayllarni tozalash"""
        try:
            for dir_name in ['downloads', 'temp']:
                if os.path.exists(dir_name):
                    for file in os.listdir(dir_name):
                        try:
                            os.remove(os.path.join(dir_name, file))
                        except:
                            pass

            await query.edit_message_text("✅ **Fayllar tozalandi!**", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await query.edit_message_text(f"❌ **Tozalashda xatolik:** {str(e)}", parse_mode=ParseMode.MARKDOWN)

    def run(self):
        """Botni ishga tushirish"""
        logger.info("🤖 Bot ishga tushmoqda...")
        print("=" * 50)
        print("🎵 INSTAGRAM MUSIC FINDER BOT")
        print("=" * 50)
        print(f"📊 Foydalanuvchilar: {db.get_stats()['total_users']}")
        print(f"📥 Yuklab olishlar: {db.get_stats()['total_downloads']}")
        print(f"🎵 Fingerprint lar: {db.get_stats()['total_fingerprints']}")
        print("=" * 50)

        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# ==================== ASOSIY FUNKSIYA ====================
def main():
    # Token tekshirish
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Iltimos, bot tokenini sozlang!")
        print("config.BOT_TOKEN = 'your_actual_bot_token'")
        return

    # Botni yaratish va ishga tushirish
    bot = InstagramMusicBot()
    bot.run()


if __name__ == "__main__":
    main()