import requests
import json
from config import token
from logger import general_log
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
        time.sleep(1 - (time.time() % 1))
        while True:
            self.refill_bucket()
            # print(datetime.datetime.now().strftime('%H:%M:%S.%f'), "refill")
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
                query = func(*args, **kwargs)
                return query
    return exec_or_wait


tps_bucket = TPSBucket(expected_tps=2)

@bucket_queue
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

@bucket_queue
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

@bucket_queue
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
