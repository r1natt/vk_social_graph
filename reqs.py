import requests
import json
from config import token


def get_friends(vk_id, token):
    response = requests.get("https://api.vk.com/method/friends.get",
        params={"user_id": vk_id,
                "access_token": token,
                "v": 5.154,
                "order": "hints",
                "count": 1000,
                "fields": [
                    "bdate",
                    "can_post",
                    "can_see_all_posts",
                    "can_write_private_message",
                    "city",
                    "contacts",
                    "country",
                    "domain",
                    "education",
                    "has_mobile",
                    "timezone",
                    "last_seen",
                    "nickname",
                    "online",
                    "photo_100",
                    "photo_200_orig",
                    "photo_50",
                    "relation",
                    "sex",
                    "status",
                    "universities"
                ]
            }
        ).text
    json_response = json.loads(response)
    return response
