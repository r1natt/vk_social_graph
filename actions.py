from reqs import get_users_info, get_friends
import db


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
        db.Users().save_many_users(self.users)


class Friends:
    def __init__(self, vk_id: int, goal_depth: int, update=False):
        self.vk_id = vk_id
        self.update = update
        self.goal_depth = goal_depth

        # self.recurse(self.vk_id, 1)

    def get_layer_friends(self, layer_num):
        if layer_num == 1:
            users_list = [self.vk_id]
            
        

    def layers_manager(self):
        for i in range(self.goal_depth + 1):
            self.get_layer_friends(i)

    '''
    def request(self, vk_id):
        friends = get_friends(vk_id)
        return friends

    def recurse(self, source_id, depth):
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

        friends_list = self.request(source_id)

        if len(friends_list) == 0 and depth == 1:
            print("Профиль введеного пользователя закрыт")

        self.save(source_id, friends_list)
        Users(friends_list)
        for friend_vk_id in friends_list:
            print((depth - 1) * "|-- " + str(friend_vk_id))
            is_end = self.recurse(friend_vk_id, depth + 1)
            if is_end == 1:
                break

    def save(self, vk_id, friends_list):
        db.Friends().save_friends(vk_id, friends_list)
    '''

