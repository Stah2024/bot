import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from db.database import init_db
from handlers.start import get_main_keyboard
from handlers.settings import router as settings_router  # ← РОУТЕР С КНОПКАМИ
from handlers.repost import repost_channel_post

logging.basicConfig(level=logging.INFO)

init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ПОДПИСКА НА КАНАЛЫ ===
REQUIRED_CHANNELS = [-1001792603455, -1003347493013]  # ← ЗАМЕНИ НА СВОИ

async def check_subscription(user_id: int, bot: Bot) -> bool:
    for channel_id in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception as e:
            logging.warning(f"[SUBSCRIBE] Ошибка проверки канала {channel_id}: {e}")
            return False
    return True


# === /start ===
@dp.message(Command("start"))
async def start(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id, bot)
    if not is_subscribed:
        await message.answer(
            "Для использования бота нужно подписаться на оба канала:\n\n"
            "[Канал 1](https://t.me/your_channel_1)\n"
            "[Канал 2](https://t.me/your_channel_2)\n\n"
            "После подписки нажми /start снова.",
            parse_mode="Markdown"
        )
        return

    await message.answer(
        "Привет! Я репост-бот TG → VK\nВыбери действие:",
        reply_markup=get_main_keyboard()
    )


# === ПОДКЛЮЧАЕМ ВСЕ ХЕНДЛЕРЫ ИЗ settings.py ===
dp.include_router(settings_router)

# === РЕПОСТ ИЗ КАНАЛА ===
dp.channel_post.register(repost_channel_post)


# === ЗАПУСК ===
async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())