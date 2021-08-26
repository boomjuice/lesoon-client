import typing as t


class RemoteCallError(Exception):
    """远程调用异常"""

    CODE = "3001"

    def __init__(
        self, msg: t.Optional[str] = None, request: t.Any = None, response: t.Any = None
    ):
        self.code = self.CODE
        self.msg = msg or "远程调用异常"
        self.request = request
        self.response = response
