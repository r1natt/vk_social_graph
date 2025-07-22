import logging
import time
from collections import deque
from typing import Union, Optional
from enum import Enum, IntEnum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import requests

from config.config import API_KEY
from models._types import FriendsResponse, UserResponse


logger = logging.getLogger(__name__)

VK_API_VERSION = 5.199
ERROR_RESPONSE = {"count": 0, "items": []}

class HTTPMethods(Enum):
    GET = "get"
    POST = "post"

class VKAPIResource(Enum):
    FRIENDS = "friends.get"
    USERS = "users.get"
    EXECUTE = "execute"  # Для кода на языке VKScript

class VKErrorCode(IntEnum):
    UNKNOWN_ERROR = 1
    APP_DISABLED = 2
    METHOD_NOT_FOUND = 3
    INVALID_SIGNATURE = 4
    AUTH_FAILED = 5
    TOO_MANY_REQUESTS = 6
    PERMISSION_DENIED = 7
    BAD_REQUEST = 8
    SPAM_LIMIT = 9
    INTERNAL_ERROR = 10
    CAPTCHA_NEEDED = 14
    ACCESS_DENIED = 15
    HTTPS_REQUIRED = 16
    VALIDATION_REQUIRED = 17
    PAGE_BLOCKED = 18
    NON_STANDALONE_FORBIDDEN = 20
    STANDALONE_ONLY = 21
    METHOD_DISABLED = 23
    USER_CONFIRM_REQUIRED = 24
    COMMUNITY_TOKEN_INVALID = 27
    APP_TOKEN_INVALID = 28
    METHOD_RATE_LIMIT = 29
    PROFILE_PRIVATE = 30
    PARAM_MISSING_OR_INVALID = 100
    INVALID_API_ID = 101
    INVALID_USER_ID = 113
    INVALID_TIMESTAMP = 150
    ALBUM_ACCESS_DENIED = 200
    AUDIO_ACCESS_DENIED = 201
    GROUP_ACCESS_DENIED = 203
    ALBUM_FULL = 300
    PAYMENTS_DISABLED = 500
    ADS_NO_ACCESS = 600
    ADS_ERROR = 603

@dataclass
class ErrorSeverity:
    NON_CRITICAL = "non_critical"
    RETRYABLE = "retryable"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class APIError:
    code: int
    message: str
    severity: ErrorSeverity
    is_retryable: bool = False

@dataclass
class APIResponse:
    success: bool
    data: Optional[dict[str, Union[dict, str, int]]]
    error: Optional[APIError]

class ErrorClassifier(ABC):
    @abstractmethod
    def classify_error(self, code: int, message: str) -> ErrorSeverity:
        pass

    @abstractmethod
    def is_retryable(self, code: int) -> bool:
        pass

class VKAPIErrorClassifier(ErrorClassifier):
    NON_CRITICAL = {
        VKErrorCode.PERMISSION_DENIED,
        VKErrorCode.ACCESS_DENIED,
        VKErrorCode.PAGE_BLOCKED,
        VKErrorCode.PROFILE_PRIVATE,
        VKErrorCode.ALBUM_ACCESS_DENIED,
        VKErrorCode.AUDIO_ACCESS_DENIED,
        VKErrorCode.GROUP_ACCESS_DENIED
    }

    RETRYABLE = {
        VKErrorCode.TOO_MANY_REQUESTS,
        VKErrorCode.SPAM_LIMIT,
        VKErrorCode.INTERNAL_ERROR,
        VKErrorCode.CAPTCHA_NEEDED,
        VKErrorCode.METHOD_RATE_LIMIT
    }

    CRITICAL = {
        VKErrorCode.UNKNOWN_ERROR,
        VKErrorCode.APP_DISABLED,
        VKErrorCode.METHOD_NOT_FOUND,
        VKErrorCode.INVALID_SIGNATURE,
        VKErrorCode.AUTH_FAILED,
        VKErrorCode.BAD_REQUEST,
        VKErrorCode.HTTPS_REQUIRED,
        VKErrorCode.VALIDATION_REQUIRED,
        VKErrorCode.NON_STANDALONE_FORBIDDEN,
        VKErrorCode.STANDALONE_ONLY,
        VKErrorCode.METHOD_DISABLED,
        VKErrorCode.USER_CONFIRM_REQUIRED,
        VKErrorCode.COMMUNITY_TOKEN_INVALID,
        VKErrorCode.APP_TOKEN_INVALID,
        VKErrorCode.PARAM_MISSING_OR_INVALID,
        VKErrorCode.INVALID_API_ID,
        VKErrorCode.INVALID_USER_ID,
        VKErrorCode.INVALID_TIMESTAMP,
        VKErrorCode.ALBUM_FULL,
        VKErrorCode.PAYMENTS_DISABLED,
        VKErrorCode.ADS_NO_ACCESS,
        VKErrorCode.ADS_ERROR
    }

    def classify_error(self, code: int, message: int):
        if code in self.NON_CRITICAL or code in self.RETRYABLE:
            return ErrorSeverity.NON_CRITICAL
        elif code in self.CRITICAL:
            logger.critical("critical error code: %s, msg: %s", code, message)
            return ErrorSeverity.CRITICAL
        else:
            logger.critical("unknown error code: %s, msg: %s", code, message)
            return ErrorSeverity.UNKNOWN

    def is_retryable(self, code: int) -> bool:
        if code in self.RETRYABLE:
            return True
        return False


