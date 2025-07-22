import logging
from abc import ABC, abstractclassmethod
from enum import Enum
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
from config.config import MONGO_URI, MONGO_DB_NAME, MONGO_TEST_DB_NAME
from models._types import (
    VK_ID,
    BaseResponse,
    FriendsResponse,
    UserResponse,
    BaseRecord,
    FriendsRecord,
    UserRecord
)


logger = logging.getLogger(__name__)


class CollectionName(Enum):
    FRIENDS = "friends"
    USERS = "users"

class BaseClient:
    def __init__(self, client):
        self.db = client[MONGO_DB_NAME]

    def collection(self, collection_name: str):
        return self.db[collection_name]

class MongoMethods:
    def __init__(self, collection):
        self.collection = collection

    def _insert(self, data: BaseRecord) -> list[ObjectId]:
        if isinstance(data, BaseRecord):
            data = [data]
        format_for_insert = [record.model_dump(by_alias=True) for record in data]
        return self.collection.insert_many(format_for_insert).inserted_ids

    def _find(self, query, many=False) -> list:
        if many:
            return [record for record in self.collection.find(query)]
        return self.collection.find_one(query)

    def _update(self, query, new_value) -> None:
        new_value_request = {"$set": new_value}
        self.collection.update_one(query, new_value_request)

    def _delete(self, query):
        pass


class Collection(ABC):
    @abstractclassmethod
    def save(self, vk_id: VK_ID, data: BaseResponse):
        pass

    @abstractclassmethod
    def get_by_vk_id(self, vk_id: VK_ID) -> BaseRecord:
        pass

    @abstractclassmethod
    def is_in_db(self, vk_id: VK_ID) -> bool:
        pass


class FriendsCollection(MongoMethods, Collection):
    def __init__(self, collection, update_policy, period):
        super().__init__(collection)

        self.update_policy = update_policy
        self.period: timedelta = period

    def save(self, vk_id: VK_ID, data: FriendsResponse):
        is_in_db = self.is_in_db(vk_id)
        if self.update_policy and is_in_db:
            self._update_record(vk_id, data)
        elif not(is_in_db):
            self._new_record(vk_id, data)
        else:
            pass

    def _update_record(self, vk_id, new_data: FriendsResponse):
        record_in_db = self.get_by_vk_id(vk_id)
        last_active_friends_list = record_in_db.active_friends
        deleted_friends_list_in_db = record_in_db.deleted_friends
        visit_history = record_in_db.visit_history

        now_active_friends = new_data.ids

        restore_deleted_friends = self._calc_restore_friends(
            deleted_friends_list_in_db,
            now_active_friends
        )

        compare_deleted_friends = self._calc_deleted_friends(
            last_active_friends_list,
            new_data.ids
        )

        final_deleted_friends = restore_deleted_friends + compare_deleted_friends

        query = {"_id": vk_id}
        self._generate_update_request(query, "active_friends", now_active_friends)
        self._generate_update_request(query, "deleted_friends", final_deleted_friends)
        self._record_new_visit(query, visit_history)

    def _calc_restore_friends(self,
        already_deleted: list[VK_ID],
        active: list[VK_ID]
    ) -> list[VK_ID]:
        # Если кто-то был удален, но они снова начали дружить, то удаляем id из удаленных друзей
        restore_list = []

        for deleted_friend in already_deleted:
            if deleted_friend not in active:
                restore_list.append(deleted_friend)

        return restore_list

    def _calc_deleted_friends(self,
        old_list: list[VK_ID],
        new_list: list[VK_ID]
    ) -> list[VK_ID]:
        # Добавляем новых удаленных людей
        old_list_set = set(old_list)
        new_list_set = set(new_list)
        deleted_friends = old_list_set.difference(new_list)
        return list(deleted_friends)

    def _generate_update_request(self, query, new_data_key, new_data_value):
        self._update(query, {new_data_key: new_data_value})

    def _record_new_visit(self, query, visit_history: list[datetime]):
        # Зафиксировать новый визит
        now = datetime.now()
        visit_history.append(now)
        self._generate_update_request(query, "visit_history", visit_history)

    def _new_record(self, vk_id, data: FriendsResponse) -> None:
        now = datetime.now()
        inserted_record = FriendsRecord(
            _id=vk_id,
            visit_history=[now],
            active_friends=data.items
        )
        self._insert(inserted_record)
        logger.info(f"Friends list successfully saved: {vk_id}")

    def get_by_vk_id(self, vk_id: VK_ID) -> FriendsRecord:
        record_in_db = self._find({"_id": vk_id})
        return FriendsRecord(**record_in_db)

    def is_in_db(self, vk_id: VK_ID) -> bool:
        record_in_db = self._find({"_id": vk_id})
        return bool(record_in_db)


class UserCollection(MongoMethods, Collection):
    def __init__(self, collection):
        super().__init__(collection)

    def save(self, data: list[UserResponse]):
        for user_response in data:
            vk_id = user_response.id

            is_in_db = self.is_in_db(vk_id)
            if not(is_in_db):
                self._new_record(user_response)

    def _new_record(self, data: UserResponse):

        now = datetime.now()

        clean_data = {
            k: v for k, v in data if not(k in ["id", "_id"])
        }

        inserted_record = UserRecord(
            _id=data.id,
            visit_history=[now],
            **clean_data
        )
        self._insert(inserted_record)
        logger.info(f"new user info: {data.id}")

    def get_by_vk_id(self, vk_id: VK_ID) -> UserRecord:
        record_in_db = self._find({"_id": vk_id})
        return UserRecord(**record_in_db)

    def is_in_db(self, vk_id: VK_ID) -> bool:
        record_in_db = self._find({"_id": vk_id})
        return bool(record_in_db)


class CollectionFactory:
    _client = MongoClient(MONGO_URI)

    def __init__(self, test=False, reset=False):
        db_name = MONGO_DB_NAME
        if test:
            db_name = MONGO_TEST_DB_NAME

        self._db = self._client[db_name]

        if reset:
            self.reset_collections()

    def reset_collections(self):
        collections_name = self._db.list_collection_names()

        for collection_name in collections_name:
            self._db[collection_name].drop()
            self._db[collection_name]
        print(self._db.list_collection_names())

    def friend_collection(self, update=False, period=timedelta(days=14)):
        collection = self._db[CollectionName.FRIENDS.value]
        return FriendsCollection(collection, update, period)

    def user_collection(self):
        collection = self._db[CollectionName.USERS.value]
        return UserCollection(collection)