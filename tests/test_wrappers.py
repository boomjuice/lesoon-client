import pytest

from lesoon_common.code import ResponseCode
from lesoon_common.exceptions import ServiceError
from lesoon_common.response import Response

from lesoon_client import LesoonClient


class SimpleClient(LesoonClient):
    BASE_URL = ""
    URL_PREFIX = "/simple"

    def _handle_pre_request(self, method: str, uri: str, kwargs: dict):
        super(LesoonClient, self)._handle_pre_request(method, uri, kwargs)
        self.inherit_headers(kwargs)


class TestLesoonClient:
    client = None

    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, server):
        cls.client = SimpleClient(base_url=server)

    def test_http_exception(self):
        with pytest.raises(ServiceError):
            self.client.GET("/httpException")

    def test_service_unavailable(self):
        r = self.client.GET("/serviceUnavailable")
        r = Response.load(r)
        assert r.code == ResponseCode.Success.code
        assert r.msg == "系统繁忙,请稍后重试"
