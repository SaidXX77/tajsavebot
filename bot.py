import os
import yt_dlp
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message
from aiogram.filters import Command, Text
import nest_asyncio
nest_asyncio.apply()
from aiogram.utils.markdown import link

# Получаем токен из переменной окружения
TOKEN = os.getenv("TOKEN", "7341799826:AAFS-TMnZIEhbV8ZV2QB5X-DelfMl4skKaE")
if not TOKEN:
    raise ValueError("Не указан токен бота. Установите переменную окружения TOKEN.")

bot = Bot(token=TOKEN)
router = Router()
dp = Dispatcher()
dp.include_router(router)

def get_direct_link(video_url):
    """Получение прямой ссылки на видео."""
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'quiet': True,
        'no_warnings': True,
        'outtmpl': '%(id)s.%(ext)s',
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
    formats = info_dict['formats']
    for fmt in formats:
        if fmt.get('height') == 720:
            return fmt['url']
    return None

@router.message(Command("start"))
async def start_command_handler(message: Message):
    """Обработчик команды /start."""
    await message.reply("Просто отправьте мне ссылку на видео YouTube, и я скачаю его для вас!")

@router.message(Text(regexp=r'^https:\/\/(www\.youtube.*|youtu\.be.*|youtube\.com.*)'))
async def youtube_link_handler(message: Message):
    """Обработчик сообщений с YouTube-ссылками."""
    url = message.text.strip()
    await message.answer("Обрабатываю ссылку, пожалуйста, подождите...")
    try:
        direct_link = get_direct_link(url)
        if direct_link:
            text = link("Вот, лови", direct_link)
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("Не удалось найти видео в разрешении 720p.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке ссылки: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling(bot, skip_updates=True))
    loop.run_forever()
