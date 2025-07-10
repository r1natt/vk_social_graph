
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