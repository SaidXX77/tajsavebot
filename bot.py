import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import aiofiles

# Загрузка переменных окружения
load_dotenv()

# Токен бота и URL вебхука
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not TOKEN or not WEBHOOK_URL:
    raise ValueError("Необходимо указать TOKEN и WEBHOOK_URL в переменных окружения.")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ - ограничение Telegram на отправку файлов

def get_ydl_options(resolution=None):
    """Опции для загрузки через yt-dlp."""
    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best' if resolution else 'bestaudio',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
    }
    return ydl_opts

async def download_video(url, resolution=None):
    """Скачивание видео через yt-dlp."""
    try:
        with YoutubeDL(get_ydl_options(resolution)) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logging.error(f"Ошибка при загрузке видео: {e}")
        return None

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Обработчик команды /start."""
    welcome_text = (
        "Привет! 👋\n\n"
        "Я помогу вам скачать видео или аудио с YouTube. 🟡\n\n"
        "Просто отправьте ссылку на видео, и выберите желаемое качество.\n\n"
        "❗ Видео должно быть меньше 50 МБ."
    )
    await message.reply(welcome_text)

@dp.message_handler()
async def handle_message(message: types.Message):
    """Обработчик сообщений (ссылки)."""
    if "youtube.com" in message.text or "youtu.be" in message.text:
        try:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("360p", callback_data=f"video|360p|{message.text}"))
            keyboard.add(InlineKeyboardButton("720p", callback_data=f"video|720p|{message.text}"))
            keyboard.add(InlineKeyboardButton("Скачать аудио", callback_data=f"audio|{message.text}"))

            await message.reply("Выберите, что вы хотите скачать:", reply_markup=keyboard)
        except Exception as e:
            logging.error(f"Ошибка обработки ссылки: {e}")
            await message.reply("Не удалось обработать ссылку. Проверьте её и попробуйте снова.")
    else:
        await message.reply("Пожалуйста, отправьте корректную ссылку на YouTube-видео.")

@dp.callback_query_handler(lambda c: c.data.startswith("video"))
async def handle_video_download(callback_query: types.CallbackQuery):
    """Обработчик скачивания видео."""
    try:
        await bot.answer_callback_query(callback_query.id, "Начинаю обработку...")
        _, resolution, url = callback_query.data.split("|")
        logging.info(f"Запрос на скачивание видео. URL: {url}, разрешение: {resolution}")

        file_path = await download_video(url, resolution)

        if not file_path:
            logging.error("Видео не было скачано. Возможно, формат или разрешение недоступны.")
            await bot.send_message(callback_query.from_user.id, "Не удалось скачать видео. Попробуйте другой формат.")
            return

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            logging.warning(f"Файл {file_path} превышает лимит 50 МБ.")
            await bot.send_message(callback_query.from_user.id, "Видео слишком большое для отправки через Telegram.")
            os.remove(file_path)
            return

        async with aiofiles.open(file_path, mode='rb') as video:
            await bot.send_video(callback_query.from_user.id, video, caption="🎥 Ваше видео готово!")
        logging.info(f"Видео {file_path} успешно отправлено пользователю.")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Ошибка в обработчике handle_video_download: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при скачивании видео.")

@dp.callback_query_handler(lambda c: c.data.startswith("audio"))
async def handle_audio_download(callback_query: types.CallbackQuery):
    """Обработчик скачивания аудио."""
    try:
        await bot.answer_callback_query(callback_query.id, "Начинаю обработку...")
        _, url = callback_query.data.split("|")
        logging.info(f"Запрос на скачивание аудио. URL: {url}")

        file_path = await download_video(url)

        if not file_path:
            logging.error("Аудио не было скачано. Возможно, формат недоступен.")
            await bot.send_message(callback_query.from_user.id, "Не удалось скачать аудио.")
            return

        file_name = file_path.replace(file_path.split('.')[-1], 'mp3')
        os.rename(file_path, file_name)

        async with aiofiles.open(file_name, mode='rb') as audio:
            await bot.send_audio(callback_query.from_user.id, audio, caption="🎵 Ваше аудио готово!")
        logging.info(f"Аудио {file_name} успешно отправлено пользователю.")
        os.remove(file_name)
    except Exception as e:
        logging.error(f"Ошибка в обработчике handle_audio_download: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при скачивании аудио.")

async def on_startup(dp):
    """Действия при старте бота."""
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info("Webhook установлен успешно.")
    except Exception as e:
        logging.error(f"Ошибка установки webhook: {e}")

async def on_shutdown(dp):
    """Действия при завершении работы бота."""
    await bot.delete_webhook()
    logging.info("Webhook успешно удалён.")

if __name__ == "__main__":
    executor.start_webhook(
        dispatcher=dp,
        webhook_path="/webhook",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        skip_updates=True,
    )
