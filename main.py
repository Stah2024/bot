import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
from db.database import init_db
from handlers.start import get_main_keyboard
from handlers.settings import router as settings_router
from handlers.repost import repost_channel_post

logging.basicConfig(level=logging.INFO)

init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === КАНАЛЫ ДЛЯ ПОДПИСКИ ===
REQUIRED_CHANNELS = [
    {"id": -1001792603455, "username": "@your_channel_1", "name": "Канал 1"},
    {"id": -1003347493013, "username": "@your_channel_2", "name": "Канал 2"},
]

# === КНОПКИ ПОДПИСКИ ===
def get_subscribe_keyboard():
    kb = []
    for ch in REQUIRED_CHANNELS:
        kb.append([InlineKeyboardButton(
            text=f"Подписаться: {ch['name']}",
            url=f"https://t.me/{ch['username'].lstrip('@')}"
        )])
    kb.append([InlineKeyboardButton(text="Я подписался", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# === ПРОВЕРКА ПОДПИСКИ ===
async def check_subscription(user_id: int) -> bool:
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception as e:
            logging.warning(f"[SUBSCRIBE] Ошибка проверки канала {ch['id']}: {e}")
            return False
    return True

# === /start ===
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)

    if is_subscribed:
        await message.answer(
            "Привет! Я репост-бот TG → VK\n"
            "Выбери действие:",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Для использования бота подпишись на каналы:",
            reply_markup=get_subscribe_keyboard()
        )

# === КНОПКА "Я подписался" ===
@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.edit_text("Подписка подтверждена!")
        await call.message.answer(
            "Выбери действие:",
            reply_markup=get_main_keyboard()
        )
    else:
        await call.answer("Ты ещё не подписался на все каналы!", show_alert=True)

# === КНОПКА "Инструкция" ===
@dp.callback_query(lambda c: c.data == "help")
async def help_handler(call: types.CallbackQuery):
    help_text = (
        "Инструкция по подключению:\n\n"
        "1. Создай приложение:\n"
        "   → https://vk.com/apps?act=manage\n"
        "   → «Создать» → «Сайт»\n"
        "   → Название: любое\n"
        "   → Адрес: https://example.com\n"
        "   → Домен: example.com\n"
        "   → Сохранить\n\n"
        "2. Запиши ID приложения (например, 51778376)\n\n"
        "3. Открой ссылку (замени ID):\n"
        "   https://oauth.vk.com/authorize?client_id=51778376"
        "&scope=wall,photos,video,docs,groups,offline"
        "&response_type=token"
        "&redirect_uri=https://oauth.vk.com/blank.html&v=5.199\n\n"
        "4. Нажми «Разрешить»\n\n"
        "5. Скопируй токен из URL:\n"
        "   vk1.a.длинный_токен_до_&\n\n"
        "6. Перешли любое сообщение из канала боту\n"
        "7. Отправь токен → выбери группу → готово!\n\n"
        "Фото, видео, текст — будут в ВК!"
    )
    await call.message.edit_text(help_text, parse_mode="Markdown", disable_web_page_preview=True)

# === ПОДКЛЮЧАЕМ ХЕНДЛЕРЫ ===
dp.include_router(settings_router)
dp.channel_post.register(repost_channel_post)

# === ЗАПУкуда ===
async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())