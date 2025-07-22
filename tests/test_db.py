import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from pymongo import MongoClient
from config.config import MONGO_URI, MONGO_TEST_DB_NAME

from db.db import (
    BaseClient,
    MongoMethods,
    FriendsCollection,
    CollectionFactory,
    Collection
)
from models._types import (
    VK_ID,
    FriendsResponse,
    UserResponse,
    BaseRecord,
    FriendsRecord,
    UserRecord
)


class TestBaseClient(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.mock_db = Mock()
        self.mock_client.__getitem__.return_value = self.mock_db
        self.base_client = BaseClient(self.mock_client)
    
    def test_init(self):
        self.assertEqual(self.base_client.db, self.mock_db)
        self.mock_client.__getitem__.assert_called_once()
    
    def test_collection(self):
        collection_name = "test_collection"
        mock_collection = Mock()
        self.mock_db.__getitem__.return_value = mock_collection
        
        result = self.base_client.collection(collection_name)
        
        self.assertEqual(result, mock_collection)
        self.mock_db.__getitem__.assert_called_once_with(collection_name)


class TestMongoMethods(unittest.TestCase):
    def setUp(self):
        self.mock_collection = Mock()
        self.mongo_methods = MongoMethods(self.mock_collection)
    
    def test_init(self):
        self.assertEqual(self.mongo_methods.collection, self.mock_collection)
    
    def test_insert_single_record(self):
        mock_record = Mock(spec=BaseRecord)
        mock_record.dict.return_value = {"test": "data"}
        mock_insert_result = Mock()
        mock_insert_result.inserted_ids = [ObjectId()]
        self.mock_collection.insert_many.return_value = mock_insert_result
        
        result = self.mongo_methods._insert(mock_record)
        
        self.assertEqual(result, mock_insert_result.inserted_ids)
        self.mock_collection.insert_many.assert_called_once_with([{"test": "data"}])
    
    def test_find_one(self):
        query = {"_id": "test_id"}
        expected_result = {"test": "data"}
        self.mock_collection.find_one.return_value = expected_result
        
        result = self.mongo_methods._find(query)
        
        self.assertEqual(result, expected_result)
        self.mock_collection.find_one.assert_called_once_with(query)
    
    def test_find_many(self):
        query = {"test": "query"}
        mock_cursor = [{"doc1": "data1"}, {"doc2": "data2"}]
        self.mock_collection.find.return_value = mock_cursor
        
        result = self.mongo_methods._find(query, many=True)
        
        self.mock_collection.find.assert_called_once_with(query)
    
    def test_update(self):
        query = {"_id": "test_id"}
        new_value = {"field": "new_value"}
        expected_update = {"$set": new_value}
        
        self.mongo_methods._update(query, new_value)
        
        self.mock_collection.update_one.assert_called_once_with(query, expected_update)


class TestFriendsCollection(unittest.TestCase):
    def setUp(self):
        self.mock_collection = Mock()
        self.update_policy = True
        self.period = timedelta(days=14)
        self.friends_collection = FriendsCollection(
            self.mock_collection, 
            self.update_policy, 
            self.period
        )
    
    def test_init(self):
        self.assertEqual(self.friends_collection.collection, self.mock_collection)
        self.assertEqual(self.friends_collection.update_policy, self.update_policy)
        self.assertEqual(self.friends_collection.period, self.period)
    
    def test_calc_deleted_friends(self):
        old_list = [1, 2, 3, 4, 5]
        new_list = [1, 2, 4, 6, 7]
        
        result = self.friends_collection._calc_deleted_friends(old_list, new_list)
        
        expected = [3, 5]
        self.assertEqual(sorted(result), sorted(expected))
    
    def test_is_in_db_true(self):
        vk_id = 12345
        self.mock_collection.find_one.return_value = {"_id": vk_id}
        
        result = self.friends_collection.is_in_db(vk_id)
        
        self.assertTrue(result)
        self.mock_collection.find_one.assert_called_once_with({"_id": vk_id})
    
    def test_is_in_db_false(self):
        vk_id = 12345
        self.mock_collection.find_one.return_value = None
        
        result = self.friends_collection.is_in_db(vk_id)
        
        self.assertFalse(result)
        self.mock_collection.find_one.assert_called_once_with({"_id": vk_id})
    
    @patch('db.db.datetime')
    def test_new_record(self, mock_datetime):
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        vk_id = 12345
        friends_data = Mock()
        friends_data.items = [1, 2, 3]
        
        with patch.object(self.friends_collection, '_insert') as mock_insert:
            self.friends_collection._new_record(vk_id, friends_data)
            
            mock_insert.assert_called_once()
            call_args = mock_insert.call_args[0][0]
            self.assertEqual(call_args._id, vk_id)
            self.assertEqual(call_args.visit_history, [mock_now])
            self.assertEqual(call_args.active_friends, friends_data.items)
    
    def test_get_by_vk_id(self):
        vk_id = 12345
        mock_record_data = {
            "_id": vk_id,
            "visit_history": [datetime.now()],
            "active_friends": [1, 2, 3],
            "deleted_friends": []
        }
        self.mock_collection.find_one.return_value = mock_record_data
        
        with patch('your_module.FriendsRecord') as mock_friends_record:
            mock_instance = Mock()
            mock_friends_record.return_value = mock_instance
            
            result = self.friends_collection.get_by_vk_id(vk_id)
            
            self.assertEqual(result, mock_instance)
            mock_friends_record.assert_called_once_with(**mock_record_data)
    
    def test_save_friends_new_record(self):
        vk_id = 12345
        friends_data = Mock()
        
        with patch.object(self.friends_collection, 'is_in_db', return_value=False):
            with patch.object(self.friends_collection, '_new_record') as mock_new_record:
                self.friends_collection.save_friends(vk_id, friends_data)
                
                mock_new_record.assert_called_once_with(vk_id, friends_data)
    
    def test_save_friends_update_record(self):
        vk_id = 12345
        friends_data = Mock()
        
        with patch.object(self.friends_collection, 'is_in_db', return_value=True):
            with patch.object(self.friends_collection, '_update_record') as mock_update_record:
                self.friends_collection.save_friends(vk_id, friends_data)
                
                mock_update_record.assert_called_once_with(vk_id, friends_data)


class TestCollectionFactory(unittest.TestCase):
    @patch('your_module.MongoClient')
    def test_init_production(self, mock_mongo_client):
        mock_client = Mock()
        mock_db = Mock()
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client
        
        factory = CollectionFactory(test=False)
        
        self.assertEqual(factory._client, mock_client)
        self.assertEqual(factory._db, mock_db)
    
    @patch('your_module.MongoClient')
    def test_init_test(self, mock_mongo_client):
        mock_client = Mock()
        mock_db = Mock()
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client
        
        factory = CollectionFactory(test=True)
        
        self.assertEqual(factory._client, mock_client)
        self.assertEqual(factory._db, mock_db)
    
    def test_friends_collection(self):
        mock_client = Mock()
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__.return_value = mock_collection
        
        with patch('your_module.MongoClient', return_value=mock_client):
            mock_client.__getitem__.return_value = mock_db
            factory = CollectionFactory()
            
            with patch('your_module.FriendsCollection') as mock_friends_collection:
                mock_instance = Mock()
                mock_friends_collection.return_value = mock_instance
                
                result = factory.friends_collection()
                
                self.assertEqual(result, mock_instance)
                mock_friends_collection.assert_called_once_with(
                    mock_collection, 
                    False, 
                    timedelta(days=14)
                )


class TestFriendsCollectionPytest:
    @pytest.fixture
    def mock_collection(self):
        return Mock()
    
    @pytest.fixture
    def friends_collection(self, mock_collection):
        return FriendsCollection(mock_collection, True, timedelta(days=14))
    
    def test_calc_deleted_friends_empty_lists(self, friends_collection):
        result = friends_collection._calc_deleted_friends([], [])
        assert result == []
    
    def test_calc_deleted_friends_no_changes(self, friends_collection):
        old_list = [1, 2, 3]
        new_list = [1, 2, 3]
        result = friends_collection._calc_deleted_friends(old_list, new_list)
        assert result == []
    
    def test_calc_deleted_friends_all_deleted(self, friends_collection):
        old_list = [1, 2, 3]
        new_list = []
        result = friends_collection._calc_deleted_friends(old_list, new_list)
        assert sorted(result) == sorted([1, 2, 3])
    
    def test_calc_deleted_friends_partial_deletion(self, friends_collection):
        old_list = [1, 2, 3, 4, 5]
        new_list = [1, 3, 5, 6, 7]
        result = friends_collection._calc_deleted_friends(old_list, new_list)
        assert sorted(result) == sorted([2, 4])
    
    @pytest.mark.parametrize("vk_id,expected", [
        (12345, True),
        (67890, False),
        (None, False),
    ])
    def test_is_in_db_parametrized(self, friends_collection, vk_id, expected):
        if expected:
            friends_collection.collection.find_one.return_value = {"_id": vk_id}
        else:
            friends_collection.collection.find_one.return_value = None
        
        result = friends_collection.is_in_db(vk_id)
        assert result == expected


class TestIntegrationWithMongo:
    @pytest.fixture(scope="class")
    def mongo_client(self):
        client = MongoClient(MONGO_URI)
        yield client
        client.close()
    
    @pytest.fixture
    def test_db(self, mongo_client):
        db = mongo_client.test_database
        yield db
        mongo_client.drop_database(MONGO_TEST_DB_NAME)
    
    @pytest.fixture
    def friends_collection_real(self, test_db):
        collection = test_db.friends
        return FriendsCollection(collection, True, timedelta(days=14))
    
    @pytest.mark.integration
    def test_real_mongo_operations(self, friends_collection_real):
        vk_id = 12345
        
        assert not friends_collection_real.is_in_db(vk_id)
        
        friends_data = Mock()
        friends_data.items = [1, 2, 3, 4, 5]
        
        friends_collection_real._new_record(vk_id, friends_data)
        
        assert friends_collection_real.is_in_db(vk_id)
        
        record = friends_collection_real.get_by_vk_id(vk_id)
        assert record._id == vk_id
        assert record.active_friends == friends_data.items


if __name__ == "__main__":
    unittest.main(verbosity=2)