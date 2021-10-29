import pytest
from lesoon_common.code import ResponseCode
from lesoon_common.exceptions import ServiceError
from lesoon_common.response import Response

from lesoon_client import LesoonClient


class SimpleClient(LesoonClient):
    BASE_URL = ''
    URL_PREFIX = '/simple'

    def _handle_pre_request(self, method: str, uri: str, kwargs: dict):
        super(LesoonClient, self)._handle_pre_request(method, uri, kwargs)
        self.inherit_custom_headers(kwargs)
        self.inherit_trace_headers(kwargs)


class TestLesoonClient:
    client = None

    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, server):
        cls.client = SimpleClient(base_url=server)

    def test_custom_headers(self):
        headers = {'user-speciality': 'userId=111'}
        resp = self.client.GET('/', headers=headers)
        assert resp['headers'].get(
            'user-speciality') == headers['user-speciality']

    def test_trace_headers(self):
        trace_headers = {
            'x-request-id': '123456',
            'X-B3-TraceId': '062b6c669aa919952a61d5c69015104b',
            'X-B3-SpanId': '3d18c271eaf03bfa',
            'X-B3-Sampled': '1'
        }
        resp = self.client.GET('/', headers=trace_headers)
        assert all([
            trace_key.lower() in resp['headers']
            for trace_key in trace_headers.keys()
        ])

    def test_http_exception(self):
        with pytest.raises(ServiceError):
            self.client.GET('/httpException')

    def test_service_unavailable(self):
        r = self.client.GET('/serviceUnavailable')
        r = Response.load(r)
        assert r.code == ResponseCode.Success.code
        assert r.msg == '系统繁忙,请稍后重试'
