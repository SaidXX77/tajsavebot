import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from yt_dlp import YoutubeDL
import aiofiles
import asyncio
import html  # Используем стандартный модуль html из Python

# Получение токена из переменных окружения
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Не задан токен Telegram")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Настройки yt-dlp
def get_direct_link(video_url):
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'quiet': True,
        'no_warnings': True,
        'outtmpl': '%(id)s.%(ext)s',
        'merge_output_format': 'mp4'
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
    for fmt in info_dict.get('formats', []):
        if fmt.get('height') == 720:  # Только 720p
            return fmt['url']
    return None

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    """Обработчик команды /start."""
    await message.reply("Просто напиши мне ссылку на видео YouTube, а я скачаю его для тебя.")

@dp.message(F.text.regexp(r'^https:\/\/(www\.youtube.*|youtu\.be.*|youtube\.com.*)'))
async def video_handler(message: Message):
    """Обработчик сообщений с YouTube ссылками."""
    url = message.text
    try:
        direct_link = get_direct_link(url)
        if direct_link:
            # Экранирование ссылки с помощью html.escape
            text = f'<a href="{html.escape(direct_link)}">Вот, лови</a>'
            await message.answer(text, parse_mode="HTML")
        else:
            await message.reply("Не удалось найти видео в подходящем качестве.")
    except Exception as e:
        logging.error(f"Ошибка при обработке видео: {e}")
        await message.reply("Произошла ошибка при обработке видео.")

async def main():
    """Запуск бота."""
    try:
        logging.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
