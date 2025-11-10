from aiogram import types

def get_main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Подключить", callback_data="connect"),
        types.InlineKeyboardButton("Оплатить", callback_data="pay"),
        types.InlineKeyboardButton("Инструкция", callback_data="help")
    )
    return kb