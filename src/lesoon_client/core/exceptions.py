import typing as t

import requests
from lesoon_common import ServiceError
from lesoon_common.code import ResponseCode

if t.TYPE_CHECKING:
    from lesoon_client.core.base import BaseClient
    from lesoon_client.wrappers.client import LesoonClient


class ClientException(Exception):

    def __init__(self,
                 client: 'BaseClient',
                 request: t.Optional[requests.Request] = None,
                 response: t.Optional[requests.Response] = None):
        self.client = client
        self.request = request
        self.response = response


class RemoteCallError(ClientException, ServiceError):
    CODE = ResponseCode.RemoteCallError

    def __init__(self,
                 client: 'LesoonClient',
                 errmsg: t.Optional[str] = None,
                 request: t.Optional[requests.Request] = None,
                 response: t.Optional[requests.Response] = None):
        ClientException.__init__(
            self, client=client, request=request, response=response)
        ServiceError.__init__(self, msg_detail=errmsg)
