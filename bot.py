import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytube import YouTube
from dotenv import load_dotenv
import aiofiles

# Загрузка переменных окружения
load_dotenv()

# Токен бота и настройки
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not all([TOKEN, WEBHOOK_URL, CHANNEL_ID]):
    raise ValueError("Не заданы все необходимые переменные окружения. Убедитесь, что TOKEN, WEBHOOK_URL и CHANNEL_ID установлены.")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Обработчик команды /start."""
    welcome_text = (
        "Привет! 👋\n\n"
        "Этот бот поможет скачать видео с YouTube.\n"
        "Просто отправьте ссылку на видео, и выберите желаемое качество.\n\n"
        "❗ Обратите внимание: перед использованием убедитесь, что вы подписаны на наш канал."
    )
    await message.reply(welcome_text)

async def check_subscription(user_id):
    """Проверяет, подписан ли пользователь на канал."""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

@dp.message_handler()
async def handle_message(message: types.Message):
    """Обработчик сообщений (ссылки)."""
    # Проверяем подписку
    is_subscribed = await check_subscription(message.from_user.id)

    if not is_subscribed:
        # Создаем клавиатуру с кнопкой для подписки
        keyboard = InlineKeyboardMarkup()
        subscribe_button = InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_ID}")
        keyboard.add(subscribe_button)

        await message.reply("Чтобы использовать бота, подпишитесь на наш канал.", reply_markup=keyboard)
        return

    # Если пользователь подписан, продолжаем обработку
    if "youtube.com" in message.text or "youtu.be" in message.text:
        try:
            yt = YouTube(message.text)
            keyboard = InlineKeyboardMarkup()

            # Добавляем кнопки для выбора форматов
            keyboard.add(
                InlineKeyboardButton("360p", callback_data=f"download|360p|{yt.watch_url}"),
                InlineKeyboardButton("480p", callback_data=f"download|480p|{yt.watch_url}"),
                InlineKeyboardButton("720p", callback_data=f"download|720p|{yt.watch_url}"),
                InlineKeyboardButton("1080p", callback_data=f"download|1080p|{yt.watch_url}")
            )

            await message.reply("Выберите качество видео:", reply_markup=keyboard)
        except Exception as e:
            logging.error(f"Ошибка обработки ссылки: {e}")
            await message.reply("Не удалось обработать ссылку. Проверьте её и попробуйте снова.")
    else:
        await message.reply("Пожалуйста, отправьте корректную ссылку на YouTube-видео.")

@dp.callback_query_handler(lambda c: c.data.startswith("download"))
async def handle_download_callback(callback_query: types.CallbackQuery):
    """Обработчик выбора формата для скачивания."""
    try:
        _, resolution, url = callback_query.data.split("|")
        yt = YouTube(url)

        # Выбираем поток с нужным разрешением
        stream = yt.streams.filter(res=resolution, file_extension="mp4").first()

        if not stream:
            await bot.answer_callback_query(callback_query.id, "Видео в этом качестве недоступно.", show_alert=True)
            return

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Начинаю загрузку...")

        # Загружаем видео и отправляем пользователю
        file_path = stream.download()

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            await bot.send_message(callback_query.from_user.id, "Видео слишком большое для отправки через Telegram.")
            os.remove(file_path)
            return

        try:
            async with aiofiles.open(file_path, mode='rb') as video:
                await bot.send_video(callback_query.from_user.id, video)
        except Exception as e:
            logging.error(f"Ошибка при отправке видео: {e}")
            await bot.send_message(callback_query.from_user.id, "Произошла ошибка при отправке видео.")
        finally:
            os.remove(file_path)  # Удаляем файл после отправки

    except Exception as e:
        logging.error(f"Ошибка загрузки видео: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при загрузке видео.")

async def on_startup(dp):
    """Действия при запуске бота."""
    logging.info("Starting webhook setup...")
    try:
        response = await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set successfully: {response}")
    except Exception as e:
        logging.error(f"Ошибка установки вебхука: {e}")

async def on_shutdown(dp):
    """Действия при остановке бота."""
    logging.info("Deleting webhook...")
    try:
        await bot.delete_webhook()
        logging.info("Webhook deleted successfully.")
    except Exception as e:
        logging.error(f"Ошибка удаления вебхука: {e}")

if __name__ == "__main__":
    # Запуск бота
    executor.start_webhook(
        dispatcher=dp,
        webhook_path="/webhook",  # Путь вебхука
        on_startup=on_startup,   # Функция, выполняемая при старте
        on_shutdown=on_shutdown,  # Функция, выполняемая при остановке
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),  # Порт передаётся в переменных окружения
        skip_updates=True,        # Пропустить старые обновления
    )

