user_db = {}

def save_user_tokens(user_id, tg_token, vk_token):
    user_db[user_id] = {"tg_token": tg_token, "vk_token": vk_token}
    print(f"Сохранено для {user_id}")
