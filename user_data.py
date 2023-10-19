import json
from datetime import datetime


class User(dict):
    def __init__(self, user_data):
        self.update(user_data)
        self.change_id()

    def change_id(self):
        _id = self["id"]
        del self["id"]
        self["_id"] = _id


class Old:
    def __init__(self, owner_id, user_data):
        self.user_data = user_data
        self.owner_id = owner_id
        self._cook_user_data()

    def __repr__(self):
        return json.dumps(self.user_data, ensure_ascii=False)

    def _cook_user_data(self):
        self._user_add_date()
    
    def _user_add_date(self):
        user_id = self.user_data["_id"]
        del self.user_data["_id"]
        today = datetime.today()
        today = today.strftime("%Y-%m-%d_%H:%M:%S")
        
        updated_data = {}
        updated_data["_id"] = user_id
        updated_data[today] = self.user_data
        self.user_data = updated_data

