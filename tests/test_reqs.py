"""
Должны быть включены тесты:
 * успешного запроса users и friends в разных конфигурациях
 * различных ошибок, которые прописаны в errors.
"""

import time
import requests

import unittest
from unittest.mock import patch, MagicMock
from utils.reqs import RequestTracker, get_friends


SUCCESS_RESPONSE = {
    "response": {
        "count": 1,
        "items": [123456789]
    }
}

ERROR_RESPONSE = {
    "response": {
        "count": 1,
        "items": [123456789]
    }
}

class TestGetUserData(unittest.TestCase):
    @patch("utils.reqs.time.sleep", wraps=time.sleep)
    @patch("utils.reqs.requests.get")
    def test_requests(self, mock_get, mock_sleep):
        """Успешность отработки трекера запросов"""
        mock_get.return_value = MagicMock(status_code=200, text=SUCCESS_RESPONSE)

        rt = RequestTracker()

        for _ in range(15):
            rt.send_request("http://httpbin.org/get")
            # Запрос заменяется мокой, url не имеет значения

        assert mock_sleep.called
        assert mock_sleep.call_count == 2
        assert mock_get.call_count == 15

    @patch("utils.reqs.requests.get")
    def test_get_friends_success(self, mock_get):
        """"""
        error = requests.exceptions.SSLError
        mock_get.side_effects = error

        rt = RequestTracker()

        with self.assertRaises(error):
            rt.send_request("http://httpbin.org/get")

    # @patch("utils.reqs.requests.get")
    # def test_get_friends_success(mock_get):
    #     mock_get.return_value = MagicMock(status_code=200, text=SUCCESS_RESPONSE)

    #     result = get_friends(123456789)

    #     assert result is 
    #     assert result.response.count == 1
    #     assert result.response.items == [123456789]
    #     mock_send_request.assert_called_once()