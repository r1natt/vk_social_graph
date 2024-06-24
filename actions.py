from reqs import get_users_info, get_friends, get_many_friends
import db
from math import ceil


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

    def request(self, parted_ids):
        response = get_users_info(parted_ids)
        return response

    def search(self):
        number_of_cycles = ceil(len(self.user_ids) / 500)
        for i in range(number_of_cycles):
            response = self.request(self.user_ids[i * 500:i * 500 + 500])
            self.init_users(response)

    def init_users(self, response):
        for user_data in response:
            self.users.append(User(user_data))

    def save(self):
        db.Users().save_many_users(self.users)


class Friends:
    def __init__(self, vk_id: int, goal_depth: int, update=False):
        self.vk_id = vk_id
        self.update = update
        self.goal_depth = goal_depth + 1

        self.recurse(self.vk_id, 1, [])

    def request(self, vk_id):
        friends = get_friends(vk_id)
        return friends
    
    def prepare_to_save_users(self, many_friends):
        all_friends_ids = []
        for owner_friends_pair in many_friends:
            # print(owner_friends_pair['owner'])
            if owner_friends_pair["friends"] != None:
                all_friends_ids += owner_friends_pair["friends"]
        Users(all_friends_ids)
    
    def request_many(self, users_list):
        number_of_cycles = ceil(len(users_list) / 25)
        for i in range(number_of_cycles):
            many_friends = get_many_friends(users_list[i * 25:i * 25 + 25])
            self.save_many(many_friends)
            self.prepare_to_save_users(many_friends)

    def recurse(self, source_id, depth, friends_list):
        # Вся магия поиска вглубину происходит в этой функции, здесь я 
        # использую рекурсию для поиска вглубь, когда функция доходит до 
        # нужного мне уровня, она дальше не идет
        # 
        # Самая частая проблема для рекурсий - утечки памяти, но:
        # По идее одновременно количество запущенных функций не может 
        # превышать числа для поиска вглубину (если self.goal_depth = 3, то 
        # единовременно не может существовать больше 3х функций recurse) 
        if depth == self.goal_depth - 1:
            self.request_many(friends_list)
            print((depth - 2) * "|-- " + "...")
            return 1  # Выход из рекурсии происходит, когда мы достигаем 
                      # искомой глубины

        friends_list = self.request(source_id)

        if len(friends_list) == 0 and depth == 1:
            print("Профиль введеного пользователя закрыт")

        self.save(source_id, friends_list)
        Users(friends_list)

        for n, friend_vk_id in enumerate(friends_list):
            print((depth - 1) * "|-- " + str(friend_vk_id))
            is_end = self.recurse(friend_vk_id, depth + 1, friends_list)
            if is_end == 1:
                break

    def save(self, vk_id, friends_list):
        db.Friends().save_friends(vk_id, friends_list)
    
    def save_many(self, owner_friends_pairs):
        for owner_friends_pair in owner_friends_pairs:
            vk_id = owner_friends_pair["owner"]
            friends_list = owner_friends_pair["friends"]
            if friends_list == None:
                friends_list = []
            self.save(vk_id, friends_list)

