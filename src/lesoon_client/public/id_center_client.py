import typing as t

from lesoon_client.wrappers import Java3Client


class IdCenterClient(Java3Client):
    PROVIDER = 'lesoon-id-center-api'

    URL_PREFIX = '/lesoon-id-center-api'

    MODULE_NAME = '/generatorApi'

    def uid(self, biz_type: str):
        """获取自增ID."""
        params = {'bizType': biz_type}
        return self.GET('/segment/id', params=params)

    def batch_get_segment_id(self, biz_type: str, count: int):
        """批量获取自增ID."""
        params = {'bizType': biz_type, 'count': count}
        return self.GET('/batch/segment/id', params=params)

    def get_uid(self):
        """获取UID."""
        return self.GET('/uid')

    def batch_get_uid(self, count: int):
        """批量获取UID."""
        params = {'count': count}
        return self.GET('/batch/uid', params=params)

    def get_serial_no(self,
                      company_id: str,
                      code_rule_no: str,
                      dynamic_value: t.Optional[str] = None):
        """获取编码规则流水号，例如: 单号."""
        params = {
            'companyId': company_id,
            'codeRuleNo': code_rule_no,
            'dynamicValue': dynamic_value,
        }
        return self.GET('/code/no', params=params)

    def batch_get_serial_no(
        self,
        company_id: str,
        code_rule_no: str,
        num: int,
        dynamic_value: t.Optional[str] = None,
    ):
        """批量获取编码规则流水号，例如: 单号."""
        params = {
            'companyId': company_id,
            'codeRuleNo': code_rule_no,
            'num': num,
            'dynamicValue': dynamic_value,
        }
        return self.GET('/batch/code/no', params=params)
