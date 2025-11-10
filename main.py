import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот жив! Тест через GitHub Actions.\nНапиши /test")

@dp.message(Command("test"))
async def test(message: types.Message):
    await message.answer("Работает! Version 3.x")

async def main():
    print("Bot started in GitHub Actions...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())