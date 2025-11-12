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


# Привязка канала через пересланное сообщение
@router.message(lambda m: m.forward_from_chat and m.forward_from_chat.type == "channel")
async def handle_forwarded_channel(message: types.Message, state: FSMContext):
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id

    await state.clear()
    await state.update_data(channel_id=channel_id)
    await message.answer(
        f"Канал `{channel_id}` обнаружен и привязан.\n\n"
        "Теперь пришли **standalone-токен** (user access token):\n\n"
        "1. https://vk.com/apps?act=manage → Создать → Web\n"
        "2. Адрес: `https://example.com`, домен: `example.com`\n"
        "3. Сохранить → запиши ID\n"
        "4. Открой: https://oauth.vk.com/authorize?client_id=ТВОЙ_ID&scope=wall,photos,video,docs,groups,offline&response_type=token&redirect_uri=https://oauth.vk.com/blank.html&v=5.199\n"
        "5. Разрешить → скопируй токен (vk1.a...)\n\n"
        "Пришли его сюда:",
        parse_mode="Markdown"
    )
    await state.set_state(ConnectStates.waiting_vk_token)


# Кнопка "Подключить"
@router.callback_query(lambda c: c.data == "connect")
async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "Настройка подключения:\n\n"
        "1. Добавь бота в **Telegram-канал** как админа (чтение + посты)\n"
        "2. Перешли **любое сообщение из канала** в личку боту\n"
        "3. Создай **standalone-токен**:\n"
        "   → https://vk.com/apps?act=manage → Web → example.com\n"
        "   → Получи токен по ссылке (vk1.a...)\n"
        "4. Пришли токен → бот сам покажет твои группы\n"
        "5. Выбери группу → готово\n\n"
        "После этого репост с фото/видео будет работать!"
    )
    await call.answer()


# Получение VK токена (standalone)
@router.message(ConnectStates.waiting_vk_token)
async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    logger.info(f"[FSM] Получен VK токен от user {message.from_user.id}")

    # Проверяем standalone-токен
    check = validate_vk_token(vk_token)
    logger.info(f"[FSM] validate_vk_token: {check}")

    if "error" in check:
        await message.answer(
            f"Неверный токен:\n`{check['error']}`\n\n"
            "Попробуй снова:",
            parse_mode="Markdown"
        )
        return

    # Сохраняем токен
    await state.update_data(vk_token=vk_token)

    # Получаем группы, где пользователь — админ
    groups = check.get("groups", [])
    if not groups:
        await message.answer("Ты не админ ни в одной группе. Введи ID вручную (без -):")
        await state.set_state(ConnectStates.waiting_group_id)
        return

    if len(groups) == 1:
        # Одна группа — авто
        g = groups[0]
        await state.update_data(vk_group_id=f"-{g['id']}", group_name=g["name"])
        await message.answer(
            f"Группа найдена: `{g['name']}` (ID: {g['id']})\n\n"
            "Подтверди: напиши `да` или введи другой ID (без -)",
            parse_mode="Markdown"
        )
    else:
        # Несколько групп — выбор
        kb = []
        for g in groups:
            kb.append([types.InlineKeyboardButton(
                text=f"{g['name']} ({g['id']})",
                callback_data=f"select_group:{g['id']}"
            )])
        kb.append([types.InlineKeyboardButton(text="Ввести вручную", callback_data="manual_group")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(
            "Выбери группу для репоста:",
            reply_markup=keyboard
        )
        await state.update_data(available_groups=groups)

    await state.set_state(ConnectStates.waiting_group_id)


# Выбор группы из списка
@router.callback_query(lambda c: c.data.startswith("select_group:"))
async def select_group(call: types.CallbackQuery, state: FSMContext):
    group_id = call.data.split(":")[1]
    data = await state.get_data()
    groups = data.get("available_groups", [])
    group = next((g for g in groups if g["id"] == group_id), None)
    if group:
        await state.update_data(vk_group_id=f"-{group_id}", group_name=group["name"])
        await call.message.edit_text(
            f"Выбрана: `{group['name']}` (ID: {group_id})\n\n"
            "Теперь всё готово!",
            parse_mode="Markdown"
        )
    await call.answer()
    await finalize_connection(call.message, state)


# Ввод вручную
@router.callback_query(lambda c: c.data == "manual_group")
async def manual_group(call: types.CallbackQuery):
    await call.message.edit_text("Введи ID группы ВК вручную (без -):")
    await call.answer()


# Получение group_id и сохранение
@router.message(ConnectStates.waiting_group_id)
async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vk_token = data.get("vk_token")
    channel_id = data.get("channel_id")

    if not vk_token or not channel_id:
        await message.answer("Ошибка: данные потеряны. Начни заново.")
        await state.clear()
        return

    # Авто-ID из токена
    auto_id = data.get("vk_group_id")

    try:
        input_text = message.text.strip()
        if input_text.lower() in ["да", "ok", "подтвердить"] and auto_id:
            group_id = auto_id
        else:
            raw_id = int(input_text)
            group_id = f"-{raw_id}"
    except ValueError:
        await message.answer("ID должен быть числом. Попробуй ещё:")
        return

    await finalize_connection(message, state, group_id)


# Финализация (общая функция)
async def finalize_connection(message: types.Message, state: FSMContext, group_id=None):
    data = await state.get_data()
    vk_token = data["vk_token"]
    channel_id = data["channel_id"]
    group_id = group_id or data.get("vk_group_id")

    try:
        encrypted_token = encrypt(vk_token)
        save_user_tokens(
            user_id=message.from_user.id,
            vk_token=encrypted_token,
            group_id=group_id,
            channel_id=channel_id
        )
        logger.info(f"Сохранено: user={message.from_user.id}, группа={group_id}, канал={channel_id}")
        await message.answer(
            f"Подключено!\n\n"
            f"VK: `{group_id}`\n"
            f"TG: `{channel_id}`\n\n"
            "Репост с фото/видео начнётся автоматически.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Ошибка сохранения. Попробуй позже.")

    await state.clear()