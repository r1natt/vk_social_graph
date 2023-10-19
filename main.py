from config import my_vk_id, kate_vk_id
from pprint import pprint
import time

from reqs import get_friends, get_user_info
from user_data import User
from db import DB
from errors import error_check


db = DB()


class Users:
    def __init__(self, user_ids: list):
        self.user_ids = user_ids
        users = self.search()
        self.save(users)

    def search(self):
        response = get_user_info(self.user_ids)
        if not error_check(response):
            users_info = response["response"]
        return users_info

    def save(self, users_data):
        for user_data in users_data:
            user = User(user_data)
            db.save_user(user)


class Friends:
    def __init__(self, vk_ids: list[int]):
        self.vk_ids = vk_ids
   
    def get_friends_user_data(self, ids):
        Users(ids)

    def make_closed_profile_dict(self):
        pass

    def request(self, vk_id):
        response = get_friends(vk_id)
        error_flag = error_check(response)
        if not error_flag:
            friends_list = response["response"]["items"]
            ids = [i["id"] for i in friends_list]
            db.add_friends_to_user_record(vk_id, ids)
            self.get_friends_user_data(ids)
            for friend_data in friends_list:
                t = time.time()
                
                user = User(friend_data)
                db.add_friends_to_user_record(user["_id"], [vk_id])
                
                delta_t = time.time() - t
                if delta_t > 0:
                    time.sleep(delta_t)
        elif error_flag == 30:
            print(vk_id, "closed")
        elif error_flag == 18:
            ids = []
        return ids

    def search(self):
        all_friends_ids = []
        for num, vk_id in enumerate(self.vk_ids):
            print(f"{num + 1} / {len(self.vk_ids)}")
            ids = self.request(vk_id)
            all_friends_ids += ids
        return all_friends_ids

class Parser:
    def __init__(self, update=False):
        self.update = update

    def ask(self):
        pass

    def get_friends_in_depth(self, vk_id, depth):
        """
        Порядок действий:
        1) Получаю User данные по странице vk_id
        2) Получаю список друзей Friends пользователя vk_id
        3) 
        """

        Users([vk_id])
        friends_ids = [vk_id]
        for _ in range(2, depth + 1):
            friends_ids = Friends(friends_ids).search()
            print(friends_ids)

#users = Users([321366596])
parser = Parser()
parser.get_friends_in_depth(my_vk_id, 4)
#db.update({"_id": 1}, {"$set": {"a": 2}})
