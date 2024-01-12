import requests
import json
from config import token


def get_friends(vk_id, advanced=True):
    advanced_fields = ",".join([
        "can_post", "can_see_all_posts", "can_write_private_message", "city",
        "contacts", "country", "domain", "education", "has_mobile", "timezone",
        "last_seen", "nickname", "online", "photo_100", "photo_200_orig",
        "photo_50", "relation", "sex", "status", "universities"
        ]
    )
    tiny_fields = ",".join(["nickname", "photo_200_orig", "sex", "status"])
    
    if advanced:
        fields = advanced_fields
    else:
        fields = tiny_fields

    response = requests.get("https://api.vk.com/method/friends.get",
        params={"user_id": vk_id,
                "access_token": token,
                "v": 5.154,
                "order": "hints",
                "count": 1000
            }
        )
    json_response = json.loads(response.text)
    return json_response

def get_users_info(user_ids: list):
    """
    Функция запрашивает данные сразу о нескольких пользователях c целью
    уменьшить количество запросов
    """
    fields = ",".join([
        "activities", "about", "blacklisted", "blacklisted_by_me", "books", 
        "bdate", "can_be_invited_group", "can_post", "can_see_all_posts", 
        "can_see_audio", "can_send_friend_request", "can_write_private_message", 
        "career", "common_count", "connections", "contacts", "city", 
        "country", "crop_photo", "domain", "education", "exports", 
        "followers_count", "friend_status", "has_photo", "has_mobile", 
        "home_town", "photo_100", "photo_200", "photo_200_orig", 
        "photo_400_orig", "photo_50", "sex", "site", "schools", "screen_name", 
        "status", "verified", "games", "interests", "is_favorite", "is_friend",
        "is_hidden_from_feed", "last_seen", "maiden_name", "military", "movies", 
        "music", "nickname", "occupation", "online", "personal", "photo_id", 
        "photo_max", "photo_max_orig", "quotes", "relation", "relatives", 
        "timezone", "tv", "universities"
    ])
    str_user_ids = [str(user) for user in user_ids]
    users = ",".join(str_user_ids)
    response = requests.get("https://api.vk.com/method/users.get",
        params={"user_ids": users,
                "access_token": token,
                "v": 5.154,
                "fields": fields            
            }
        )
    json_response = json.loads(response.text)
    return json_response
