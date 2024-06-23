import requests
import json
from config import token
from logger import general_log
from multiprocessing import Process, Value
import datetime
from errors import Errors
import time
from math import ceil # деление в большую сторону


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
def get_friends_execute_reqs(parted_users_list):
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

def get_friends(users_list):
    number_of_cycles = ceil(len(users_list) / 25)
    print('number of cycles: ', number_of_cycles)
    users_friends = []
    for i in range(number_of_cycles):
        print(i * 25, i * 25 + 25)
        users_friends += get_friends_execute_reqs(users_list[i * 25:i * 25 + 25])
    return users_friends

tps_bucket.start()
print(len(get_friends([2695377, 33994417, 65889850, 66927760, 85731004, 87186820, 101251072, 102013854, 112234597, 121923250, 132804584, 134117959, 138692332, 138966028, 144995034, 145957477, 148376178, 150387845, 150659210, 150925330, 157553198, 159953562, 160192302, 165875497, 166227328, 166354144, 166987837, 167216762, 169954793, 170122847, 175242329, 180978044, 181182492, 184060884, 184488794, 188377290, 190172214, 191223472, 192300383, 194911958, 195146772, 199316410, 202509857, 220494037, 222995820, 228707072, 230353463, 240326241, 242706801, 246794955, 247118376, 248685319, 252774684, 260515274, 262449975, 268104884, 270234980, 272402723, 282839399, 284456904, 292484853, 293568223, 299427279, 299830077, 307724182, 309322209, 311819448, 318658282, 320692179, 322535534, 323437765, 323534452, 324040975, 330675985, 331076160, 332675860, 333038736, 333798307, 336537789, 337110988, 341714325, 353021597, 353372671, 356005371, 358495501, 358687680, 359492386, 362758210, 383000248, 388354990, 388775460, 390384247, 390905535, 400445922, 410002600, 415190927, 419924233, 422407610, 422670045, 422975446, 425854961, 436344954, 437314559, 444863423, 447154882, 458406064, 458583563, 460921836, 461063711, 469685436, 470201403, 477278322, 480248223, 483836159, 485384484, 486095682, 495215494, 505186625, 511671587, 524986286, 530494073, 532588169, 565842103, 573841372, 577074699, 582330617, 585982405, 601963475, 603257266, 603465278, 613076820, 614658927, 632253124, 654223619, 695681230, 742068321, 748179209, 767741403, 778804628])))


'''
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
'''

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
        "career", "connections", "contacts", "city", 
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
    # Я работаю с сервисным ключом, поле common_count не может быть запрошено
    str_user_ids = [str(user) for user in user_ids]
    str_user_ids = str_user_ids[:500] # ПОТОМ НАДО ПОФИКСИТЬ, ИЗЗА 414 ошибки я обрезаю КОЛИЧЕСТВО ЛЮДЕЙ В ЗАПРОСЕ!!!
    users = ",".join(str_user_ids)
    response = requests.get("https://api.vk.com/method/users.get",
        params={"user_ids": users,
                "access_token": token,
                "v": 5.154,
                "fields": fields            
            }
        )
    general_log.debug(f"Users request: {len(user_ids)} items")
    json_response = json.loads(response.text)
    
    if Errors(json_response).is_error:
        users = []
    else:
        users = json_response["response"]
    
    return users
