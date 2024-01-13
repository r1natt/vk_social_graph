import requests
import json
from config import token
from logger import reqs_logger
from multiprocessing import Process, Value
import datetime
from errors import Errors
import time

"""
TPS - transaction per second
VK API имеют лимиты на запросы (5 запросов в секунду, но позволяют они немного 
больше). Все дело в том, что пока я выполняю запросы к api без прокси и в 
одном процессе, поэтому мне нужно, чтобы запросы проходили в одной очереди с 
минимальными задержками, пока не достигнут лимит запросов в секунду

TPSBucket - решает эту проблему, по сути своей это отдельный процесс, который 
следит за достижением лимита, и каждую секунду обновляет количество запросов 
на заданное число

Важно отметить, что этот класс будет работать и с запросами, поступающеми от 
разных процессов одновременно
"""
class TPSBucket:
    def __init__(self, expected_tps):
        self.number_of_tokens = Value('i', 0)
        self.expected_tps = expected_tps
        self.bucket_refresh_process = Process(target=self.refill_bucket_per_second)

    def refill_bucket_per_second(self):
        while True:
            self.refill_bucket()
            time.sleep(1)

    def refill_bucket(self):
        self.number_of_tokens.value = self.expected_tps

    def start(self):
        self.bucket_refresh_process.start()

    def stop(self):
        self.bucket_refresh_process.kill()

    def get_token(self):
        response = False
        if self.number_of_tokens.value > 0:
            with self.number_of_tokens.get_lock():
                if self.number_of_tokens.value > 0:
                    self.number_of_tokens.value -= 1
                    response = True
        return response


"""
Декоратор, который проверяет достигнут ли лимит запросов в эту секунду, если 
он достигнут, цикл while будет ждать следующей секунды, чтобы выполнить 
заданную функцию
"""
def bucket_queue(func):
    def exec_or_wait(*args, **kwargs):
        while True:
            if tps_bucket.get_token():
                return func(*args, **kwargs)
    return exec_or_wait


tps_bucket = TPSBucket(expected_tps=5)


@bucket_queue
def get_friends(vk_id):
    reqs_logger.debug(f"Friends request: {vk_id}")
    
    response = requests.get("https://api.vk.com/method/friends.get",
        params={"user_id": vk_id,
                "access_token": token,
                "v": 5.154,
                "order": "hints",
                "count": 1000
            }
        )
    json_response = json.loads(response.text)
    
    if Errors(json_response).is_error:
        friends = []
    else:
        friends = json_response["response"]["items"]

    return friends

@bucket_queue
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

