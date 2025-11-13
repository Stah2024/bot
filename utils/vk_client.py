import requests
import logging

VK_API_VERSION = "5.199"
logging.basicConfig(level=logging.INFO)


def validate_vk_token(token: str) -> dict:
    """Проверяет любой токен: сервисный (Community) или standalone (User)"""
    try:
        # === 1. Пробуем как СЕРВИСНЫЙ токен (groups.getById) ===
        response = requests.get(
            "https://api.vk.com/method/groups.getById",
            params={"access_token": token, "v": VK_API_VERSION},
            timeout=10
        )

        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}

        try:
            data = response.json()
        except ValueError:
            return {"error": "Invalid JSON"}

        print("[VK] validate_vk_token (сервисный) ответ:", data)

        if "error" not in data and data.get("response", {}).get("groups"):
            groups = data["response"]["groups"]
            if groups:
                g = groups[0]
                return {
                    "ok": True,
                    "group_id": str(g["id"]),
                    "name": g["name"],
                    "type": "service"
                }

        # === 2. Пробуем как STANDALONE токен (groups.get + filter=admin) ===
        response = requests.get(
            "https://api.vk.com/method/groups.get",
            params={
                "access_token": token,
                "v": VK_API_VERSION,
                "extended": 1,
                "filter": "admin",
                "fields": "name"
            },
            timeout=10
        )

        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}

        try:
            data = response.json()
        except ValueError:
            return {"error": "Invalid JSON"}

        print("[VK] validate_vk_token (standalone) ответ:", data)

        if "error" in data:
            err = data["error"]
            return {"error": err.get("error_msg", "Unknown error")}

        items = data.get("response", {}).get("items", [])
        if not items:
            return {"error": "Нет групп, где вы админ"}

        groups = [{"id": str(g["id"]), "name": g["name"]} for g in items]
        return {
            "ok": True,
            "groups": groups,
            "type": "standalone"
        }

    except Exception as e:
        logging.error(f"[validate_vk_token] Критическая ошибка: {e}")
        return {"error": "Сеть/таймаут"}


def post_to_vk(token: str, group_id: str | int, text: str, attachments: list = None) -> dict:
    """Публикует пост в VK через POST (избегаем 414)"""
    if attachments is None:
        attachments = []

    group_id_str = str(group_id)

    try:
        data = {
            "owner_id": group_id_str,
            "from_group": 1,
            "message": text[:4096],
            "access_token": token,
            "v": VK_API_VERSION
        }
        if attachments:
            data["attachments"] = ",".join(attachments)

        print("[VK] Публикуем пост (POST):", data)

        response = requests.post(
            "https://api.vk.com/method/wall.post",
            data=data,  # POST, не params!
            timeout=15
        )

        if response.status_code != 200:
            logging.error(f"[post_to_vk] HTTP {response.status_code}: {response.text}")
            return {"error": f"HTTP {response.status_code}"}

        try:
            result = response.json()
        except ValueError:
            logging.error(f"[post_to_vk] Не JSON: {response.text}")
            return {"error": "Invalid JSON from VK"}

        if "error" in result:
            err = result["error"]
            logging.error(f"[post_to_vk] VK Error {err['error_code']}: {err['error_msg']}")
            return result

        post_id = result.get("response", {}).get("post_id")
        logging.info(f"[post_to_vk] Успешно: post_id = {post_id}")
        return result

    except Exception as e:
        logging.error(f"[post_to_vk] Критическая ошибка: {e}")
        return {"error": str(e)}


