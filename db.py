import pymongo
from config import mongo_uri
from user_data import User


def get_conn():

    myclient = pymongo.MongoClient(mongo_uri)
    mydb = myclient["vk_parser"]

    users_col = mydb["users"]
    friends_col = mydb["friends"]
    return users_col, friends_col


class DB:
    def __init__(self):
        self.users_col, self.friends_col = get_conn()

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


class Users(DB):
    def __init__(self):
        super().__init__()

    def _records_diff(self, record):
        data_in_db = self.find({"_id": vk_id})

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
        return self.users_col.find(conds)


class Friends(DB):
    def __init__(self):
        super().__init__()

    def _is_record_exist(self, vk_id):
        if self._get_friends_by_id(vk_id) == None:
            return False
        return True

    def _is_user_in_friends_list(self, source_id, target_id):
        # source_id - юзер, в чьем списке друзей я проверяю наличие target_id
        friends_list = self._get_friends_by_id(source_id)
        if friends_list == None:
            return None
        if target_id in friends_list:
            return True
        return False

    def _exclude_in_db(self, friends_list):
        friends_exclude_in_db = []
        for friend_id in friends_list:
            if not bool(self.find(self.friends_col, friend_id)):
                friends_exclude_in_db.append(friend_id)
        return friends_exclude_in_db

    def _get_friends_by_id(self, whose_friends_vk_id, exclude_in_db=False) -> list | None:
        # Возвращает список друзей, если есть запись о друзьях искомого юзера.
        # Либо возвращает None, если такой записи нет
        # Либо, если exclude_in_db=True, возвращает список друзей юзера, 
        # записи о которых еще нет в бд (эта функция нужна для mutual_friends)
        record = self.find(self.friends_col, whose_friends_vk_id)
        if record == None:
            return None
        if exclude_in_db:
            return self._exclude_in_db(record["friends"])
        return record["friends"]
    
    def _new_record(self, whose_friends_vk_id, friends_list):
        data = {"_id": whose_friends_vk_id, "friends": friends_list}
        self.save(self.friends_col, data)

    def _update_existing_record(self, whose_friends_vk_id, friends_list):
        friends_in_db = set(self._get_friends_by_id(whose_friends_vk_id))
        friends_list = set(friends_list)
        new_friends = sorted(list(friends_list - friends_in_db))
        if len(new_friends) != 0:
            updated_values = {"$addToSet": {"friends": {"$each": new_friends}}}
            self.update(self.friends_col, whose_friends_vk_id, updated_values)

    def save_friends(self, vk_id, friends_list):
        # Функция сохраняет список друзей friends_list пользователя vk_id
        # vk_id - id пользователя вк, обладатель друзей
        # friends_list - список друзей пользователя

        if not self._is_user_in_db(self.friends_col, vk_id):
            # условие выполняется, если до этого в бд не было сохранено списка
            # друзей этом пользователя
            self._new_record(vk_id, friends_list)
        else:
            # если список друзей до этого уже сохранялся, мы должны объединить
            # список в бд и новый список
            self._update_existing_record(vk_id, friends_list)
        self._add_mutual_friends(vk_id, friends_list)

    def _add_mutual_friends(self, whose_friends_vk_id, friends_list):
        
        for friend_vk_id in friends_list:
            # проходимся по всем друзьям циклом
            if self._is_record_exist(friend_vk_id):
                # проверяем есть ли запись в бд
                if self._is_user_in_friends_list(friend_vk_id, whose_friends_vk_id):
                    # может быть такое, что у friend_vk_id уже есть 
                    # whose_friends_vk_id в списке друзей в бд, в этом случае 
                    # не делаю ничего
                    pass
                else:
                    # Если whose_friends_vk_id нет в списке друзей 
                    # friend_vk_id, то добавляю его в список
                    updated_values = {"$addToSet": {"friends": whose_friends_vk_id}}
                    self.update(self.friends_col, friend_vk_id, updated_values)
            else:
                # если записи о пользователе нет, создаем новую запись
                data = {"_id": friend_vk_id, "friends": [whose_friends_vk_id]}
                self.save(self.friends_col, data)

    def find_for_graph(self, conds):
        return self.friends_col.find(conds)


"""
db = DB()

db.save_friends(1, [2, 3, 4])
db.save_friends(2, [4, 5, 6])
print(db.get_friends_except_in_db(2))
"""
