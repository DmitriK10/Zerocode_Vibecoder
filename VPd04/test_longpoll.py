import requests
from config import Config

token = Config.VK_BOT_TOKEN
group_id = "238939741"  # укажите цифровой ID (например, 123456789)

resp = requests.get("https://api.vk.com/method/groups.getLongPollServer", params={
    "group_id": group_id,
    "access_token": token,
    "v": "5.199"
})

print(resp.json())