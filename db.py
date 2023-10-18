import pymongo
from config import mongo_uri


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
