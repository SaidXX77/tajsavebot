from aiogram import Bot, Dispatcher, executor
from aiogram.types import Update
import logging

TOKEN = "7341799826:AAFS-TMnZIEhbV8ZV2QB5X-DelfMl4skKaE"
WEBHOOK_URL = "https://<tajsavebot-2>.onrender.com/webhook"  # Укажите URL вашего хоста

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message):
    await message.reply("Hello! I'm running on Webhook!")

async def on_startup(dp):
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Ошибка установки вебхука: {e}")

async def on_shutdown(dp):
    try:
        await bot.delete_webhook()
        logging.info("Webhook удалён")
    except Exception as e:
        logging.error(f"Ошибка удаления вебхука: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_webhook(
        dispatcher=dp,
        webhook_path="/webhook",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
    )
