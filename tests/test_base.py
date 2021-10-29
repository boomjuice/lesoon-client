import json

import pytest
import requests

from lesoon_client import BaseClient


class SimpleClient(BaseClient):
    BASE_URL = ''
    URL_PREFIX = '/simple'


class TestBaseClient:
    client = None

    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, server):
        cls.client = SimpleClient(base_url=server)

    def test_get(self):
        params = {'text': 'client-get'}
        resp = self.client.GET('/', params=params)
        assert resp['method'] == 'GET'
        assert resp['params'] == params

    def test_post(self):
        params = {'text': 'client-post'}
        data = {'a': 1}
        resp = self.client.POST('/', params=params, data=json.dumps(data))
        assert resp['method'] == 'POST'
        assert resp['params'] == params
        assert resp['data'] == data

    def test_put(self):
        params = {'text': 'client-put'}
        data = {'a': 1}
        resp = self.client.PUT('/', params=params, data=json.dumps(data))
        assert resp['method'] == 'PUT'
        assert resp['params'] == params
        assert resp['data'] == data

    def test_delete(self):
        params = {'text': 'client-delete'}
        data = {'a': 1}
        resp = self.client.DELETE('/', params=params, data=json.dumps(data))
        assert resp['method'] == 'DELETE'
        assert resp['params'] == params
        assert resp['data'] == data

    def test_http_exception(self):
        with pytest.raises(requests.exceptions.HTTPError):
            r = self.client.GET('/simple/httpException')
