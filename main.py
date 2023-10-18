import json
from config import kate_vk_id

from reqs import get_friends
from user_data import UserData
from db import DB
from errors import Errors


class Friends:
    def __init__(self, vk_id, depth):
        self.vk_id = vk_id
        self.depth = depth

    def search(self):
        response = get_friends(self.vk_id)
        json_response = json.loads(response)
        if not self.errors.error_checker(response):
            for friends_dict in response["response"]["items"]:
                user_data = UserData(vk_id, friends_dict)
                self.db.add_users_friends()
                break
            self.db.save_users_friends(user_data)
        return self.response

    def search_in_depth(self, entry_point, depth=3):  # entry_point - точка входа, с кого начинать поиск в глубину
        ep_friends = self.get_friends(entry_point)["response"]["items"]  # entry point friends
        ep_friends_ids = [i["id"] for i in ep_friends]

        for knee in range(2, depth + 1):
            all_users_past_knee = self.saver._get_users_n_knee(knee - 1)
            for n, user_id in enumerate(all_users_past_knee):
                t = time.time()
                self.get_friends(user_id, save=True, knee=knee)
                print(f"{knee} {n + 1}/{len(all_users_past_knee)}")
                delta_t = time.time() - t
                if 0.2 - delta_t > 0:
                    time.sleep(0.2 - delta_t)


class Parser:
    def __init__(self):
        self.db = DB()
        self.errors = Errors()



parser = Parser()
# parser.friends(my_vk_id)
db = DB()
db.add_users_friends(kate_vk_id, [1])
