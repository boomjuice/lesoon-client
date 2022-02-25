from lesoon_common import request
from lesoon_common import success_response
from lesoon_common.exceptions import ServiceError
from lesoon_restful import Resource
from lesoon_restful import Route
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import ServiceUnavailable


class SimpleResource(Resource):

    class Meta:
        name = 'simple'

    @staticmethod
    def _original_request():
        return {
            'method': request.method,
            'params': request.args,
            'data': request.get_json(silent=True),
            'headers': dict(request.headers.items(lower=True))
        }

    @Route.GET('')
    def get(self):
        return self._original_request()

    @Route.POST('')
    def post(self):
        return self._original_request()

    @Route.PUT('')
    def put(self):
        return self._original_request()

    @Route.DELETE('')
    def delete(self):
        return self._original_request()

    @Route.GET('/standard')
    def standard(self):
        return success_response()

    @Route.GET('/httpException')
    def raise_http_exception(self):
        raise NotFound()

    @Route.GET('/serviceException')
    def raise_server_exception(self):
        raise ServiceError()

    @Route.GET('/serviceUnavailable')
    def raise_service_unavailable(self):
        raise ServiceUnavailable()