def upload_photo_to_vk(token: str, group_id: str | int, file_url: str) -> str | None:
    """Загружает фото из URL → возвращает 'photo123_456'"""
    group_id_str = str(group_id).lstrip("-")

    try:
        # 1. Получаем сервер
        upload_server_resp = requests.get(
            "https://api.vk.com/method/photos.getWallUploadServer",
            params={
                "group_id": group_id_str,
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=10
        )

        if upload_server_resp.status_code != 200:
            logging.error(f"[upload_photo] HTTP {upload_server_resp.status_code}")
            return None

        try:
            data = upload_server_resp.json()
        except ValueError:
            return None

        if "error" in data:
            logging.error(f"[upload_photo] Ошибка getWallUploadServer: {data['error']}")
            return None

        upload_url = data["response"]["upload_url"]

        # 2. Скачиваем фото
        photo_data = requests.get(file_url, timeout=15).content
        if not photo_data:
            logging.warning("[upload_photo] Фото пустое")
            return None

        # 3. Загружаем на сервер VK
        upload_resp = requests.post(
            upload_url,
            files={"photo": ("photo.jpg", photo_data, "image/jpeg")},
            timeout=15
        )

        if upload_resp.status_code != 200:
            logging.error(f"[upload_photo] Загрузка: {upload_resp.text}")
            return None

        try:
            upload_data = upload_resp.json()
        except ValueError:
            return None

        if "photo" not in upload_data:
            logging.error(f"[upload_photo] Ошибка загрузки: {upload_data}")
            return None

        # 4. Сохраняем
        save_resp = requests.get(
            "https://api.vk.com/method/photos.saveWallPhoto",
            params={
                "group_id": group_id_str,
                "photo": upload_data["photo"],
                "server": upload_data["server"],
                "hash": upload_data["hash"],
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=10
        )

        if save_resp.status_code != 200:
            logging.error(f"[upload_photo] saveWallPhoto HTTP {save_resp.status_code}")
            return None

        try:
            save_data = save_resp.json()
        except ValueError:
            return None

        if "error" in save_data:
            logging.error(f"[upload_photo] Ошибка saveWallPhoto: {save_data['error']}")
            return None

        photo = save_data["response"][0]
        photo_id = f"photo{photo['owner_id']}_{photo['id']}"
        logging.info(f"[upload_photo] Успешно: {photo_id}")
        return photo_id

    except Exception as e:
        logging.error(f"[upload_photo_to_vk] Критическая ошибка: {e}")
        return None


def upload_video_to_vk(token: str, group_id: str | int, file_url: str) -> str | None:
    """Загружает видео из URL → возвращает 'video123_456'"""
    group_id_str = str(group_id).lstrip("-")

    try:
        # 1. Получаем upload_url
        save_resp = requests.get(
            "https://api.vk.com/method/video.save",
            params={
                "group_id": group_id_str,
                "name": "Репост из Telegram",
                "wallpost": 1,
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=10
        )

        if save_resp.status_code != 200:
            logging.error(f"[upload_video] HTTP {save_resp.status_code}")
            return None

        try:
            save_data = save_resp.json()
        except ValueError:
            return None

        if "error" in save_data:
            logging.error(f"[upload_video] Ошибка video.save: {save_data['error']}")
            return None

        upload_url = save_data["response"]["upload_url"]

        # 2. Скачиваем видео
        video_data = requests.get(file_url, timeout=30).content
        if len(video_data) > 25 * 1024 * 1024:
            logging.warning("[upload_video] Видео >25MB — пропускаем")
            return None

        # 3. Загружаем
        upload_resp = requests.post(
            upload_url,
            files={"video_file": ("video.mp4", video_data, "video/mp4")},
            timeout=60
        )

        if upload_resp.status_code != 200:
            logging.error(f"[upload_video] Ошибка загрузки: {upload_resp.text}")
            return None

        # 4. Берём ID
        owner_id = save_data["response"]["owner_id"]
        video_id = save_data["response"]["video_id"]
        video_str = f"video{owner_id}_{video_id}"
        logging.info(f"[upload_video] Успешно: {video_str}")
        return video_str

    except Exception as e:
        logging.error(f"[upload_video_to_vk] Критическая ошибка:ed: {e}")
        return None