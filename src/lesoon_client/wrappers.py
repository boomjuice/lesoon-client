import json
import os
import typing as t

import requests
from flask.logging import default_handler
from lesoon_common import ClientResponse
from lesoon_common import LesoonFlask
from lesoon_common import Response
from lesoon_common import ResponseCode
from lesoon_common import success_response
from lesoon_common.ctx import has_app_context
from lesoon_common.ctx import has_request_context
from lesoon_common.dataclass.req import PageParam
from lesoon_common.dataclass.user import TokenUser
from lesoon_common.exceptions import ServiceError
from lesoon_common.globals import current_app
from lesoon_common.globals import current_user
from lesoon_common.globals import request
from lesoon_common.response import ResponseBase
from lesoon_common.utils.jwt import create_token
from opentracing.propagation import Format
from opentracing_instrumentation.request_context import get_current_span
from werkzeug.exceptions import ServiceUnavailable

from lesoon_client.base import BaseClient


class LesoonClient(BaseClient):
    """
    Lesoon体系Python调用客户端基类.

    """
    # 提供方名称
    PROVIDER: str = ''

    # 模块名
    MODULE_NAME: str = ''

    # Response类
    RESPONSE_CLS: t.Type[ResponseBase] = ClientResponse

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provider = kwargs.pop('provider', '') or self.PROVIDER
        self.module_name = kwargs.pop('module_name', '') or self.MODULE_NAME
        self.response_class = kwargs.pop('response_cls',
                                         '') or self.RESPONSE_CLS

    def init_app(self, app: LesoonFlask):
        """
        初始化client配置
        支持自定义client.uri_prefix
        Args:
            app: LesoonFlask

        """
        self.logger_handler = default_handler
        current_app.config.setdefault('CLIENT', self._default_config())
        client_config = current_app.config['CLIENT']
        provider_urls = client_config.get('PROVIDER_URLS', {})

        if self.provider in provider_urls:
            self.base_url, self.url_prefix = provider_urls[self.provider], ''
        else:
            self.base_url = client_config['BASE_URL'] or self.base_url

        if 'lesoon-client' not in current_app.extensions:
            current_app.extensions['lesoon-client'] = {}
        current_app.extensions['lesoon-client'][self.provider] = self

    @staticmethod
    def _default_config() -> dict:
        return {'BASE_URL': '', 'PROVIDER_URLS': {}}

    @staticmethod
    def set_token(kwargs):
        # 请求token
        token = ''
        try:
            token = request.token
        except RuntimeError:
            pass
        kwargs['headers']['token'] = token or create_token(TokenUser.new())

    @staticmethod
    def inherit_custom_headers(kwargs):
        """ 从headers继承自定义的key-value."""
        if has_request_context() and 'user-speciality' in request.headers.keys(
        ):
            kwargs['headers']['user-speciality'] = request.headers.get(
                'user-speciality')

    def inherit_trace_headers(self, kwargs):
        """ 从headers继承链路跟踪的key-value."""
        try:
            if has_request_context(
            ) and 'link_tracer' in current_app.extensions:
                # opentracing-B3规范请求头
                link_tracer = current_app.extensions['link_tracer']
                link_tracer.tracer.inject(
                    span_context=link_tracer.get_span().context,
                    format=Format.HTTP_HEADERS,
                    carrier=kwargs['headers'])
                # istio规范请求头
                incoming_header_keys = ['x-request-id', 'x-ot-span-context']
                for key in incoming_header_keys:
                    if value := request.headers.get(key):
                        kwargs['headers'][key] = value
        except Exception as e:
            self.log.warning(f'拷贝链路跟踪请求头异常:{e}')

    def _handle_pre_request(self, method: str, kwargs: dict):
        """
        请求前预处理.
        处理主要包括: 1.检查base_url
                     2.设置请求token
                     3.请求头的继承
        Args:
            method: 请求方法
            uri: 请求uri(即请求资源)
            kwargs:

        """
        super()._handle_pre_request(method, kwargs)
        if has_app_context():
            self.init_app(current_app)
            if current_app.config.get('JWT_ENABLE', False):
                self.set_token(kwargs)
        self.inherit_custom_headers(kwargs)
        self.inherit_trace_headers(kwargs)

    def _build_uri_prefix(self, kwargs: dict):
        return self.base_url + self.url_prefix + self.module_name

    def _request(
        self,
        method: str,
        request_url: str,
        **kwargs,
    ):
        """
        发送请求调用.
        在父类方法上新增异常处理
        注意: 这里对状态为503的请求做了特殊处理(istio熔断问题)
        Args:
            method: 请求方法
            request_url: 请求url

        """

        try:
            result = super()._request(
                method=method, request_url=request_url, **kwargs)
        except requests.HTTPError as e:
            if e.response.status_code == ServiceUnavailable.code:
                result = success_response(msg='系统繁忙,请稍后重试')
            else:
                self.log.error(f'\n【请求地址】: {method.upper()} {request_url}' +
                               f'\n【异常信息】：{e}' + f'\n【请求参数】：{kwargs}')
                raise ServiceError(code=ResponseCode.RemoteCallError)
        return result

    def _handle_result(
        self,
        res,
        method: str,
        request_url: str,
        **kwargs,
    ):
        """
        处理请求结果.
        拓展父类函数,提供以下功能:
                    1. 异常静默(kwargs['silent'])
                    2. 自定义状态码处理(lesoon_common.ResponseCode)
        Args:
            res: 调用结果
            method: 调用方法
            request_url: 请求url
            **kwargs:
                silent: 是否异常静默
                其余参数见父类注释
        """
        result = super()._handle_result(res, method, request_url, **kwargs)
        try:
            if kwargs.pop('load_response', True):
                return self.load_response(result, method, request_url, **kwargs)
            else:
                return result
        except Exception:
            if not kwargs.pop('silent', False):
                raise
            else:
                return self.response_class(
                    code=ResponseCode.Success, result=result)

    def load_response(self, result: t.Any, method: str, request_url: str,
                      **kwargs):
        if isinstance(result, dict) and 'flag' in result:
            resp = self.response_class.load(result)
            if resp.code != ResponseCode.Success.code:
                self.log.error(f'\n【请求地址】: {method.upper()} {request_url}' +
                               f'\n【异常信息】：{resp.flag}' + f'\n【请求参数】：{kwargs}')
                raise ServiceError(
                    code=ResponseCode.RemoteCallError, msg=resp.msg)
            return resp
        else:
            raise ServiceError(
                code=ResponseCode.RemoteCallError,
                msg=f'初始化Response对象异常:{result}')

    def _page_get(
        self,
        rule: str,
        page_param: PageParam,
        **kwargs,
    ):
        """
        分页查询
        Args:
            rule: 资源路径
            page_param: 分页相关参数
            kwargs: 参考 :func:`lesoonClient._request`
        Returns:
            `lesoon_common.Response`
        """
        kwargs.setdefault('params', {})

        kwargs['params'].update({
            'page': page_param.page,
            'pageSize': page_param.page_size,
            'where': json.dumps(page_param.where),
        })

        return self.GET(rule=rule, **kwargs)

    def create(self, data: dict):
        return self.POST('', json=data)

    def create_many(self, data_list: t.List[dict]):
        return self.POST('/batch', json=data_list)

    def update(self, data: dict):
        return self.PUT('', json=data)

    def update_many(self, data_list: t.List[dict]):
        return self.PUT('/batch', json=data_list)

    def remove_many(self, ids: t.List[t.Union[str, int]]):
        return self.DELETE('', json=ids)