class ResponseParser(ABC):
    @abstractmethod
    def parse_response(self, response: requests.Response) -> APIResponse:
        pass

class JSONResponseParser(ResponseParser):
    def __init__(self, error_classifier: ErrorClassifier):
        self.error_classifier = error_classifier

    def parse_response(self, response: requests.Response) -> APIResponse:
        response_json = response.json()

        if "error" in response_json.keys():
            error = response_json["error"]
            code = error["error_code"]
            message = error["error_msg"]

            severity = self.error_classifier.classify_error(code, message)
            is_retryable = self.error_classifier.is_retryable(code)

            logger.info("response error: %s - %s", code, message)
            return APIResponse(
                success=False,
                data=None,
                error=APIError(
                    code=code,
                    message=message,
                    severity=severity,
                    is_retryable=is_retryable
                )
            )
        else:
            return APIResponse(
                success=True,
                data=response_json,
                error=None
            )

class RequestTracker(ABC):
    @abstractmethod
    def acquire(self) -> None:
        pass

class SynchronousRequestTracker(RequestTracker):
    """
    Апи имеют ограничения на количество запросов в секунду (Request Per Second).
    Данный класс отслеживает RPS и ждет, исчерпан лимит запросов за последнюю
    секунду
    """

    def __init__(self, excepted_rps: int = 5):
        self.request_times = deque()

        self.excepted_rps = excepted_rps

    def acquire(self) -> None:
        """
        Проверяет время запросов в request_times и если количество запросов было
        равное значению excepted_rps и все они были менее секунды назад, то
        функция останавливает всю программу на время, через которое можно будет
        снова отправить запрос
        """
        logger.debug("Access to acquire")
        while True:
            now = time.monotonic()

            while self.request_times and self.request_times[0] <= now - 1:
                self.request_times.popleft()

            if len(self.request_times) < self.excepted_rps:
                self.request_times.append(now)
                logger.debug("Acquire release")
                break
            else:
                wait_time = self.request_times[0] + 1 - now
                time.sleep(wait_time)

class RetryStrategy(ABC):
    @abstractmethod
    def should_retry(self, attempt, response: APIResponse) -> bool:
        pass

    @abstractmethod
    def get_delay(self, attempt) -> float:
        pass

class ExponentialBackoffRetryStrategy(RetryStrategy):
    def __init__(self, max_retries=3):
        self.base_delay = 1  # задержка в 1 секунду
        self.max_retries = max_retries

    def should_retry(self, attempt: int, response: APIResponse) -> bool:
        if attempt >= self.max_retries:
            return False
        return response.error.is_retryable

    def get_delay(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)


class APIClient():
    def __init__(self,
        error_classifier: ErrorClassifier,
        response_parser: ResponseParser,
        request_tracker: RequestTracker,
        retry_strategy: RetryStrategy
    ):
        self.error_classifier = error_classifier
        self.response_parser = response_parser
        self.request_tracker = request_tracker
        self.retry_strategy = retry_strategy

        self.request_exceptions = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        )

    def make_request(self,
        method: HTTPMethods,
        url: str,
        params: dict[str, Union[str, int, list[str]]]
    ) -> APIResponse:
        attempt = 0

        while True:
            try:
                self.request_tracker.acquire()

                response = self._execute_request(method, url, params)

                parsed_response = self.response_parser.parse_response(response)

                if not(parsed_response.error) or \
                    parsed_response.error.severity is ErrorSeverity.NON_CRITICAL:
                    return parsed_response

                if self.retry_strategy.should_retry(attempt, parsed_response):
                    time.sleep(self.retry_strategy.get_delay(attempt))
                else:
                    logger.error("not retryable error: %s %s", url, params)
            except self.request_exceptions:
                network_error = APIResponse(
                    success=False,
                    data=None,
                    error=APIError(
                        code=0,
                        message="Netwotk Error",
                        severity=ErrorSeverity.CRITICAL,
                        is_retryable=True
                    )
                )

                if self.retry_strategy.should_retry(attempt, network_error):
                    time.sleep(self.retry_strategy.get_delay(attempt))
                else:
                    logger.error("not retryable error: %s %s", url, params)
                attempt += 1
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.exception(e)
                unknown_error = APIResponse(
                    success=False,
                    data=None,
                    error=APIError(
                        code=0,
                        message="Unknown Error",
                        severity=ErrorSeverity.CRITICAL,
                        is_retryable=False
                    )
                )
                return unknown_error

    def _execute_request(self,
        method: HTTPMethods,
        url: str,
        params: dict[str, Union[str, int, list[str]]]
    ) -> requests.Response:
        match method:
            case HTTPMethods.GET:
                return requests.get(url, params=params, timeout=1)
            case HTTPMethods.POST:
                return requests.post(url, params=params, timeout=1)
            case _:
                raise ValueError(f"Неизвестный тип запроса: {method}")

