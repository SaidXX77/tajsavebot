from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os
import yt_dlp

# Ваш токен
TOKEN = "7341799826:AAFS-TMnZIEhbV8ZV2QB5X-DelfMl4skKaE"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на YouTube, и я скачаю видео для тебя.")


@dp.message_handler()
async def download_video(message: types.Message):
    url = message.text.strip()

    if not url.startswith("http") or "youtube.com" not in url and "youtu.be" not in url:
        await message.reply("Пожалуйста, отправьте корректную ссылку на YouTube.")
        return

    try:
        # Настройки yt-dlp
        ydl_opts = {
            "format": "best",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "socket_timeout": 60,
            "retries": 3,
            "fragment_retries": 10,  # Повторная попытка загрузки сегментов
            "concurrent_fragment_downloads": 5,  # Одновременная загрузка нескольких сегментов
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        # Отправляем файл
        await bot.send_message(message.chat.id, "Видео скачано, отправляю файл...")
        with open(video_path, "rb") as video:
            await bot.send_video(message.chat.id, video)

        os.remove(video_path)
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")
        print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    executor.start_polling(dp, skip_updates=True)
