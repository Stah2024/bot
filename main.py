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
    {
        "id": -1001792603455,
        "username": "@newsSVOih",
        "name": "🇷🇺Новости для своих📲"
    },
    {
        "id": -1003347493013,
        "username": "@bot_tg2vc",
        "name": "Боты ТГ"
    }
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
            logging.warning(f"[SUBSCRIBE] Ошибка проверки {ch['id']}: {e}")
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
    await call.message.edit_text(
        "Полный гайд по подключению:\n\n"
        "[Гайд: как настроить репост TG → VK](https://teletype.in/@artstah/RQPCerHRJ3l)\n\n"
        "1. Добавь бота в канал как админа\n"
        "2. Перешли любое сообщение\n"
        "3. Получи токен по гайду\n"
        "4. Пришли токен → выбери группу",
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
        ])
    )

# === КНОПКА "Поддержка" ===
@dp.callback_query(lambda c: c.data == "support")
async def support_handler(call: types.CallbackQuery):
    await call.message.edit_text(
        "Поддержка:\n\n"
        "По всем вопросам — @artstah\n"
        "Пиши в личку, помогу с настройкой!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")]
        ])
    )

# === КНОПКА "Назад" ===
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "Выбери действие:",
        reply_markup=get_main_keyboard()
    )

# === ЛОВИМ ОШИБКИ И ШЛЁМ ТЕБЕ ===
YOUR_ID = 5127280245  # ← ЗАМЕ BIT НА СВОЙ ID (узнай через @userinfobot)

@dp.errors()
async def error_handler(event: types.ErrorEvent):
    error = event.exception
    user = None
    if event.update.message:
        user = event.update.message.from_user
    elif event.update.callback_query:
        user = event.update.callback_query.from_user

    text = (
        f"ОШИБКА В БОТЕ\n\n"
        f"Пользователь: {user.full_name if user else 'Неизвестно'} (@{user.username if user else '—'}) ID: {user.id if user else '—'}\n"
        f"Ошибка: {error}\n"
        f"Тип: {type(error).__name__}"
    )
    try:
        await bot.send_message(YOUR_ID, text)
    except:
        pass

# === ПОДКЛЮЧАЕМ ХЕНДЛЕРЫ ===
dp.include_router(settings_router)
dp.channel_post.register(repost_channel_post)

# === ЗАПУСК ===
async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())