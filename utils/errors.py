import logging
from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Optional
import requests


logger = logging.getLogger(__name__)


class ErrorAction(Enum):
    SKIP = "SKIP"
    RETRY = "RETRY"
    WAIT = "WAIT"
    STOP = "STOP"


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


ERROR_STRATEGIES = {
    # Критические ошибки - остановка
    VKErrorCode.APP_DISABLED: ErrorAction.STOP,
    VKErrorCode.AUTH_FAILED: ErrorAction.STOP,
    VKErrorCode.COMMUNITY_TOKEN_INVALID: ErrorAction.STOP,
    VKErrorCode.APP_TOKEN_INVALID: ErrorAction.STOP,
    VKErrorCode.INVALID_API_ID: ErrorAction.STOP,
    VKErrorCode.CAPTCHA_NEEDED: ErrorAction.STOP,
    
    # Rate limiting - ожидание
    VKErrorCode.TOO_MANY_REQUESTS: ErrorAction.WAIT,
    VKErrorCode.METHOD_RATE_LIMIT: ErrorAction.WAIT,
    VKErrorCode.SPAM_LIMIT: ErrorAction.WAIT,
    
    # Повторяемые ошибки
    VKErrorCode.INTERNAL_ERROR: ErrorAction.RETRY,
    VKErrorCode.UNKNOWN_ERROR: ErrorAction.RETRY,
    
    # Пропускаемые ошибки (нормальные в парсинге)
    VKErrorCode.ACCESS_DENIED: ErrorAction.SKIP,
    VKErrorCode.PROFILE_PRIVATE: ErrorAction.SKIP,
    VKErrorCode.PAGE_BLOCKED: ErrorAction.SKIP,
    VKErrorCode.PERMISSION_DENIED: ErrorAction.SKIP,
    VKErrorCode.INVALID_USER_ID: ErrorAction.SKIP,
    VKErrorCode.GROUP_ACCESS_DENIED: ErrorAction.SKIP,
    VKErrorCode.ALBUM_ACCESS_DENIED: ErrorAction.SKIP,
    VKErrorCode.AUDIO_ACCESS_DENIED: ErrorAction.SKIP,
    
    # Ошибки параметров - пропуск
    VKErrorCode.BAD_REQUEST: ErrorAction.SKIP,
    VKErrorCode.PARAM_MISSING_OR_INVALID: ErrorAction.SKIP,
    VKErrorCode.METHOD_NOT_FOUND: ErrorAction.SKIP,
}

@dataclass
class ErrorHandlerResult:
    action: ErrorAction
    retry_count: int = 0
    wait_time: float = 0


class VKApiErrorHandler(Exception):
    def handle(self, response: requests.Response, existing_error: Optional[ErrorHandlerResult]):
        if "error" in response.keys():
            error = response["error"]
            code = self._validate_code(error["error_code"])
            message = error["error_msg"]
            action = ERROR_STRATEGIES[code]

            match action:
                case ErrorAction.SKIP:
                    self._skip_error_handler()

    def _validate_code(self, code):
        try:
            return VKErrorCode(code)
        except ValueError:
            raise ValueError(f"Незнакомый код ошибки: {code}")
    
    def _skip_error_handler(self):
        logger.info(f"")
        return ErrorHandlerResult(action=ErrorAction.SKIP)

    def _retry_error_handler(self):
        logger.info()
        return ErrorHandlerResult(action=ErrorAction.RETRY)
    
    def _stop_error_handler(self):
        logger.info()
        return ErrorHandlerResult(action=ErrorAction.WAIT)
    
    def _wait_error_handler(self):
        logger.info()
        return ErrorHandlerResult(action=ErrorAction.STOP)
    
    

