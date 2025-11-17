# handlers/settings.py
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.vk_client import validate_vk_token
from db.database import save_or_update_user, add_subscription
import logging

logger = logging.getLogger(__name__)
router = Router()


class ConnectStates(StatesGroup):
    waiting_vk_token = State()
    waiting_group_id = State()


# Привязка канала через пересланное сообщение
@router.message(F.forward_from_chat & F.forward_from_chat.type == "channel")
async def handle_forwarded_channel(message: types.Message, state: FSMContext):
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id

    await state.clear()
    await state.update_data(channel_id=channel_id)
    await message.answer(
        f"Отлично! Канал привязан.\n\n"
        "Теперь пришли токен VK:\n"
        "→ [Гайд: как получить токен за 1 минуту](https://teletype.in/@artstah/RQPCerHRJ3l)\n\n"
        "Жду токен (vk1.a...)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await state.set_state(ConnectStates.waiting_vk_token)


# Кнопка "Подключить"
@router.callback_query(F.data == "connect")
async def connect_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "Настройка подключения:\n\n"
        "1. Добавь бота в **Telegram-канал** как админа (чтение + посты)\n"
        "2. Перешли **любое сообщение из канала** в личку боту\n"
        "3. Получи **токен VK** по гайду:\n"
        "   → [Гайд: как получить токен](https://teletype.in/@artstah/RQPCerHRJ3l)\n"
        "4. Пришли токен → выбери группу → готово\n\n"
        "Репост с фото/видео будет работать!",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await call.answer()


# Получение VK токена
@router.message(ConnectStates.waiting_vk_token)
async def get_vk_token(message: types.Message, state: FSMContext):
    vk_token = message.text.strip()
    logger.info(f"[FSM] Получен VK токен от user {message.from_user.id}")

    check = validate_vk_token(vk_token)
    logger.info(f"[FSM] validate_vk_token: {check}")

    if "error" in check:
        await message.answer(
            f"Неверный токен:\n`{check['error']}`\n\n"
            "Попробуй снова:",
            parse_mode="Markdown"
        )
        return

    await state.update_data(vk_token=vk_token)

    groups = check.get("groups", [])
    if not groups:
        await message.answer("Ты не админ ни в одной группе. Введи ID вручную (без -):")
        await state.set_state(ConnectStates.waiting_group_id)
        return

    if len(groups) == 1:
        g = groups[0]
        await state.update_data(vk_group_id=f"-{g['id']}", group_name=g["name"])
        await message.answer(
            f"Группа найдена: `{g['name']}` (ID: {g['id']})\n\n"
            "Подтверди: напиши `да` или введи другой ID (без -)",
            parse_mode="Markdown"
        )
    else:
        kb = []
        for g in groups:
            kb.append([types.InlineKeyboardButton(
                text=f"{g['name']} ({g['id']})",
                callback_data=f"select_group:{g['id']}"
            )])
        kb.append([types.InlineKeyboardButton(text="Ввести вручную", callback_data="manual_group")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer("Выбери группу для репоста:", reply_markup=keyboard)
        await state.update_data(available_groups=groups)

    await state.set_state(ConnectStates.waiting_group_id)


# Выбор группы через кнопку
@router.callback_query(F.data.startswith("select_group:"))
async def select_group(call: types.CallbackQuery, state: FSMContext):
    group_id = call.data.split(":")[1]
    data = await state.get_data()
    groups = data.get("available_groups", [])
    group = next((g for g in groups if str(g['id']) == group_id), None)
    if group:
        await state.update_data(vk_group_id=f"-{group_id}", group_name=group["name"])
        await call.message.edit_text(
            f"Выбрана группа: `{group['name']}` (ID: {group_id})\n\n"
            "Готово! Репосты включены.",
            parse_mode="Markdown"
        )
    await call.answer()
    await finalize_connection(call.message, state)


# Ввод группы вручную
@router.callback_query(F.data == "manual_group")
async def manual_group(call: types.CallbackQuery):
    await call.message.edit_text("Введи ID группы ВК вручную (цифры без -):")
    await call.answer()


# Получение group_id (вручную или подтверждение)
@router.message(ConnectStates.waiting_group_id)
async def get_group_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    vk_token = data.get("vk_token")
    channel_id = data.get("channel_id")

    if not vk_token or not channel_id:
        await message.answer("Ошибка: данные потерялись. Начни заново с кнопки «Подключить»")
        await state.clear()
        return

    auto_id = data.get("vk_group_id")

    try:
        text = message.text.strip().lower()
        if text in ["да", "ok", "подтвердить", "yes", "готово"] and auto_id:
            group_id = auto_id
            group_name = data.get("group_name", "Моя группа")
        else:
            raw_id = int(text)
            group_id = f"-{raw_id}"
            group_name = f"Группа {raw_id}"
    except ValueError:
        await message.answer("ID должен быть числом. Попробуй ещё раз:")
        return

    await state.update_data(vk_group_id=group_id, group_name=group_name)
    await finalize_connection(message, state)


# Финализация — сохранение токена + добавление подписки
async def finalize_connection(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    vk_token = data["vk_token"]
    channel_id = data["channel_id"]
    group_id = data["vk_group_id"]
    group_name = data.get("group_name", "Группа ВК")

    try:
        # 1. Сохраняем/обновляем токен (один на пользователя)
        save_or_update_user(user_id, vk_token)

        # 2. Добавляем подписку (можно сколько угодно)
        success = add_subscription(
            telegram_id=user_id,
            tg_channel_id=channel_id,
            vk_group_id=int(group_id),
            vk_group_name=group_name
        )

        if success:
            await message.answer(
                f"Подключено!\n\n"
                f"Канал: `{channel_id}`\n"
                f"Группа ВК: `{group_id}` ({group_name})\n\n"
                f"Репосты запущены автоматически!",
                parse_mode="Markdown"
            )
            logger.info(f"УСПЕШНО: user={user_id} | {channel_id} → {group_id}")
        else:
            await message.answer("Такая связка уже существует — ничего не добавлено.")

    except Exception as e:
        logger.error(f"Ошибка финализации: {e}")
        await message.answer("Произошла ошибка. Попробуй позже.")

    await state.clear()