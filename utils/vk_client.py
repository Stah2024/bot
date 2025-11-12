import requests
import logging

VK_API_VERSION = "5.199"
logging.basicConfig(level=logging.INFO)

def validate_vk_token(token: str) -> dict:
    """Проверяет токен: возвращает ID группы и имя"""
    try:
        response = requests.get(
            "https://api.vk.com/method/groups.getById",
            params={"access_token": token, "v": VK_API_VERSION},
            timeout=10
        ).json()

        print("[VK] validate_vk_token ответ:", response)

        if "error" in response:
            err = response["error"]
            return {"error": err.get("error_msg", "Unknown error")}

        groups = response.get("response", {}).get("groups", [])
        if not groups:
            return {"error": "Группа не найдена"}

        group = groups[0]
        return {
            "ok": True,
            "group_id": str(group["id"]),
            "name": group["name"]
        }

    except Exception as e:
        logging.error(f"[validate_vk_token] Критическая ошибка: {e}")
        return {"error": f"Сеть/таймаут: {str(e)}"}


def post_to_vk(token: str, group_id: str, text: str, attachments: list = None) -> dict:
    """Публикует пост в VK. attachments — список строк типа 'photo123_456'"""
    if attachments is None:
        attachments = []

    try:
        params = {
            "owner_id": group_id,
            "from_group": 1,
            "message": text[:4096],  # ← VK лимит
            "access_token": token,
            "v": VK_API_VERSION
        }
        if attachments:
            params["attachments"] = ",".join(attachments)

        response = requests.post(
            "https://api.vk.com/method/wall.post",
            params=params,
            timeout=15
        ).json()

        if "error" in response:
            err = response["error"]
            logging.error(f"[post_to_vk] Ошибка {err['error_code']}: {err['error_msg']}")
        else:
            post_id = response.get("response", {}).get("post_id")
            logging.info(f"[post_to_vk] Успешно: post_id = {post_id}")

        return response

    except Exception as e:
        logging.error(f"[post_to_vk] Критическая ошибка: {e}")
        return {"error": str(e)}


def upload_photo_to_vk(token: str, group_id: str, file_url: str) -> str | None:
    """Загружает фото из URL → возвращает 'photo123_456'"""
    try:
        # 1. Получаем сервер
        upload_server_resp = requests.get(
            "https://api.vk.com/method/photos.getWallUploadServer",
            params={
                "group_id": group_id.lstrip("-"),
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=10
        ).json()

        if "error" in upload_server_resp:
            logging.error(f"[upload_photo] Ошибка getWallUploadServer: {upload_server_resp['error']}")
            return None

        upload_url = upload_server_resp["response"]["upload_url"]

        # 2. Скачиваем фото из TG
        photo_data = requests.get(file_url, timeout=15).content
        if not photo_data:
            logging.warning("[upload_photo] Фото пустое")
            return None

        # 3. Загружаем на сервер VK
        upload_resp = requests.post(
            upload_url,
            files={"photo": ("photo.jpg", photo_data, "image/jpeg")},
            timeout=15
        ).json()

        if "photo" not in upload_resp:
            logging.error(f"[upload_photo] Ошибка загрузки: {upload_resp}")
            return None

        # 4. Сохраняем
        save_resp = requests.get(
            "https://api.vk.com/method/photos.saveWallPhoto",
            params={
                "group_id": group_id.lstrip("-"),
                "photo": upload_resp["photo"],
                "server": upload_resp["server"],
                "hash": upload_resp["hash"],
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=10
        ).json()

        if "error" in save_resp:
            logging.error(f"[upload_photo] Ошибка saveWallPhoto: {save_resp['error']}")
            return None

        photo = save_resp["response"][0]
        photo_id = f"photo{photo['owner_id']}_{photo['id']}"
        logging.info(f"[upload_photo] Успешно: {photo_id}")
        return photo_id

    except Exception as e:
        logging.error(f"[upload_photo_to_vk] Критическая ошибка: {e}")
        return None


def upload_video_to_vk(token: str, group_id: str, file_url: str) -> str | None:
    """Загружает видео из URL → возвращает 'video123_456'"""
    try:
        # 1. Получаем upload_url
        save_resp = requests.get(
            "https://api.vk.com/method/video.save",
            params={
                "group_id": group_id.lstrip("-"),
                "name": "Репост из Telegram",
                "wallpost": 1,  # ← сразу прикрепить к стене
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=10
        ).json()

        if "error" in save_resp:
            logging.error(f"[upload_video] Ошибка video.save: {save_resp['error']}")
            return None

        upload_url = save_resp["response"]["upload_url"]

        # 2. Скачиваем видео
        video_data = requests.get(file_url, timeout=30).content
        if len(video_data) > 25 * 1024 * 1024:  # >25MB — VK не примет
            logging.warning("[upload_video] Видео >25MB — пропускаем")
            return None

        # 3. Загружаем
        upload_resp = requests.post(
            upload_url,
            files={"video_file": ("video.mp4", video_data, "video/mp4")},
            timeout=60  # видео долго
        )

        if upload_resp.status_code != 200:
            logging.error(f"[upload_video] Ошибка загрузки: {upload_resp.text}")
            return None

        # 4. Видео уже сохранено — берём ID
        owner_id = save_resp["response"]["owner_id"]
        video_id = save_resp["response"]["video_id"]
        video_str = f"video{owner_id}_{video_id}"
        logging.info(f"[upload_video] Успешно: {video_str}")
        return video_str

    except Exception as e:
        logging.error(f"[upload_video_to_vk] Критическая ошибка: {e}")
        return None