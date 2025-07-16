import logging
import time
from collections import deque
from functools import wraps
import json
from typing import Optional, Callable
from abc import ABC, abstractclassmethod

import requests
from config import API_KEY
from models._types import FriendsResponse, UserInfo
from .errors import VKApiErrorHandler, ErrorHandlerResult, ErrorAction

logger = logging.getLogger(__name__)
VK_API_VERSION = 5.199
ERROR_RESPONSE = {"count": 0, "items": []}


class RetryPolicy:
    def __init__(self, max_retries=3):
        self.vk_error_handler = VKApiErrorHandler()

        self.max_retries = max_retries
        self.retry_exceptions = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        )
    
    def execute(self, func: Callable, *args, **kwargs):
        attempt = 1

        while attempt <= self.max_retries:
            try:
                result =  func(*args, **kwargs)
                error: ErrorHandlerResult = self.vk_error_handler.handle(result)

                return result

            except self.retry_exceptions as e:
                logger.error(f"retry_exception error: {e}")
                attempt += 1
            except Exception as e:
                logger.exception(f"Unknown error: {e}")
                raise e
        


class RequestTracker:
    """
    Апи имеют ограничения на количество запросов в секунду (Request Per Second).
    Данный класс отслеживает RPS и ждет, исчерпан лимит запросов за последнюю 
    секунду
    """

    request_times = deque()
    exceptedRPS = 5

    def __init__(self):
        self.rp = RetryPolicy()

    def send_request(self, *args, **kwargs):
        """Исполняет запрос только после проверки _check_rps_and_wait_if_need"""
        self._check_rps_and_wait_if_need()

        def _request() -> dict:
            response = requests.get(*args, **kwargs)
            response.raise_for_status()
            return response.json()
        
        self.rp.execute(_request)

    def _check_rps_and_wait_if_need(self) -> None:
        """
        Проверяет время запросов в request_times и если количество запросов было 
        равное значению exceptedRPS и все они были менее секунды назад, то 
        функция останавливает всю программу на время, через которое можно будет 
        снова отправить запрос 
        """
        while True:
            now = time.monotonic()

            while self.request_times and self.request_times[0] <= now - 1:
                self.request_times.popleft()

            if len(self.request_times) < self.exceptedRPS:
                self.request_times.append(now)
                break
            else:
                wait_time = self.request_times[0] + 1 - now
                print(wait_time)
                time.sleep(wait_time)


rt = RequestTracker()


def check_vk_api_error(response_json: dict) -> Optional[VKAPIError]:
    try:
        handle_vk_api_error(response_json)
    except VKAPIError as e:
        logger.error(f"VKAPIError: {e}")
        return e

def get_friends(vk_id: int) -> FriendsResponse | VKAPIError:
    """Вызывает ручку апи получения друзей пользователя vk_id"""
    response = rt.send_request(
        "https://api.vk.com/method/friends.get", 
        params={"user_id": vk_id,
            "access_token": API_KEY,
            "v": 5.154,
            "order": "hints",
            "count": 1000
        }
    )

    vk_error = check_vk_api_error(response)
    if vk_error:
        return FriendsResponse(**ERROR_RESPONSE)

    # Если vk_error пустой - в ответе точно есть "response"
    response_body_json = response_json["response"]

    logger.info(f"{vk_id} {response_body_json}")
    response_model = FriendsResponse(**response_body_json)

    return response_model

def get_user(vk_id: int) -> list[UserInfo] | VKAPIError:
    response = rt.send_request(
        "https://api.vk.com/method/users.get", 
        params={"user_ids": vk_id,
            "access_token": API_KEY,
            "v": VK_API_VERSION,
            "fields": [
                "activities","about","blacklisted","blacklisted_by_me","books",
                "bdate","can_be_invited_group","can_post","can_see_all_posts",
                "can_see_audio","can_send_friend_request","can_write_private_message",
                "career","common_count","connections","contacts","city",
                "crop_photo","domain","education","exports","followers_count",
                "friend_status","has_photo","has_mobile","home_town","photo_100",
                "photo_200","photo_200_orig","photo_400_orig","photo_50","sex",
                "site","schools","screen_name","status","verified","games",
                "interests","is_favorite","is_friend","is_hidden_from_feed",
                "last_seen","maiden_name","movies","music","nickname",
                "occupation","online","personal","photo_id","photo_max",
                "photo_max_orig","quotes","relation","relatives","timezone",
                "tv","universities","is_verified"
            ]
        }
    )

    response_json = json.loads(response.text)

    vk_error = check_vk_api_error(response_json)
    if vk_error:
        return vk_error

    # Если vk_error пустой - в ответе точно есть "response"
    response_body_json = response_json["response"]

    logger.info(f"{vk_id} {response_body_json}")
    response_model_list = [UserInfo(**response_user_info) for response_user_info in response_body_json]

    return response_model_list

# @catch_network_errors
# def get_many_friends(vk_ids: list[int]):
#     code = f"""
#     var my_users = {parted_users_list};
#     var return_data = [];
#     var a = 0;
#     while (a != my_users.length) {{
#         var friends = API.friends.get({{ "user_id":my_users[a] }});
#         var owner_friends_dict = {{"owner": my_users[a], "friends": friends.items}};
#         return_data.push(owner_friends_dict);

#         a = a + 1;
#     }}; 
#     return return_data;
#     """

#     friends = requests.get("https://api.vk.com/method/execute",
#         params = {
#             "code": code,
#             "access_token": token,
#             "v": VK_API_VERSION
#         }
#     )
#     friends = json.loads(friends.text)
#     return friends['response']

# @bucket_queue
# def get_users_info(user_ids: list):
#     code = f"""
#     var user_ids = {user_ids};

#     var users = API.users.get({{ "user_ids":user_ids }});
    
#     return users;
#     """

#     users = requests.get("https://api.vk.com/method/execute",
#         params = {
#             "code": code,
#             "access_token": token,
#             "v": VK_API_VERSION
#         }
#     )
#     users = json.loads(users.text)
    
#     return users['response']
