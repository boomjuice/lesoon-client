import json
import os
import typing as t

from .base import BaseClient
from .exceptions import RemoteCallError
from .utils import set_token

try:
    from lesoon_common import Response as LesoonResponse
    from lesoon_common import ResponseCode
    from lesoon_common.dataclass.req import PageParam
except ImportError:
    print("无法从lesoon-common导入模块,请检查是否已安装lesoon-common")
    LesoonResponse = None
    ResponseCode = None
    PageParam = None


class LesoonClient(BaseClient):
    BASE_URL = os.environ.get("BASE_URL", "")

    MODULE_NAME = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _handle_pre_request(self, method: str, uri: str, kwargs: dict):
        super()._handle_pre_request(method, uri, kwargs)
        set_token(kwargs)

    def build_uri(self, rule: str, **kwargs):
        url_prefix = kwargs.pop("url_prefix", self.URL_PREFIX)
        module_name = kwargs.pop("module_name", self.MODULE_NAME)

        uri = (url_prefix + module_name + rule).replace("//", "/")
        return uri

    def _handle_result(
        self,
        res,
        method: str,
        request_url: str,
        **kwargs,
    ):

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

    def python_page_get(
        self,
        rule: str,
        page_param: PageParam,
        **kwargs,
    ):
        """
        python 体系分页查询
        :param rule: 资源路径
        :param page_param: 分页相关参数
        :param kwargs: 参考 :func:requests.Session.request
        :return: lesoon_common.Response
        """
        if "params" not in kwargs:
            kwargs["params"] = {}

        kwargs["params"].update(
            {
                "ifPage": int(page_param.if_page),
                "where": json.dumps(page_param.where),
            }
        )
        if page_param.if_page:
            kwargs["params"].update(
                {"page": page_param.page, "pageSize": page_param.page_size}
            )

        return self.GET(rule=rule, **kwargs)

    def java_page_get(
        self,
        rule: str,
        page_param: PageParam,
        **kwargs,
    ):
        """
        java 体系分页查询
        :param rule: 资源路径
        :param page_param: 分页相关参数
        :param kwargs: 参考 :func:requests.Session.request
        :return: lesoon_common.Response
        """
        if "params" not in kwargs:
            kwargs["params"] = {}

        if not page_param.if_page:
            # petrel体系中带page后缀为分页,反之不分页
            rule = rule.replace("/page", "")
        else:
            kwargs["params"].update(
                {"page.pn": page_param.page, "page.size": page_param.page_size}
            )

        if page_param.where:
            kwargs["params"].update(
                {f"search.{k}": v for k, v in page_param.where.items()}
            )

        return self.GET(rule=rule, **kwargs)


class IdCenterClient(LesoonClient):
    URL_PREFIX = "/petrel/lesoon-id-center-api"

    def ui(self, biz_type: str):
        """获取自增ID."""
        params = {"bizType": biz_type}
        return self.GET("/generatorApi/segment/id", params=params)

    def batch_get_segment_id(self, biz_type: str, count: int):
        """批量获取自增ID."""
        params = {"bizType": biz_type, "count": count}
        return self.GET("/generatorApi/batch/segment/id", params=params)

    def get_uid(self):
        """获取UID."""
        return self.GET("/generatorApi/uid")

    def batch_get_uid(self, count: int):
        """批量获取UID."""
        params = {"count": count}
        return self.GET("/generatorApi/batch/uid", params=params)

    def get_serial_no(
        self, company_id: str, code_rule_no: str, dynamic_value: t.Optional[str] = None
    ):
        """获取编码规则流水号，例如: 单号."""
        params = {
            "companyId": company_id,
            "codeRuleNo": code_rule_no,
            "dynamicValue": dynamic_value,
        }
        return self.GET("/generatorApi/code/no", params=params)

    def batch_get_serial_no(
        self,
        company_id: str,
        code_rule_no: str,
        num: int,
        dynamic_value: t.Optional[str] = None,
    ):
        """批量获取编码规则流水号，例如: 单号."""
        params = {
            "companyId": company_id,
            "codeRuleNo": code_rule_no,
            "num": num,
            "dynamicValue": dynamic_value,
        }
        return self.GET("/generatorApi/batch/code/no", params=params)
