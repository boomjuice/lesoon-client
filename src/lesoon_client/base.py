""" client基类模块."""
import json
import logging
import typing as t
from concurrent.futures import ThreadPoolExecutor
from urllib import parse

import requests  # type:ignore

from .exceptions import RemoteCallError
from .utils import set_default_headers


class BaseClient:
    BASE_URL: str = ""

    URL_PREFIX: str = ""

    http = requests.Session()

    executor = ThreadPoolExecutor(thread_name_prefix="app_client")

    @property
    def log(self):
        if not self._log:
            self._log = logging.getLogger(__name__)
            self._log.addHandler(logging.StreamHandler())
        return self._log

    def __init__(self, base_url: t.Optional[str] = None):
        self.base_url = base_url or self.BASE_URL
        self._log = None

    def _handle_pre_request(self, method: str, uri: str, kwargs: dict):
        set_default_headers(request_kwargs=kwargs)

    def build_uri(self, rule: str, **kwargs):
        url_prefix = kwargs.pop("url_prefix", self.URL_PREFIX)
        if not rule.startswith(url_prefix):
            url = (url_prefix + rule).replace("//", "/")
        else:
            url = rule
        return url

    def request(self, method: str, rule: str, **kwargs):
        uri = self.build_uri(rule=rule, **kwargs)

        base_url = kwargs.pop("base_url", self.base_url)
        request_url = parse.urljoin(base_url, uri)

        self._handle_pre_request(method, uri, kwargs)

        return self._request(method, request_url, **kwargs)

    def _request(
        self,
        method: str,
        request_url: str,
        **kwargs,
    ):
        """

        :param method: 请求方式 GET/POST/PUT/DELETE...
        :param request_url: 请求地址
        :param kwargs: 参考 :func:`requests.sessions.request`
        :return:
        """
        res: requests.Response = self.http.request(
            method=method, url=request_url, **kwargs
        )
        try:
            res.raise_for_status()
        except requests.RequestException as e:
            msg = (
                f"\n【请求地址】: {method.upper()} {request_url}"
                f"\n【请求参数】：{kwargs}"
                f"\n【异常信息】：{e}"
            )
            self.log.error(msg)
            raise RemoteCallError(msg=msg, request=e.request, response=e.response)

        result = self._handle_result(res, method, request_url, **kwargs)

        self.log.debug(
            f"\n【请求地址】: {method.upper()} {request_url}"
            f"\n【请求参数】：{kwargs}"
            f"\n【响应数据】：{result}"
        )
        return result

    def _decode_result(self, res: requests.Response):
        """解析请求结果."""
        try:
            res = res.json()
        except json.JSONDecodeError:
            self.log.debug("无法将response解析为json", exc_info=True)
            res = res.text
        return res

    def _handle_result(
        self,
        res: requests.Response,
        method: str,
        request_url: str,
        **kwargs,
    ):
        """处理请求结果.
        包含返回码处理,序列化结果,以及自定义结果处理。
        """
        if not isinstance(res, dict):
            result = self._decode_result(res)
        else:
            result = res

        return result

    def GET(self, rule: str, **kwargs):
        return self.request("GET", rule, **kwargs)

    def POST(self, rule: str, **kwargs):
        return self.request("POST", rule, **kwargs)

    def PUT(self, rule: str, **kwargs):
        return self.request("PUT", rule, **kwargs)

    def DELETE(self, rule: str, **kwargs):
        return self.request("DELETE", rule, **kwargs)
