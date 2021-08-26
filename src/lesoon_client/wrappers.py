import json
import os
import typing as t

from .base import BaseClient
from .exceptions import RemoteCallError
from .utils import set_token


class LesoonClient(BaseClient):
    BASE_URL = os.environ.get("BASE_URL", "")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _handle_pre_request(self, method: str, url: str, kwargs: dict):
        super()._handle_pre_request(method, url, kwargs)
        set_token(kwargs)

    def _handle_result(
        self,
        res,
        method: str,
        request_url: str,
        **kwargs,
    ):
        from lesoon_common import Response as LesoonResponse
        from lesoon_common import ResponseCode

        result = super()._handle_result(res, method, request_url, **kwargs)

        if isinstance(result, dict) and "flag" in result:
            resp = LesoonResponse.load(result)
            if resp.code != ResponseCode.Success.code:
                msg = (
                    f"\n【请求地址】: {method.upper()} {request_url}"
                    f"\n【请求参数】：{kwargs}"
                    f"\n【错误信息】：{resp.flag}"
                )
                self.log.error(msg)
                raise RemoteCallError(msg=msg, request=res.request, response=res)
            return resp
        else:
            return result

    def page_get(
        self,
        rule: str,
        page: int,
        page_size: int,
        if_page: bool,
        where: t.Optional[dict] = None,
        **kwargs,
    ):
        """
        分页查询
        :param rule: 资源路径
        :param page: 页码
        :param page_size: 页码数
        :param if_page: 是否分页
        :param where: 过滤条件
        :param kwargs: 参考 :func:requests.Session.request
        :return: lesoon_common.Response
        """
        if "params" not in kwargs:
            kwargs["params"] = {}

        kwargs["params"].update(
            {
                "page": page,
                "pageSize": page_size,
                "ifPage": int(if_page),
                "where": json.dumps(where),
            }
        )

        return self.GET(rule=rule, **kwargs)

    def java_page_get(
        self,
        rule: str,
        page: int,
        page_size: int,
        where: t.Optional[dict] = None,
        **kwargs,
    ):
        """
        java 体系分页查询
        :param rule: 资源路径
        :param page: 页码
        :param page_size: 页码数
        :param where: 过滤条件
        :param kwargs: 参考 :func:requests.Session.request
        :return: lesoon_common.Response
        """
        if "params" not in kwargs:
            kwargs["params"] = {}

        kwargs["params"].update(
            {"page.pn": page, "page.size": page_size},
        )
        if where:
            kwargs["params"].update({f"search.{k}": v for k, v in where.items()})

        return self.GET(rule=rule, **kwargs)
