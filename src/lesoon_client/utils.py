def set_default_headers(request_kwargs: dict):
    """设置请求头参数."""
    if "headers" not in request_kwargs:
        request_kwargs["headers"] = dict()

    request_kwargs["headers"]["Content-Type"] = "application/json"


def set_token(request_kwargs: dict):
    """设置请求token."""
    from lesoon_common import request  # type:ignore
    from lesoon_common.utils.jwt import create_system_token  # type:ignore

    if "headers" not in request_kwargs:
        request_kwargs["headers"] = dict()

    token = ""
    try:
        token = request.token
    except RuntimeError:
        pass
    request_kwargs["headers"]["token"] = token or create_system_token()
