import requests
import logging

VK_API_VERSION = "5.199"
logging.basicConfig(level=logging.INFO)

def validate_vk_token(token: str) -> dict:
    try:
        response = requests.get(
            "https://api.vk.com/method/groups.getById",
            params={"access_token": token, "v": VK_API_VERSION},
            timeout=10
        )
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}
        data = response.json()
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
        data = response.json()
        print("[VK] validate_vk_token (standalone) ответ:", data)
        if "error" in data:
            return {"error": data["error"].get("error_msg", "Unknown error")}
        items = data.get("response", {}).get("items", [])
        if not items:
            return {"error": "Нет групп, где вы админ"}
        groups = [{"id": str(g["id"]), "name": g["name"]} for g in items]
        return {"ok": True, "groups": groups, "type": "standalone"}
    except Exception as e:
        logging.error(f"[validate_vk_token] Критическая ошибка: {e}")
        return {"error": "Сеть/таймаут"}

def post_to_vk(token: str, group_id: str | int, text: str, attachments: list = None) -> dict:
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
        response = requests.post("https://api.vk.com/method/wall.post", data=data, timeout=15)
        if response.status_code != 200:
            logging.error(f"[post_to_vk] HTTP {response.status_code}: {response.text}")
            return {"error": f"HTTP {response.status_code}"}
        result = response.json()
        if "error" in result:
            logging.error(f"[post_to_vk] VK Error {result['error']['error_code']}: {result['error']['error_msg']}")
            return result
        post_id = result.get("response", {}).get("post_id")
        logging.info(f"[post_to_vk] Успешно: post_id = {post_id}")
        return result
    except Exception as e:
        logging.error(f"[post_to_vk] Критическая ошибка: {e}")
        return {"error": str(e)}

def upload_photo_to_vk(token: str, group_id: str | int, file_url: str) -> str | None:
    group_id_str = str(group_id).lstrip("-")
    try:
        upload_server_resp = requests.get(
            "https://api.vk.com/method/photos.getWallUploadServer",
            params={"group_id": group_id_str, "access_token": token, "v": VK_API_VERSION},
            timeout=10
        )
        data = upload_server_resp.json()
        if "error" in data:
            logging.error(f"[upload_photo] Ошибка getWallUploadServer: {data['error']}")
            return None
        upload_url = data["response"]["upload_url"]
        photo_data = requests.get(file_url, timeout=15).content
        if not photo_data:
            logging.warning("[upload_photo] Фото пустое")
            return None
        upload_resp = requests.post(
            upload_url,
            files={"photo": ("photo.jpg", photo_data, "image/jpeg")},
            timeout=15
        )
        upload_data = upload_resp.json()
        if "photo" not in upload_data:
            logging.error(f"[upload_photo] Ошибка загрузки: {upload_data}")
            return None
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
        save_data = save_resp.json()
        if "error" in save_data:
            logging.error(f"[upload_photo] Ошибка saveWallPhoto: {save_data['error']}")
            return None
        photo = save_data["response"][0]
        return f"photo{photo['owner_id']}_{photo['id']}"
    except Exception as e:
        logging.error(f"[upload_photo_to_vk] Критическая ошибка: {e}")
        return None

def upload_video_to_vk(token: str, group_id: str | int, file_url: str) -> str | None:
    group_id_str = str(group_id).lstrip("-")
    try:
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
        save_data = save_resp.json()
        if "error" in save_data:
            logging.error(f"[upload_video] Ошибка video.save: {save_data['error']}")
            return None
        upload_url = save_data["response"]["upload_url"]
        owner_id = save_data["response"]["owner_id"]
        video_id = save_data["response"]["video_id"]
        video_data = requests.get(file_url, timeout=30).content
        if len(video_data) > 25 * 1024 * 1024:
            logging.warning("[upload_video] Видео >25MB — пропускаем")
            return None
        upload_resp = requests.post(
            upload_url,
            files={"video_file": ("video.mp4", video_data, "video/mp4")},
            timeout=60
        )
        try:
            upload_result = upload_resp.json()
        except ValueError:
            logging.error("[upload_video] Ответ не JSON")
            return None
        if "response" not in upload_result and "video_id" not in upload_result:
            logging.warning("[upload_video] VK не подтвердил загрузку")
            return None
        return f"video{owner_id}_{video_id}"
    except Exception as e:
        logging.error(f"[upload_video_to_vk] Критическая ошибка: {e}")
        return None