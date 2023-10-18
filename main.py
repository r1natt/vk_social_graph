import json
from config import token, mongo_uri, my_vk_id, save_dir, kate_vk_id
from datetime import datetime

from reqs import get_friends
from user_data import UserData
from db import DB


class Parser:
    def __init__(self):
        self.db = DB()

    def error_checker(self, vk_id):
        error = False
        if 'error' in self.response:
            code = self.response["error"]["error_code"]
            if code == 30:
                self.response = {"id": vk_id,
                                 "is_closed": True}
            elif code == 5:
                print("Update auth key")
            else:
                print("Error", self.response)
            error = True
        return error

    def friends(self, vk_id):
        self.response = get_friends
        self.response = json.loads(self.response)
        if not self.error_checker(vk_id):
            for friends_dict in self.response["response"]["items"]:
                user_data = UserData(vk_id, friends_dict)
                self.db.add_users_friends()
                break
            self.db.save_users_friends(user_data)
        return self.response

#    def search_in_depth(self, entry_point, depth=3):  # entry_point - точка входа, с кого начинать поиск в глубину
#        ep_friends = self.get_friends(entry_point)["response"]["items"]  # entry point friends
#        ep_friends_ids = [i["id"] for i in ep_friends]
#
#        for knee in range(2, depth + 1):
#            all_users_past_knee = self.saver._get_users_n_knee(knee - 1)
#            for n, user_id in enumerate(all_users_past_knee):
#                t = time.time()
#                self.get_friends(user_id, save=True, knee=knee)
#                print(f"{knee} {n + 1}/{len(all_users_past_knee)}")
#                delta_t = time.time() - t
#                if 0.2 - delta_t > 0:
#                    time.sleep(0.2 - delta_t)


parser = Parser()
# parser.friends(my_vk_id)
db = DB()
db.add_users_friends(kate_vk_id, [1])
