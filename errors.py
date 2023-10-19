from logger import logger


class ErrorsCheck:
    def __init__(self):
        """
        {"error":
            {"error_code":5,
            "error_msg":"User authorization failed: access_token has expired.",
            "request_params":[
                {"key":"user_id","value":"3...6"},
                ...,
                {"key":"v","value":"5.154"}
                ]
            }
        }
        Выше пример запроса с ошибкой
        """
        pass

def _get_vk_id_in_response(response):
    # данная функция находит user_id который был отправлен в запросе в 
    # ответе, который представлен в __init__
    params = response["error"]["requests_params"]
    for param_dict in params:
        if param_dict["key"] == "user_id":
            return param_dict["value"]
    return None

def error_check(vk_api_response) -> bool | int:
    if 'error' in vk_api_response:
        code = vk_api_response["error"]["error_code"]
        
        match code:
            case 30:
                response = {"id": _get_vk_id_in_response(response),
                            "is_closed": True}
                return 30
            case 5:
                logger.error("Update auth key")
                return 5
            case 18:
                return 18
            case _:
                print("Error", vk_api_response)
                return -1
    return 0  # если нет ошибки, возвращает 0, в ином случае номер ошибки
