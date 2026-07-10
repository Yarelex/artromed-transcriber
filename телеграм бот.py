import logging
import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

client = OpenAI(api_key="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")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-транскрибатор от АртроМед.\n\n"
        "Отправь голосовое сообщение или аудиофайл."
    )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file = None
    
    if message.voice:
        file = await message.voice.get_file()
    elif message.audio:
        file = await message.audio.get_file()
    elif message.document and (message.document.mime_type or "").startswith("audio"):
        file = await message.document.get_file()
    else:
        await message.reply_text("Отправь голосовое или аудиофайл.")
        return

    await message.reply_text("⬇️ Скачиваю и конвертирую...")

    ogg_path = f"voice_{message.message_id}.ogg"
    mp3_path = ogg_path.replace(".ogg", ".mp3")
    
    await file.download_to_drive(ogg_path)

    try:
        # Конвертация OGG → MP3 через ffmpeg
        subprocess.run([
            "ffmpeg", "-i", ogg_path, "-acodec", "libmp3lame", "-q:a", "0", mp3_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Транскрипция
        with open(mp3_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        text = transcript.text.strip()

        await message.reply_text(f"✅ **Транскрипция готова:**\n\n{text}")

    except subprocess.CalledProcessError:
        await message.reply_text("❌ Ошибка конвертации аудио. Убедись, что ffmpeg установлен.")
    except Exception as e:
        await message.reply_text(f"❌ Ошибка: {str(e)}")
    finally:
        for path in [ogg_path, mp3_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

def main():
    TOKEN = "8810437865:AAHafb5EqycUF1tUik_9atN9lye1MLaG_eE"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO | filters.Document.AUDIO, 
        handle_audio
    ))

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
