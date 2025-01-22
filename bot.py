import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytube import YouTube
from dotenv import load_dotenv
import aiofiles

# Загрузка переменных окружения
load_dotenv()

# Токен бота
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Не задан TOKEN. Убедитесь, что он указан в переменных окружения.")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ - ограничение Telegram на отправку файлов

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
            yt = YouTube(message.text)
            logging.info(f"Видео успешно загружено: {yt.title}")
            
            keyboard = InlineKeyboardMarkup()

            # Добавляем кнопки для выбора качества видео
            if yt.streams.filter(res="360p", file_extension="mp4").first():
                keyboard.add(InlineKeyboardButton("360p", callback_data=f"video|360p|{yt.watch_url}"))
            if yt.streams.filter(res="720p", file_extension="mp4").first():
                keyboard.add(InlineKeyboardButton("720p", callback_data=f"video|720p|{yt.watch_url}"))
            
            # Кнопка для скачивания аудио
            keyboard.add(InlineKeyboardButton("Скачать аудио", callback_data=f"audio|{yt.watch_url}"))

            await message.reply("Выберите, что вы хотите скачать:", reply_markup=keyboard)
        except KeyError:
            logging.error("Ошибка KeyError. Проверьте совместимость pytube с текущей версией YouTube.")
            await message.reply("Ошибка при обработке ссылки. Попробуйте обновить бота.")
        except Exception as e:
            logging.error(f"Общая ошибка обработки ссылки: {e}")
            await message.reply("Не удалось обработать ссылку. Проверьте её и попробуйте снова.")
    else:
        await message.reply("Пожалуйста, отправьте корректную ссылку на YouTube-видео.")


@dp.callback_query_handler(lambda c: c.data.startswith("video"))
async def handle_video_download(callback_query: types.CallbackQuery):
    """Обработчик скачивания видео."""
    try:
        _, resolution, url = callback_query.data.split("|")
        yt = YouTube(url)
        stream = yt.streams.filter(res=resolution, file_extension="mp4").first()

        if not stream:
            await bot.answer_callback_query(callback_query.id, "Видео в этом качестве недоступно.", show_alert=True)
            return

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Скачиваю видео, это может занять некоторое время...")

        file_path = stream.download()

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            await bot.send_message(callback_query.from_user.id, "Видео слишком большое для отправки через Telegram.")
            os.remove(file_path)
            return

        async with aiofiles.open(file_path, mode='rb') as video:
            await bot.send_video(callback_query.from_user.id, video, caption=f"🎥 {yt.title}")
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Ошибка загрузки видео: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при скачивании видео.")

@dp.callback_query_handler(lambda c: c.data.startswith("audio"))
async def handle_audio_download(callback_query: types.CallbackQuery):
    """Обработчик скачивания аудио."""
    try:
        _, url = callback_query.data.split("|")
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()

        if not stream:
            await bot.answer_callback_query(callback_query.id, "Аудио недоступно.", show_alert=True)
            return

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Скачиваю аудио, это может занять некоторое время...")

        file_path = stream.download()
        file_name = f"{yt.title}.mp3"
        os.rename(file_path, file_name)

        async with aiofiles.open(file_name, mode='rb') as audio:
            await bot.send_audio(callback_query.from_user.id, audio, caption=f"🎵 {yt.title}")
        os.remove(file_name)
    except Exception as e:
        logging.error(f"Ошибка загрузки аудио: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при скачивании аудио.")

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

