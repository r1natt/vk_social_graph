import pymongo
from config import mongo_uri
from user_data import User


print("import db")


class Users:
    pass


class Friends:
    pass


class DB:
    def __init__(self):
        myclient = pymongo.MongoClient(mongo_uri)
        mydb = myclient["vk_parser"]

        self.users_col = mydb["users"]
        self.friends_col = mydb["friends"]

    def reset(self):
        self.friends_col.delete_many({})
        self.users_col.delete_many({})

    def find(self, col, vk_id):
        query = col.find_one({"_id": vk_id})
        if query == None:
            return None
        return query

    def update(self, col, vk_id, updated_data):
        col.update_one({"_id": vk_id}, updated_data)

    def save(self, col, data):
        col.insert_one(data)

    def _is_user_in_db(self, col, vk_id) -> bool:
        if self.find(col, vk_id) == None:
            return False
        return True

    # ---------------- Users ----------------
    
    def _records_diff(self, record):
        user_data_in_db = self.find({"_id": vk_id})

        set_dict = {"$set": data_for_update}
        self.update(vk_id, set_dict)

    def save_user(self, user: User):
        vk_id = user["_id"]
        if not self._is_user_in_db(self.users_col, vk_id):
            self.save(self.users_col, user)
        else:
            # Делает одно и то же, пока временно
            """
            По идее словарь user новее, чем данные в бд, поэтому я сравниваю 
            два этих словаря поэлементно, и добавляю только те данные, которые
            изменились
            """

    def save_many_users(self, users: list[User]):
        for user in users:
            self.save_user(user)

    def find_for_graph(self, conds):
        return self.mycol.find(conds) 

    # ---------------- Friends ----------------

    def _save_user_friends_first_time(self, vk_id, friends_list):
        data = {"_id": vk_id, "friends": friends_list}
        self.save(self.friends_col, data)

    def _save_only_new_friends_to_user_list(self, vk_id, friends_list):
        friends_in_db = set(self._get_friends_by_id(vk_id))
        friends_list = set(friends_list)
        new_friends = sorted(list(friends_list - friends_in_db))
        if len(new_friends) != 0:
            updated_values = {"$addToSet": {"friends": {"$each": new_friends}}}
            self.update(self.friends_col, vk_id, updated_values)

    def save_friends(self, vk_id, friends_list):
        # Функция сохраняет список друзей friends_list пользователя vk_id
        # vk_id - id пользователя вк, обладатель друзей
        # friends_list - список друзей пользователя

        if not self._is_user_in_db(self.friends_col, vk_id):
            # условие выполняется, если до этого в бд не было сохранено списка
            # друзей этом пользователя
            self._save_user_friends_first_time(vk_id, friends_list)
        else:
            # если список друзей до этого уже сохранялся, мы должны объединить
            # список в бд и новый список
            self._save_only_new_friends_to_user_list(vk_id, friends_list)

    def _add_friend_to_user(self, vk_id, friend_id):
        # Продолжение self._add_mutual_friendship
        # Эта функция проверяет есть запись о vk_id и если есть, то добавляет
        # юзера friend_id в список друзей vk_id, если этого пользователя нет 
        # в списке друзей vk_id, в ином случае не делает ничего.
        # Либо она создает запись о vk_id с пока что единственным другом в 
        # этом списке - friend_id

        friends = self._get_friends_by_id(vk_id)
        if friends == None:
            data = {"_id": vk_id, "friends": [friend_id]}
            self.save(self.friends_col, data)
        else:
            if friend_id not in friends:
                updated_values = {"$addToSet": {"friends": friend_id}}
                self.update(self.friends_col, vk_id, updated_values)

    def _get_friends_by_id(self, vk_id) -> list | None:
        # Возвращает список друзей, если есть запись о друзьях искомого 
        # пользователя. Либо возвращает None, если такой записи нет
        record = self.find(self.friends_col, vk_id)
        if record == None:
            return None
        return record["friends"]

    def get_friends_except_in_db(self, vk_id) -> list | None:
        # Возвращает список друзей пользователя, которых еще нет в бд. Либо 
        # Возвращает None если записи о друзьях в бд нет.
        friends = self._get_friends_by_id(vk_id)
        friends_except_in_db = []
        if friends == None:
            return None
        for friend_id in friends:
            if not bool(self.find(self.friends_col, friend_id)):
                friends_except_in_db.append(friend_id)
        return friends_except_in_db

"""
db = DB()

db.save_friends(1, [2, 3, 4])
db.save_friends(2, [4, 5, 6])
print(db.get_friends_except_in_db(2))
"""
