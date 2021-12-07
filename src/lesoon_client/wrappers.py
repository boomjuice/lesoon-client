import json
import os
import typing as t

import requests

from lesoon_client.base import BaseClient

try:
    from lesoon_common import ResponseCode
    from lesoon_common.globals import request
    from lesoon_common import ServiceError
    from lesoon_common.dataclass.req import PageParam
except ImportError:
    raise ImportError('无法从lesoon-common导入模块,请检查是否已安装lesoon-common')


class LesoonClient(BaseClient):
    BASE_URL = os.environ.get('BASE_URL', '')

    MODULE_NAME = ''

    def __init__(self, *args, **kwargs):
        from flask.logging import default_handler

        super().__init__(*args, **kwargs)

        self.logger_handler = default_handler

    @staticmethod
    def set_token(kwargs):
        from lesoon_common.utils.jwt import create_system_token
        # 请求token
        token = ''
        try:
            token = request.token
        except RuntimeError:
            pass
        kwargs['headers']['token'] = token or create_system_token()

    @staticmethod
    def inherit_custom_headers(kwargs):
        """ 从headers继承自定义的key-value."""
        from flask.ctx import has_request_context
        if has_request_context() and 'user-speciality' in request.headers.keys(
        ):
            kwargs['headers']['user-speciality'] = request.headers.get(
                'user-speciality')

    def inherit_trace_headers(self, kwargs):
        """ 从headers继承链路跟踪的key-value."""
        try:
            from opentracing.propagation import Format
            from opentracing_instrumentation.request_context import get_current_span
            from flask.ctx import has_request_context
            from flask.globals import current_app
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

    def check_base_url(self):
        """
        检查base_url是否有值.
        self.base_url为空时, 如果此时在应用内则取取应用配置
        """
        if self.base_url:
            return
        else:
            from flask.ctx import has_app_context
            from flask.globals import current_app
            if has_app_context() and current_app.config.get('BASE_URL'):
                # 如果是在应用内调用则直接取配置
                self.base_url = current_app.config['BASE_URL']
            else:
                raise RuntimeError('Client调用缺少BASE_URL参数,请检查相关配置')

    def _handle_pre_request(self, method: str, uri: str, kwargs: dict):
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
        super()._handle_pre_request(method, uri, kwargs)
        self.check_base_url()
        self.set_token(kwargs)
        self.inherit_custom_headers(kwargs)
        self.inherit_trace_headers(kwargs)

    def build_uri(self, rule: str, **kwargs) -> str:
        """
        拓展uri构建.
        新增module_name参数,减少重复配置
        real_uri = url_prefix + module_name + rule
        Args:
            rule:
            **kwargs:

        Returns:

        """
        url_prefix = kwargs.pop('url_prefix', self.URL_PREFIX)
        module_name = kwargs.pop('module_name', self.MODULE_NAME)

        uri = (url_prefix + module_name + rule).replace('//', '/')
        return uri

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
        from werkzeug.exceptions import ServiceUnavailable
        from lesoon_common import success_response

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
            if kwargs.get('load_response', False):
                return self.load_response(result, method, request_url, **kwargs)
            else:
                return result
        except Exception:
            if not kwargs.pop('silent', False):
                raise
            else:
                return result

    def load_response(self, result: t.Any, method: str, request_url: str,
                      **kwargs):
        if isinstance(result, dict) and 'flag' in result:
            from lesoon_common import Response as LesoonResponse
            resp = LesoonResponse.load(result)
            if resp.code != ResponseCode.Success.code:
                self.log.error(f'\n【请求地址】: {method.upper()} {request_url}' +
                               f'\n【异常信息】：{resp.flag}' + f'\n【请求参数】：{kwargs}')
                raise ServiceError(code=ResponseCode.RemoteCallError)
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
        raise NotImplementedError()

    def create(self, data: dict):
        raise NotImplementedError()

    def create_many(self, data_list: t.List[dict]):
        raise NotImplementedError()

    def update(self, data: dict):
        raise NotImplementedError()

    def update_many(self, data_list: t.List[dict]):
        raise NotImplementedError()

    def remove_many(self, ids: t.List[str]):
        raise NotImplementedError()


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
        if 'params' not in kwargs:
            kwargs['params'] = {}

        kwargs['params'].update({
            'ifPage': int(page_param.if_page),
            'where': json.dumps(page_param.where),
        })
        if page_param.if_page:
            kwargs['params'].update({
                'page': page_param.page,
                'pageSize': page_param.page_size
            })

        return self.GET(rule=rule, load_response=True, **kwargs)

    def page_get(
        self,
        page_param: PageParam,
        **kwargs,
    ):
        return self._page_get(rule='', page_param=page_param, **kwargs)

    def create(self, data: dict):
        return self.POST('', json=data, load_response=True)

    def create_many(self, data_list: t.List[dict]):
        return self.POST('', json=data_list, load_response=True)

    def update(self, data: dict):
        return self.PUT('', json=data, load_response=True)

    def update_many(self, data_list: t.List[dict]):
        return self.PUT('', json=data_list, load_response=True)

    def remove_many(self, ids: t.List[str]):
        return self.DELETE('', json=ids, load_response=True)


class JavaClient(LesoonClient):

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
        if 'params' not in kwargs:
            kwargs['params'] = {}

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

        return self.GET(rule=rule, load_response=True, **kwargs)

    def page_get(
        self,
        page_param: PageParam,
        **kwargs,
    ):
        return self._page_get(rule='/page', page_param=page_param, **kwargs)

    def create(self, data: dict):
        return self.POST('', json=data, load_response=True)

    def create_many(self, data_list: t.List[dict]):
        return self.POST('/batch', json=data_list, load_response=True)

    def update(self, data: dict):
        return self.PUT('', json=data, load_response=True)

    def update_many(self, data_list: t.List[dict]):
        return self.PUT('/batch', json=data_list, load_response=True)

    def remove_many(self, ids: t.List[str]):
        return self.DELETE('/unlimited/batch', json=ids, load_response=True)
