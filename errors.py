from logger import reqs_logger 


class ExpiredToken(Exception):
    pass


class Errors:
    def __init__(self, response: dict):
        self.response = response
        self.is_error = False
        self.code = -1

        self.check()

    def _get_vk_id_from_error_response(self):
        params = self.response["error"]["request_params"]
        for param_dict in params:
            if param_dict["key"] == "user_id":
                return param_dict["value"]
        return None

    def _is_error_in_response(self):
        if 'error' in self.response:
            self.is_error = True
            self.code = self.response["error"]["error_code"]
        return self.is_error

    def check(self):
        if self._is_error_in_response():
            self.match_codes()
        return 

    def match_codes(self):
        match self.code:
            case 5:
                raise ExpiredToken("Update access token")
            case 30:
                _id = self._get_vk_id_from_error_response()
                reqs_logger.debug(f"profile {_id} is private")