class APIResponseToPydanticConverter:
    def friends(self, response: APIResponse) -> FriendsResponse:
        empty_model = FriendsResponse(count=0, items=[])

        if response.data:
            response_data = response.data
            payload = response_data["response"]

            try:
                return FriendsResponse(**payload)
            except ValueError as e:
                # Pydantic ValidationError наследуется от ValueError
                logger.exception("Pydantic Validation Error: %s", e)
                return empty_model
        return empty_model

    def users(self, response: APIResponse) -> list[UserResponse]:
        empty_response = []

        if response.data:
            response_data = response.data
            payload = response_data["response"]

            try:
                return [UserResponse(**item) for item in payload]
            except ValueError as e:
                # Pydantic ValidationError наследуется от ValueError
                logger.exception("Pydantic Validation Error: %s", e)
                return empty_response
        return empty_response

class VKAPIClient(APIClient):
    def __init__(self):
        error_classifier = VKAPIErrorClassifier()
        response_parser = JSONResponseParser(error_classifier)
        request_tracker = SynchronousRequestTracker()
        retry_strategy = ExponentialBackoffRetryStrategy()

        super().__init__(
            error_classifier,
            response_parser,
            request_tracker,
            retry_strategy
        )

        self.base_url = "https://api.vk.com/method"

    def request(self,
        method,
        resource: VKAPIResource,
        params: dict[str, Union[str, int, list[str]]]
    ) -> APIResponse:
        params.update(
            {
                "access_token": API_KEY,
                "v": VK_API_VERSION
            }
        )

        url = f"{self.base_url}/{resource.value}"

        return self.make_request(
            method,
            url,
            params
        )

class VKAPIInterface:
    def __init__(self, client: VKAPIClient):
        self.client = client
        self.converter = APIResponseToPydanticConverter()

    def get_friends(self, vk_id: int) -> FriendsResponse:
        params = {
            "user_id": vk_id,
            "order": "hints",
            "count": 1000
        }

        response = self.client.request(
            HTTPMethods.GET,
            VKAPIResource.FRIENDS,
            params
        )

        pydantic_model = self.converter.friends(response)

        logger.info("id: %s; count friends: %s", vk_id, len(pydantic_model.items))

        return pydantic_model

    def get_users(self, vk_ids: int | list[int]) -> list[UserResponse]:
        if isinstance(vk_ids, int):
            vk_ids = [vk_ids]
        params={
            "user_ids": vk_ids,
            "access_token": API_KEY,
            "v": VK_API_VERSION,
            "fields": [
                "activities","about","blacklisted","blacklisted_by_me","books",
                "bdate","can_be_invited_group","can_post","can_see_all_posts",
                "can_see_audio","can_send_friend_request","can_write_private_message",
                "career","common_count","connections","contacts","city",
                "crop_photo","domain","education","exports","followers_count",
                "friend_status","has_photo","has_mobile","home_town","photo_100",
                "photo_200","photo_200_orig","photo_400_orig","photo_50","sex",
                "site","schools","screen_name","status","verified","games",
                "interests","is_favorite","is_friend","is_hidden_from_feed",
                "last_seen","maiden_name","movies","music","nickname",
                "occupation","online","personal","photo_id","photo_max",
                "photo_max_orig","quotes","relation","relatives","timezone",
                "tv","universities","is_verified"
            ]
        }

        response = self.client.request(
            HTTPMethods.GET,
            VKAPIResource.USERS,
            params
        )

        logger.info(vk_ids)

        pydantic_model = self.converter.users(response)

        return pydantic_model

class VKAPICodeInterface:
    def __init__(self, client: VKAPIClient):
        self.client = client
        self.converter = APIResponseToPydanticConverter()

    def _execute(self, code):
        params = {
            "code": code
        }

        return self.client.request(
            HTTPMethods.GET,
            VKAPIResource.EXECUTE,
            params
        )

    def get_friends(self, vk_ids: list[int]):
        code = f"""
        var user_ids = {vk_ids}; // до 25 пользователей
        var result = [];
        var i = 0;

        while (i < user_ids.length) {{
            var uid = user_ids[i];
            var friends = API.friends.get({{ user_id: uid, order: "hints", count: 1000 }}).items;
            result.push({{ "id": uid, "friends": friends }});
            i = i + 1;
        }}

        return result;
        """

        return self._execute(code)

    def get_users(self, vk_id: int | list[int]):
        code = f"""
        var user_ids = {vk_id};

        var users = API.users.get({{ "user_ids":user_ids }});

        return users;
        """

        return self._execute(code)
