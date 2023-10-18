import requests
from pprint import pprint
import json
import os
import time
import logging
from config import token, mongo_uri, my_vk_id, save_dir, kate_vk_id
from datetime import datetime
from reqs import get_friends
import copy
import pymongo


class DB:
    def __init__(self):
        myclient = pymongo.MongoClient(mongo_uri)
        mydb = myclient["vk_parser"]
        self.mycol = mydb["users"]

    def save_users_friends(self, user_friends): 
        friends_dicts = user_friends["response"]["items"]
        for friend_dict in friends_dicts:
            self.save_user(friend_dict)

    def add_users_friends(self, vk_id, friends: list):
        user_query = self.mycol.find_one({ "_id": vk_id })
        if user_query == None:
            user_data = {
                "_id": vk_id,
                "friends": friends
            }
        else:
            user_data = user_query
            print(user_data)
            if "friends" in user_data:
                for friend_id in friends:
                    if friend_id not in user_data["friends"]:
                        #user_data["friends"].add(friends)

            else:
                user_data["friends"] = friends
        self.update_user_record(user_query, user_data)
            
    def update_user_record(self, record, updated_data):
        print(record, updated_data)
        self.mycol.update_one(record, updated_data)

    def save_user(self, user_data):
        self.mycol.insert_one(user_data)


class UserData():
    def __init__(self, owner_id, user_data):
        self.user_data = user_data
        self.owner_id = owner_id
        self._cook_user_data()

    def __repr__(self):
        print(self.user_data)
        return json.dumps(self.user_data, ensure_ascii=False)

    def _cook_user_data(self):
        self._user_handler()
        self._user_add_date()
    
    def _user_add_date(self):
        user_id = self.user_data["_id"]
        del self.user_data["_id"]
        today = datetime.today()
        today = today.strftime("%Y-%m-%d_%H:%M:%S")
        
        updated_data = {}
        updated_data["_id"] = user_id
        updated_data[today] = self.user_data
        self.user_data = updated_data

    def _user_handler(self):
        self.user_data["_id"] = self.user_data["id"]
        del self.user_data["id"]
        self.user_data["first_name"] = self.user_data["first_name"].replace("/", "-").replace("_", "-")
        self.user_data["last_name"] = self.user_data["last_name"].replace("/", "-").replace("_", "-")


class Parser:
    def __init__(self):
        self.saver = Saver()
        self.db = DB()

    def error_checker(self, vk_id):
        error = False
        if 'error' in self.response:
            code = self.response["error"]["error_code"]
            if code == 30:
                self.response = {"id": vk_id,
                                 "is_closed": True}
            elif code == 5:
                print("Update auth key")
            else:
                print("Error", self.response)
            error = True
        return error

    def friends(self, vk_id):
        self.response = get_friends
        self.response = json.loads(self.response)
        if not self.error_checker(vk_id):
            for friends_dict in self.response["response"]["items"]:
                user_data = UserData(vk_id, friends_dict)
                self.db.add_users_friends()
                break
            self.db.save_users_friends(user_data)
        return self.response

#    def search_in_depth(self, entry_point, depth=3):  # entry_point - точка входа, с кого начинать поиск в глубину
#        ep_friends = self.get_friends(entry_point)["response"]["items"]  # entry point friends
#        ep_friends_ids = [i["id"] for i in ep_friends]
#
#        for knee in range(2, depth + 1):
#            all_users_past_knee = self.saver._get_users_n_knee(knee - 1)
#            for n, user_id in enumerate(all_users_past_knee):
#                t = time.time()
#                self.get_friends(user_id, save=True, knee=knee)
#                print(f"{knee} {n + 1}/{len(all_users_past_knee)}")
#                delta_t = time.time() - t
#                if 0.2 - delta_t > 0:
#                    time.sleep(0.2 - delta_t)


class Saver: 
    def save_friends(self, owner_id, friends_list, knee=0):
        friends_dicts = friends_list["response"]["items"]
        for friend_dict in friends_dicts:
            friend_dict["whose_friend"] = owner_id  # буквально значит, чей друг, от кого я узнал этого человека
            user_id = friend_dict["id"]
            first_name = friend_dict["first_name"].replace("/", "-")
            last_name = friend_dict["last_name"].replace("/", "-").replace("_", "-")
            if knee == 0:
                file_name = save_dir + f"{user_id}_{first_name}_{last_name}" + ".json"
            else:
                file_name = save_dir + f"{knee}_{user_id}_{first_name}_{last_name}" + ".json"

            if not(self._is_vk_id_in_dir(user_id)):
                with open(file_name, 'w') as f:
                    json.dump(friend_dict, f, ensure_ascii=False)
    
    def _is_vk_id_in_dir(self, vk_id):
        all_users_in_dir = os.listdir("./users/")
        for i in all_users_in_dir:
            if str(vk_id) in i:
                return True
        return False

    def _get_user_file_name_by_vk_id(self, vk_id):
        all_users_in_dir = os.listdir("./users/")
        for i in all_users_in_dir:
            if str(vk_id) in i:
                return i

    def add_friend_list_to_owner_id(self, owner_id, json_response):
        file_name = self._get_user_file_name_by_vk_id(owner_id)
        with open(save_dir + file_name, "r") as f:
            file_info = json.load(f)
        friends_list = json_response["response"]["items"]
        friends_list_ids = [i["id"] for i in friends_list]
        if 514707049 in friends_list_ids:
            logger.info(f"В друзьях: {owner_id}")
        file_info["friends"] = friends_list_ids
        with open(save_dir + file_name, "w") as f:
            json.dump(file_info, f, ensure_ascii=False)


    def _get_users_n_knee(self, n):
        # буквально получить друзей, сохраненных в users n-го колена
        all_users_in_dir = os.listdir("./users/")
        knees_users = {}
        for user_file_name in all_users_in_dir:
            knee, vk_id, name, last_name = user_file_name.replace(".json", "").split("_")
            if knee not in knees_users:
                knees_users[knee] = [vk_id]
            else:
                knees_users[knee].append(int(vk_id))
        return knees_users[str(n)]


parser = Parser()
# parser.friends(my_vk_id)
db = DB()
db.add_users_friends(kate_vk_id, [1])