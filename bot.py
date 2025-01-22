import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import aiofiles
import yt_dlp

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


def download_video_or_audio(url, format_type="video"):
    """Скачивает видео или аудио с YouTube с использованием yt-dlp."""
    ydl_opts = {
        'format': 'bestvideo+bestaudio' if format_type == "video" else 'bestaudio',
        'outtmpl': f'%(title)s.%(ext)s',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info['title'], ydl.prepare_filename(info)


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

            # Добавляем кнопки для выбора качества видео
            keyboard.add(InlineKeyboardButton("Скачать видео", callback_data=f"video|{message.text}"))
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
        _, url = callback_query.data.split("|")

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Скачиваю видео, это может занять некоторое время...")

        title, file_path = download_video_or_audio(url, format_type="video")

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            await bot.send_message(callback_query.from_user.id, "Видео слишком большое для отправки через Telegram.")
            os.remove(file_path)
            return

        async with aiofiles.open(file_path, mode='rb') as video:
            await bot.send_video(callback_query.from_user.id, video, caption=f"🎥 {title}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Ошибка загрузки видео: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при скачивании видео.")


@dp.callback_query_handler(lambda c: c.data.startswith("audio"))
async def handle_audio_download(callback_query: types.CallbackQuery):
    """Обработчик скачивания аудио."""
    try:
        _, url = callback_query.data.split("|")

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Скачиваю аудио, это может занять некоторое время...")

        title, file_path = download_video_or_audio(url, format_type="audio")

        async with aiofiles.open(file_path, mode='rb') as audio:
            await bot.send_audio(callback_query.from_user.id, audio, caption=f"🎵 {title}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Ошибка загрузки аудио: {e}")
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
        port=int(os.getenv("PORT", 8443)),  # Используется переменная окружения PORT
        skip_updates=True,
    )
