from aiogram import Bot, Dispatcher, executor
from aiogram.types import Update
import logging

TOKEN = "7341799826:AAFS-TMnZIEhbV8ZV2QB5X-DelfMl4skKaE"
WEBHOOK_URL = "https://<your-host>.onrender.com/webhook"  # Укажите URL вашего хоста

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message):
    await message.reply("Hello! I'm running on Webhook!")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_webhook(
        dispatcher=dp,
        webhook_path="/webhook",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
    )
