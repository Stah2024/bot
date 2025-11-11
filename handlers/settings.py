from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.crypto import encrypt
from utils.vk_client import validate_vk_token
from db.database import save_user_tokens
import logging

logger = logging.getLogger(__name__)

class ConnectStates(StatesGroup):
    waiting_vk_token = State()
    waiting_group_id = State()

async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Введи Community Token ВК:")
    await state.set_state(ConnectStates.waiting_vk_token)
    await call.answer()

async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    check = validate_vk_token(vk_token)

    if "error" in check:
        await message.answer("Неверный VK токен. Попробуй ещё:")
        return

    await state.update_data(vk_token=vk_token)
    await message.answer("VK токен принят!\n\nТеперь введи ID группы ВКонтакте (без минуса):")
    await state.set_state(ConnectStates.waiting_group_id)

async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vk_token = data.get("vk_token")

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
        channel_id = message.chat.id if message.chat.type == "channel" else None

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