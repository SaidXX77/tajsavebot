from aiogram import Bot, Dispatcher, executor
from aiogram.types import Update
import logging

# Токен вашего бота
TOKEN = "7341799826:AAFS-TMnZIEhbV8ZV2QB5X-DelfMl4skKaE"
# URL вебхука (замените tajsavebot-2 на ваш Render хост)
WEBHOOK_URL = "https://tajsavebot-2.onrender.com/webhook"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Логирование
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def start_handler(message):
    """Обработчик команды /start."""
    await message.reply("Hello! I'm running on Webhook!")


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
        skip_updates=True,        # Пропустить старые обновления
    )
