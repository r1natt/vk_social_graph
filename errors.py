class Errors:
    def __init__(self, vk_api_response):
        self.vk_api_response = vk_api_response

    def error_checker(self):
        error = False
        if 'error' in self.vk_api_response:
            code = self.vk_api_response["error"]["error_code"]
            
            match code:
                case 30:
                    response = {"id": vk_id,
                                "is_closed": True}
                case 5:
                    print("Update auth key")
                case _:
                    print("Error", self.vk_api_response)
            error = True
        return error
