import requests
# import json
# from config.config import token
# from logger import general_log
# from multiprocessing import Process, Value
import datetime
# from errors import Errors
import time
from collections import deque


def sleep05():
    time.sleep(0.05)
    return 5

def sleep1():
    time.sleep(0.1)
    return 5

def sleep2():
    time.sleep(0.2)
    return 5


class RequestTracker:
    """
    К апи ВК можно обращаться Request Per Second должен быть равен 5, этот класс
    отслеживает выполнение данного условия    
    """

    request_times = deque()
    exceptedRPS = 5

    async def send_request():
        now = time.monotonic()
        print(now)

        while True:



rt = RequestTracker()

start_time = time.time()
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
rt.exec(sleep05)
print(f"exec time: {time.time() - start_time}")


# @bucket_queue
def get_friends(vk_id):
    response = requests.get("https://api.vk.com/method/friends.get",
        params={"user_id": vk_id,
                "access_token": token,
                "v": 5.154,
                "order": "hints",
                "count": 1000
            }
        )
    general_log.debug(f"Friends request: {vk_id}")
    json_response = json.loads(response.text)
    
    error_check = Errors(json_response)
    if error_check.is_error:
        friends = []
    else:
        friends = json_response["response"]["items"]

    return friends

# @bucket_queue
def get_many_friends(parted_users_list):
    code = f"""
    var my_users = {parted_users_list};
    var return_data = [];
    var a = 0;
    while (a != my_users.length) {{
        var friends = API.friends.get({{ "user_id":my_users[a] }});
        var owner_friends_dict = {{"owner": my_users[a], "friends": friends.items}};
        return_data.push(owner_friends_dict);

        a = a + 1;
    }}; 
    return return_data;
    """

    friends = requests.get("https://api.vk.com/method/execute",
        params = {
            "code": code,
            "access_token": token,
            "v": 5.199
        }
    )
    friends = json.loads(friends.text)
    return friends['response']

# @bucket_queue
def get_users_info(user_ids: list):
    code = f"""
    var user_ids = {user_ids};

    var users = API.users.get({{ "user_ids":user_ids }});
    
    return users;
    """

    users = requests.get("https://api.vk.com/method/execute",
        params = {
            "code": code,
            "access_token": token,
            "v": 5.199
        }
    )
    users = json.loads(users.text)
    
    return users['response']
