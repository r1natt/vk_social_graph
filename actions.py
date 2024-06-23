from reqs import get_users_info, get_friends
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
    def __init__(self, user_ids: list):
        self.user_ids = user_ids
        self.users = []  # вся инфа по юзерам хранится здесь

        self.search()

    def request(self, parted_users_list):
        response = get_users_info(parted_users_list)
        return response

    def search(self):
        number_of_cycles = ceil(len(self.user_ids) / 500)
        for i in range(number_of_cycles):
            parted_users_list = self.user_ids[i * 500:i * 500 + 500]
            response = self.request(parted_users_list)
            self.init_users(response)
            self.save()
            self.users = []

    def init_users(self, response):
        for user_data in response:
            self.users.append(User(user_data))

    def save(self):
        db.Users().save_many_users(self.users)


class Friends:
    def __init__(self, vk_id: int, goal_depth: int, update=False):
        db.delete_layer_num()

        self.vk_id = vk_id
        self.update = update
        self.goal_depth = goal_depth

        self.layers_manager()
        # self.recurse(self.vk_id, 1)

    def request(self, users_list, layer_num):
        number_of_cycles = ceil(len(users_list) / 25)
        print('number of cycles: ', number_of_cycles)
        for i in range(number_of_cycles):
            friends = get_friends(users_list[i * 25:i * 25 + 25])
            self.save(friends, layer_num)
            Users(friends)

    def get_layer_friends(self, layer_num):
        if layer_num == 1:
            users_list = [self.vk_id]
            self.request(users_list, layer_num)
        else:
            pass

    def layers_manager(self):
        for i in range(self.goal_depth + 1):
            self.get_layer_friends(i)

    def save(self, owner_friends_pairs, layer_num):
        """
        owner_friends_pairs:
        [
            {'owner': 26...77, 'friends': [...]},
            {'owner': 33...17, 'friends': [...]},
            {'owner': 66...60, 'friends': [...]},
        ]
        """
        for owner_friends_pair in owner_friends_pairs:
            vk_id = owner_friends_pair['owner']
            friends_list = owner_friends_pair['friends']
            db.Friends().save_friends(vk_id, friends_list, layer_num)
