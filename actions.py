from reqs import get_users_info, get_friends
from db import DB
from pprint import pprint


db = DB()


class User(dict):
    def __init__(self, user_data):
        self.update(user_data)
        self.change_id()

    def change_id(self):
        _id = self["id"]
        del self["id"]
        self["_id"] = _id


class Users:
    def __init__(self, user_ids: list, save=True):
        self.user_ids = user_ids
        self.users = []  # вся инфа по юзерам хранится здесь

        self.search()
        pprint(self.users)
        #if save:
        #    self.save(users)

    def request(self):
        response = get_users_info(self.user_ids)
        return response

    def search(self):
        response = self.request()
        self.users_info = response["response"]
        self.init_users()

    def init_users(self):
        for user_data in self.users_info:
            self.users.append(User(user_data))

    def save(self, users_data):
        pass


class Friends:
    def __init__(self, vk_id: list[int], goal_depth: int, update=True):
        self.vk_id = vk_id
        self.update = update
        self.goal_depth = goal_depth + 1
        
        entry_point_friends = self.request(vk_id)
            # entry_point - друзья точки входа, то есть первая глубина в 
            # парсинге друзей 
        self.recurse(self.vk_id, entry_point_friends, 1)

    def request(self, vk_id):
        response = get_friends(vk_id)
        if "response" in response:
            items = response["response"]["items"]
        else:
            items = []
        return items

    # Вся магия поиска вглубину происходит в этой функции, здесь я использую 
    # рекурсию для поиска вглубь, когда функция доходит до нужного мне уровня
    # Она дальше не идет
    # 
    # Самая частая проблема для рекурсий - утечки памяти, но:
    # По идее одновременно количество запущенных функций не может превышать 
    # числа для поиска вглубину (если self.goal_depth = 3, то по идее 
    # единовременно не может существовать больше 3х функций recurse)
    def recurse(self, source_id, friends_list, depth):
        if depth == self.goal_depth:
            return 1  # Выход из рекурсии происходит, когда мы достигаем искомой глубины
        self.save(source_id, friends_list)
        for friend_vk_id in friends_list:
            print((depth - 1) * "|---" + str(friend_vk_id))
            is_end = self.recurse(friend_vk_id, self.request(friend_vk_id), depth + 1)
            if is_end == 1:
                break

    def save(self, vk_id, friends_list):
        db.save_friends(vk_id, friends_list)

Friends(321366596, 3)
