import logging

from models._types import VK_ID, FriendsResponse
from .graph_search import BFS, UserTask


logger = logging.getLogger(__name__)


class VKParser(BFS):
    def __init__(self,
        reqs_interface,
        friend_collection,
        user_collection
    ):
        self.reqs_interface = reqs_interface
        self.friend_collection = friend_collection
        self.user_collection = user_collection

        super().__init__()

    def action(self, task: UserTask):
        vk_id = task.vk_id

        self.get_user(vk_id)
        return self.get_friends(vk_id)

    def get_user(self, vk_id: VK_ID):
        if not self.user_collection.is_in_db(vk_id):
            user_models = self.reqs_interface.get_users(vk_id)
            self.user_collection.save(user_models)

    def get_friends(self, vk_id: VK_ID) -> FriendsResponse:
        if not self.friend_collection.is_in_db(vk_id):
            friends_model = self.reqs_interface.get_friends(vk_id)
            self.friend_collection.save(vk_id, friends_model)
        else:
            friends_record = self.friend_collection.get_by_vk_id(vk_id)

            if not(friends_record):
                friends_list = []
            else:
                friends_list = friends_record.active_friends

            friends_model = FriendsResponse(
                count=len(friends_list),
                items=friends_list
            )

        friends_list = friends_model.items
        return friends_list
