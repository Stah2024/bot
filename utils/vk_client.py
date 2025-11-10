import requests

def validate_vk_token(token: str) -> dict:
    url = "https://api.vk.com/method/groups.getById"
    params = {
        "access_token": token,
        "v": "5.199"
    }
    response = requests.get(url, params=params)
    return response.json()
