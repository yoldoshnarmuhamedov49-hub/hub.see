cat << 'EOF' > main.py
import asyncio
import os
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp

BOT_TOKEN = "9030499922:AAEkN5SmqQUYUrfpHSjMjCSoUlZIxdX9QoY"
BITRATE = "192k"
TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Menga audio, ovozli xabar, shuningdek YouTube yoki Instagram havolasini yuboring. Men uni mashina magnitofonlari uchun 100% o'qiydigan toza MP3 formatiga o'tkazib beraman!")

async def to_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text or msg.caption or ""
    
    uid = uuid.uuid4().hex
    src = os.path.join(TMP_DIR, f"{uid}_in.mp3")
    dst = os.path.join(TMP_DIR, f"{uid}.mp3")
    
    file_obj = msg.audio or msg.voice or msg.document
    
    status = await msg.reply_text("🎵 Havola yoki fayl yuklanmoqda va magnitofon uchun tayyorlanmoqda...")
    
    try:
        if text.startswith("http://") or text.startswith("https://"):
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': src,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([text]))
            
            if os.path.exists(src):
                if src != dst:
                    os.rename(src, dst)
            else:
                found = False
                for f in os.listdir(TMP_DIR):
                    if f.startswith(uid) and f.endswith(".mp3"):
                        dst = os.path.join(TMP_DIR, f)
                        found = True
                        break
                if not found:
                    await status.edit_text("Xatolik: havoladagi audioni yuklab bo'lmadi. Havola ochiqligini tekshiring.")
                    return
        
        elif file_obj:
            tg_file = await file_obj.get_file()
            await tg_file.download_to_drive(src)
            
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-loglevel", "error", "-i", src,
                "-vn", "-ar", "44100", "-ac", "2", "-codec:a", "libmp3lame", "-b:a", BITRATE, dst,
                stderr=asyncio.subprocess.PIPE
            )
            _, err = await proc.communicate()
            
            if proc.returncode != 0 or not os.path.exists(dst):
                await status.edit_text("Xatolik: bu faylni MP3 ga o'zgartirib bo'lmadi.")
                return
        else:
            await status.edit_text("Iltimos, audio fayl, ovozli xabar yoki YouTube/Instagram havolasini yuboring!")
            return
            
        name = "Musiqa"
        with open(dst, "rb") as f:
            await msg.reply_audio(audio=f, title=name, performer="MP3 Bot", filename=f"{name}.mp3")
        await status.delete()
        
    except Exception as e:
        await status.edit_text(f"Xatolik yuz berdi: {e}")
    finally:
        for p in (src, dst):
            if os.path.exists(p) and p != dst:
                try:
                    os.remove(p)
                except:
                    pass
            if os.path.exists(dst) and text.startswith("http"):
                try:
                    os.remove(dst)
                except:
                    pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, to_mp3))
    print("Bot YouTube, Instagram va audio qo'llab-quvvatlash rejimida ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
EOF
