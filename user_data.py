import json


class UserData():
    def __init__(self, owner_id, user_data):
        self.user_data = user_data
        self.owner_id = owner_id
        self._cook_user_data()

    def __repr__(self):
        print(self.user_data)
        return json.dumps(self.user_data, ensure_ascii=False)

    def _cook_user_data(self):
        self._user_handler()
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

    def _user_handler(self):
        self.user_data["_id"] = self.user_data["id"]
        del self.user_data["id"]
        self.user_data["first_name"] = self.user_data["first_name"].replace("/", "-").replace("_", "-")
        self.user_data["last_name"] = self.user_data["last_name"].replace("/", "-").replace("_", "-")
