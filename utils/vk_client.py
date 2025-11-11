import requests

VK_API_VERSION = "5.199"

def validate_vk_token(token: str) -> dict:
    try:
        response = requests.get(
            "https://api.vk.com/method/groups.getById",
            params={"access_token": token, "v": VK_API_VERSION},
            timeout=5
        ).json()

        print("[VK] Ответ от VK API:", response)

        if "error" in response:
            return {"error": response["error"]["error_msg"]}

        group = response["groups"][0]
        return {
            "ok": True,
            "group_id": str(group["id"]),
            "name": group["name"]
        }
    except Exception as e:
        return {"error": str(e)}

def post_to_vk(token: str, group_id: str, text: str, attachments: list = []) -> dict:
    try:
        response = requests.post(
            "https://api.vk.com/method/wall.post",
            params={
                "owner_id": group_id,
                "message": text,
                "attachments": ",".join(attachments) if attachments else None,
                "access_token": token,
                "v": VK_API_VERSION
            },
            timeout=5
        ).json()

        if "error" in response:
            print("[VK] Ошибка wall.post:", response["error"])
        else:
            print("[VK] Успешно опубликовано:", response)

        return response
    except Exception as e:
        print(f"[post_to_vk] Error: {e}")
        return {"error": str(e)}

def upload_photo_to_vk(token: str, group_id: str, file_url: str) -> str | None:
    try:
        upload_server = requests.get(
            "https://api.vk.com/method/photos.getWallUploadServer",
            params={"group_id": group_id.lstrip("-"), "access_token": token, "v": VK_API_VERSION}
        ).json()

        upload_url = upload_server["response"]["upload_url"]
        photo_data = requests.get(file_url).content

        upload_response = requests.post(upload_url, files={"photo": ("photo.jpg", photo_data)}).json()

        save_response = requests.get(
            "https://api.vk.com/method/photos.saveWallPhoto",
            params={
                "group_id": group_id.lstrip("-"),
                "photo": upload_response["photo"],
                "server": upload_response["server"],
                "hash": upload_response["hash"],
                "access_token": token,
                "v": VK_API_VERSION
            }
        ).json()

        photo = save_response["response"][0]
        return f'photo{photo["owner_id"]}_{photo["id"]}'
    except Exception as e:
        print(f"[upload_photo_to_vk] Error: {e}")
        return None

def upload_video_to_vk(token: str, group_id: str, file_url: str) -> str | None:
    try:
        save_response = requests.get(
            "https://api.vk.com/method/video.save",
            params={
                "group_id": group_id.lstrip("-"),
                "name": "Telegram Video",
                "description": "",
                "wallpost": 0,
                "access_token": token,
                "v": VK_API_VERSION
            }
        ).json()

        upload_url = save_response["response"]["upload_url"]
        video_data = requests.get(file_url).content

        requests.post(upload_url, files={"video_file": ("video.mp4", video_data)})

        video_id = save_response["response"]["video_id"]
        owner_id = save_response["response"]["owner_id"]
        return f'video{owner_id}_{video_id}'
    except Exception as e:
        print(f"[upload_video_to_vk] Error: {e}")
        return None