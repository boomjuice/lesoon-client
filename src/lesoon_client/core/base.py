""" client基类模块."""
import inspect
import json
import logging
import re
import typing as t
from concurrent.futures import ThreadPoolExecutor

import requests
from lesoon_common.utils.base import AttributeDict

from lesoon_client.core.exceptions import ClientException


class BaseClient:
    """
    为应用服务提供远程调用功能,
    注意：本基类不做任何异常处理，异常处理需子类实现.
    Attributes:
        base_url: 域名,默认为cls.BASE_URL
        url_prefix: url前缀
    """
    BASE_URL: str = ''

    URL_PREFIX: str = ''

    http = requests.Session()

    executor = ThreadPoolExecutor(thread_name_prefix='app_client')

    @property
    def log(self):
        if self._log is None:
            self._log = logging.getLogger(self.__class__.__module__ + '.' +
                                          self.__class__.__name__)
            if not self._log.handlers:
                self._log.addHandler(self.logger_handler)
        return self._log

    def __init__(self,
                 base_url: t.Optional[str] = None,
                 url_prefix: t.Optional[str] = None):
        self.base_url = base_url or self.BASE_URL
        self.url_prefix = url_prefix or self.URL_PREFIX
        self._log = None
        self.logger_handler = logging.StreamHandler()

    def _handle_pre_request(self, method: str, kwargs: dict):
        """ 请求前预处理."""
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        headers = kwargs['headers']
        if 'Content_Type' not in headers and 'content_type' not in headers:
            kwargs['headers']['Content-Type'] = 'application/json'

    def _handle_request_except(self, e: ClientException, func: t.Callable,
                               *args, **kwargs):
        raise e

    def _build_uri_prefix(self, kwargs: dict):
        return self.base_url + self.url_prefix

    def request(self, method: str, rule: str, **kwargs):
        self._handle_pre_request(method, kwargs)
        uri_prefix = self._build_uri_prefix(kwargs)
        request_url = re.sub(r'(?<!:)//', '/', uri_prefix + rule)
        try:
            return self._request(method, request_url, **kwargs)
        except ClientException as e:
            return self._handle_request_except(e, self.request, method,
                                               request_url, **kwargs)

    def _request(
        self,
        method: str,
        request_url: str,
        **kwargs,
    ):
        """
        发送请求调用.
        这里预留了拓展,子类可以通过kwargs来自定义参数作自定义功能

        Args:
            method: 请求方式 GET/POST/PUT/DELETE...
            request_url: 请求地址
            kwargs: 请求参数以及自定义拓展参数
                    object_hook: 返回类型，用于做返回结果类型转换
                    object_key_hook: 返回类型，用于做返回结果类型转换
                    其余请求参数参考 :func:`requests.sessions.request`

        """
        # http.request函数签名所定义的参数
        allow_request_param_key = set(
            inspect.signature(self.http.request).parameters.keys())
        # kwarg中符合http.request函数中的参数
        input_request_param_key = set(
            kwargs.keys()).intersection(allow_request_param_key)

        res: requests.Response = self.http.request(
            method=method,
            url=request_url,
            **{k: v for k, v in kwargs.items() if k in input_request_param_key})
        try:
            res.raise_for_status()
        except requests.RequestException as e:
            self.log.error(
                f'【请求地址】: {request_url}\n'
                f'【请求参数】：{kwargs.get("params", "")} \n {kwargs.get("data", "")}\n'
                f'【异常信息】：{e}')
            raise ClientException(
                client=self, request=e.request, response=e.response)

        result = self._handle_result(res, method, request_url, **kwargs)

        self.log.info(f'\n【请求地址】: {method.upper()} {request_url}'
                      f'\n【请求参数】：{str(kwargs)[:100]}...'
                      f'\n【响应数据】：{str(result)[:100]}...')
        return result

    def _decode_result(self, res: requests.Response):
        """
        解析请求结果.

        Args:
            res: 请求结果
            object_hook: 对象钩子
            object_key_hook: 对象键值钩子

        Returns:
            res: 解析结果
        """

        try:
            res = res.json(object_hook=AttributeDict, strict=False)
        except (TypeError, ValueError) as e:
            self.log.error(f'无法将调用结果转化为json:{e}', exc_info=True)
            return res.text
        return res

    def _handle_result(
        self,
        res: requests.Response,
        method: str,
        request_url: str,
        **kwargs,
    ):
        """
        处理请求结果.
        包含返回码处理,序列化结果,以及自定义结果处理。

        Attributes:
            res: 调用结果
            method: 调用方法
            request_url: 请求url
            kwargs: 请求参数以及自定义拓展参数
                    object_hook: 返回类型，用于做返回结果类型转换
                    请求参数参考 :func:`requests.sessions.request`
        """
        if not isinstance(res, dict):
            result = self._decode_result(res)
        else:
            result = res

        result_processor = kwargs.pop('result_processor', None)

        return result if not result_processor else result_processor(result)

    def GET(self, rule: str, **kwargs):
        return self.request('GET', rule, **kwargs)

    def POST(self, rule: str, **kwargs):
        return self.request('POST', rule, **kwargs)

    def PUT(self, rule: str, **kwargs):
        return self.request('PUT', rule, **kwargs)

    def DELETE(self, rule: str, **kwargs):
        return self.request('DELETE', rule, **kwargs)
