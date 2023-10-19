import pymongo
from config import mongo_uri
from user_data import User


class DB:
    def __init__(self):
        myclient = pymongo.MongoClient(mongo_uri)
        mydb = myclient["vk_parser"]
        self.mycol = mydb["users"]

    def save_user(self, user: User):
        vk_id = user["_id"]
        if not self._is_user_in_db(vk_id):
            self.mycol.insert_one(user)
        else:
            """
            По идее словарь user новее, чем данные в бд, поэтому я сравниваю 
            два этих словаря поэлементно, и добавляю только те данные, которые
            изменились
            """
            user_data_in_db = self.find({"_id": vk_id})
            data_for_update = {}
            for key in user:
                user_value = user[key]
                if user_data_in_db != None:
                    if key in user_data_in_db:
                        in_db_value = user_data_in_db[key]
                        if user_value == in_db_value:
                            """
                            буквально значит, если данные из словаря уже есть в 
                            бд, то не делаю ничего
                            """
                            pass
                        else:
                            data_for_update[key] = user[key]
                    else:
                        data_for_update[key] = user[key]
            if len(data_for_update.keys()) == 0:
                # если обновлять нечего, то ничего не делаю
                pass
            else:
                set_dict = {"$set": data_for_update}
                self.update(vk_id, set_dict)

    def save_many_users(self, users: list[User]):
        for user in users:
            self.save_user(user)

    def _is_user_friends_list_in_db(self, vk_id):
        user_data_in_db = self.find(vk_id)
        if "friends" in user_data_in_db:
            return user_data_in_db
        else:
            return False

    def add_friends_to_user_record(self, vk_id, friends_ids_list):
        user_friends_in_db = self._is_user_friends_list_in_db(vk_id)
        if user_friends_in_db:
            user_friends_in_db = user_friends_in_db["friends"]
            whose_friend = []
            for friend_id in friends_ids_list:
                if friend_id not in user_friends_in_db:
                    whose_friend.append(friend_id)
            updated_data = {"$set": {"whose_friend": whose_friend}}   
        else:
            updated_data = {"$set": {"whose_friend": friends_ids_list}}
        self.update(vk_id, updated_data)

    def update(self, vk_id, updated_data):
        self.mycol.update_one({"_id": vk_id}, updated_data)

    def _is_user_in_db(self, vk_id) -> bool:
        if self.find(vk_id) == None:
            return False
        else:
            return True

    def find(self, vk_id):
        return self.mycol.find_one({"_id": vk_id})
