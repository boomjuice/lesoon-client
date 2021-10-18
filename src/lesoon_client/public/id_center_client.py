import typing as t

from lesoon_client.wrappers import LesoonClient


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

    def get_serial_no(self,
                      company_id: str,
                      code_rule_no: str,
                      dynamic_value: t.Optional[str] = None):
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
