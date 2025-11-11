from aiogram import types, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.crypto import encrypt
from utils.vk_client import validate_vk_token
from db.database import save_user_tokens
import logging

logger = logging.getLogger(__name__)
router = Router()

class ConnectStates(StatesGroup):
    waiting_vk_token = State()
    waiting_group_id = State()

# Вариант 1: пересланное сообщение из канала
@router.message(lambda m: m.forward_from_chat and m.forward_from_chat.type == "channel")
async def handle_forwarded_channel(message: types.Message, state: FSMContext):
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id

    await state.clear()
    await state.update_data(channel_id=channel_id)
    await message.answer(
        f"Канал `{channel_id}` обнаружен и привязан к вашему аккаунту.\n\n"
        "Теперь введи Community Token ВК:"
    )
    await state.set_state(ConnectStates.waiting_vk_token)

# Вариант 2: бот добавлен в канал как админ
@router.channel_post()
async def handle_channel_post(message: types.Message):
    channel_id = message.chat.id
    logger.info(f"[CHANNEL POST] Получено сообщение из канала {channel_id}")
    # Здесь можно логировать или отправить сообщение в лог-чат

# Кнопка "Привязать канал" (например, inline-кнопка)
@router.callback_query(lambda c: c.data == "connect")
async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Введи Community Token ВК:")
    await state.set_state(ConnectStates.waiting_vk_token)
    await call.answer()

# Получение VK токена
@router.message(ConnectStates.waiting_vk_token)
async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    check = validate_vk_token(vk_token)

    if "error" in check:
        await message.answer("Неверный VK токен. Попробуй ещё:")
        return

    await state.update_data(vk_token=vk_token)
    await message.answer("VK токен принят!\n\nТеперь введи ID группы ВКонтакте (без минуса):")
    await state.set_state(ConnectStates.waiting_group_id)

# Получение VK group_id и сохранение связки
@router.message(ConnectStates.waiting_group_id)
async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vk_token = data.get("vk_token")
    channel_id = data.get("channel_id") or (
        message.chat.id if message.chat.type == "channel" else None
    )

    if not vk_token or not isinstance(vk_token, str):
        await message.answer("Ошибка: данные повреждены. Начни заново: /start")
        await state.clear()
        return

    try:
        group_id_input = int(message.text.strip())
    except ValueError:
        await message.answer("ID группы должен быть числом. Попробуй ещё:")
        return

    vk_group_id = f"-{group_id_input}"

    try:
        encrypted_vk = encrypt(vk_token)

        save_user_tokens(
            user_id=message.from_user.id,
            vk_token=encrypted_vk,
            group_id=vk_group_id,
            channel_id=channel_id
        )

        logger.info(f"Токены сохранены: user_id={message.from_user.id}, группа={vk_group_id}, канал={channel_id}")

        await message.answer(
            f"Все данные сохранены и зашифрованы!\n\n"
            f"VK Group ID: {group_id_input}\n\n"
            "7 дней бесплатно. Дальше — 200 ₽ или 100 ⭐"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await message.answer("Ошибка при сохранении. Попробуй позже.")

    await state.clear()