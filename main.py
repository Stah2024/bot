import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from db.database import init_db, get_user_tokens, save_user_tokens
from utils.crypto import encrypt
from handlers.start import get_main_keyboard
from handlers.settings import (
    connect_callback, get_vk_token,
    get_group_id, ConnectStates
)
from handlers.repost import repost_channel_post

logging.basicConfig(level=logging.INFO)

init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🔒 ID каналов, на которые обязательна подписка
REQUIRED_CHANNELS = [-1001234567890, -1009876543210]  # ← замени на свои ID

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

@dp.message(Command("start"))
async def start(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id, bot)
    if not is_subscribed:
        await message.answer(
            "🚫 Для использования бота нужно подписаться на оба канала:\n\n"
            "📢 [Канал 1](https://t.me/your_channel_1)\n"
            "📢 [Канал 2](https://t.me/your_channel_2)\n\n"
            "После подписки нажми /start снова.",
            parse_mode="Markdown"
        )
        return

    await message.answer(
        "Привет! Я репост-бот TG → VK\nВыбери действие:",
        reply_markup=get_main_keyboard()
    )

# FSM: настройка VK
dp.callback_query.register(connect_callback, lambda c: c.data == "connect")
dp.message.register(get_vk_token, ConnectStates.waiting_vk_token)
dp.message.register(get_group_id, ConnectStates.waiting_group_id)

# Репост из канала (бот как админ)
dp.channel_post.register(repost_channel_post)

# Привязка канала через пересланное сообщение
@dp.message(lambda m: m.forward_from_chat and m.forward_from_chat.type == "channel")
async def handle_forwarded_channel(message: types.Message, state):
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id

    await state.clear()
    await state.update_data(channel_id=channel_id)
    await message.answer(
        f"Канал `{channel_id}` обнаружен и привязан к вашему аккаунту.\n\n"
        "Теперь введи Community Token ВК:"
    )
    await state.set_state(ConnectStates.waiting_vk_token)

# 🔒 Заглушка для кнопки оплаты
@dp.callback_query(lambda c: c.data == "pay")
async def pay_callback(call: types.CallbackQuery):
    await call.message.answer(
        "🔓 Бот сейчас условно бесплатный.\n\n"
        "💡 В будущем будет символическая подписка.\n"
        "📌 Поддержка проекта приветствуется, но не обязательна."
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "help")
async def help_callback(call: types.CallbackQuery):
    await call.message.answer(
        "📌 Инструкция:\n\n"
        "1. Нажми «Подключить»\n"
        "2. Введи VK Community Token\n"
        "3. Укажи ID группы ВКонтакте\n"
        "4. Перешли сообщение из канала, где бот — админ\n\n"
        "После этого бот начнёт репостить из канала в VK."
    )
    await call.answer()

async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())