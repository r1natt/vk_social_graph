from reqs import get_users_info, get_friends
from db import DB
from pprint import pprint


db = DB()
db.reset()


class User(dict):
    def __init__(self, user_data):
        self.update(user_data)
        self._change_id()

    def _change_id(self):
        _id = self["id"]
        del self["id"]
        self["_id"] = _id


class Users:
    def __init__(self, user_ids: list, save=True):
        self.user_ids = user_ids
        self.users = []  # вся инфа по юзерам хранится здесь

        self.search()
        if save:
            self.save()

    def request(self):
        response = get_users_info(self.user_ids)
        return response

    def search(self):
        response = self.request()
        self.init_users(response)

    def init_users(self, response):
        for user_data in response:
            self.users.append(User(user_data))

    def save(self):
        db.save_many_users(self.users)


class Friends:
    def __init__(self, vk_id: int, goal_depth: int, update=False):
        self.vk_id = vk_id
        self.update = update
        self.goal_depth = goal_depth + 1
        
        # entry_point_friends = self.request(vk_id)
            # entry_point - друзья точки входа, то есть первая глубина в 
            # парсинге друзей 
        self.recurse_test(self.vk_id, 1)

    def request(self, vk_id):
        """
        if not self.update:
            friends = db.get_friends_except_in_db(vk_id)
            if friends == None or len(friends) == 0:
                friends = get_friends(vk_id)
        else:
            friends = get_friends(vk_id)
        """
        friends = get_friends(vk_id)
        return friends

    def recurse_test(self, source_id, depth):
        if depth == self.goal_depth:
            print((depth - 2) * "|-- " + "...")
            return 1  # Выход из рекурсии происходит, когда мы достигаем 
                      # искомой глубины

        friends_list = self.request(source_id)
        self.save(source_id, friends_list)
        Users(friends_list)
        for friend_vk_id in friends_list:
            print((depth - 1) * "|-- " + str(friend_vk_id))
            break
            is_end = self.recurse_test(friend_vk_id, depth + 1)
            if is_end == 1:
                break

    def recurse_consistently(self, source_id, friends_list, depth):
        # Вся магия поиска вглубину происходит в этой функции, здесь я 
        # использую рекурсию для поиска вглубь, когда функция доходит до 
        # нужного мне уровня, она дальше не идет
        # 
        # Самая частая проблема для рекурсий - утечки памяти, но:
        # По идее одновременно количество запущенных функций не может 
        # превышать числа для поиска вглубину (если self.goal_depth = 3, то 
        # единовременно не может существовать больше 3х функций recurse)

        if depth == self.goal_depth:
            print((depth - 2) * "|-- " + "...")
            return 1  # Выход из рекурсии происходит, когда мы достигаем 
                      # искомой глубины

        self.save(source_id, friends_list)
        for friend_vk_id in friends_list:
            print((depth - 1) * "|-- " + str(friend_vk_id))
            friends_req = self.request(friend_vk_id)
            is_end = self.recurse_consistently(friend_vk_id, friends_req, depth + 1)
            if is_end == 1:
                break

    def save(self, vk_id, friends_list):
        db.save_friends(vk_id, friends_list)