class PythonClient(LesoonClient):

    def _page_get(
        self,
        rule: str,
        page_param: PageParam,
        **kwargs,
    ):
        """
        python 体系分页查询
        Args:
            rule: 资源路径
            page_param: 分页相关参数
            kwargs: 参考 :func:`lesoonClient._request`
        Returns:
            `lesoon_common.Response`
        """
        kwargs.setdefault('params', {})
        if page_param.if_page:
            kwargs['params'].update({
                'ifPage': int(page_param.if_page),
            })
        return super()._page_get(rule=rule, page_param=page_param, **kwargs)

    def page_get(
        self,
        page_param: PageParam,
        **kwargs,
    ):
        return self._page_get(rule='', page_param=page_param, **kwargs)


class Java3Client(LesoonClient):

    def _page_get(
        self,
        rule: str,
        page_param: PageParam,
        **kwargs,
    ):
        """
        java 体系分页查询
        Args:
            rule: 资源路径
            page_param: 分页相关参数
            kwargs: 参考 :func:`lesoonClient._request`
        Returns:
            `lesoon_common.Response`

        """
        kwargs.setdefault('params', {})

        if not page_param.if_page:
            # petrel体系中带page后缀为分页,反之不分页
            rule = rule.replace('/page', '')

        return super()._page_get(rule=rule, page_param=page_param, **kwargs)

    def page_get(
        self,
        page_param: PageParam,
        **kwargs,
    ):
        return self._page_get(rule='/page', page_param=page_param, **kwargs)

    def remove_many(self, ids: t.List[t.Union[str, int]]):
        return self.DELETE('/unlimited/batch', json=ids, load_response=True)


class Java2Client(Java3Client):

    RESPONSE_CLS = Response

    def _handle_result(
        self,
        res,
        method: str,
        request_url: str,
        **kwargs,
    ):
        kwargs['silent'] = kwargs.pop('silent', True)
        return super()._handle_result(res, method, request_url, **kwargs)

    def _page_get(
        self,
        rule: str,
        page_param: PageParam,
        **kwargs,
    ):
        """
        java 体系分页查询
        Args:
            rule: 资源路径
            page_param: 分页相关参数
            kwargs: 参考 :func:`lesoonClient._request`
        Returns:
            `lesoon_common.Response`

        """
        kwargs.setdefault('params', {})

        if not page_param.if_page:
            # petrel体系中带page后缀为分页,反之不分页
            rule = rule.replace('/page', '')
        else:
            kwargs['params'].update({
                'page.pn': page_param.page,
                'page.size': page_param.page_size
            })

        if page_param.where:
            kwargs['params'].update(
                {f'search.{k}': v for k, v in page_param.where.items()})

        return self.GET(rule=rule, **kwargs)
