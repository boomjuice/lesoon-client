"""Defines fixtures available to all tests."""
import logging
import threading

import pytest
from examples.config import Config
from werkzeug.serving import make_server


@pytest.fixture
def app():
    from lesoon_common import LesoonFlask
    """Create application for the tests."""
    app = LesoonFlask(__name__, config=Config)
    app.testing = True
    app.logger.setLevel(logging.CRITICAL)
    ctx = app.test_request_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture
def view(app):
    from lesoon_common.view import BaseView
    from lesoon_common import route
    from lesoon_common import request
    from lesoon_common.exceptions import ServiceError
    from werkzeug.exceptions import ServiceUnavailable
    from werkzeug.exceptions import NotFound

    class SimpleView(BaseView):

        @route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def simple(self):
            return {
                'method': request.method,
                'params': request.args,
                'data': request.get_json(silent=True),
                'headers': dict(request.headers.items(lower=True))
            }

        @route('/httpException', methods=['GET'])
        def raise_http_exception(self):
            raise NotFound()

        @route('/serviceException', methods=['GET'])
        def raise_server_exception(self):
            raise ServiceError()

        @route('/serviceUnavailable', methods=['GET'])
        def raise_service_unavailable(self):
            raise ServiceUnavailable()

    SimpleView.register(app, '/simple', endpoint='simple')


@pytest.fixture
def server(app, view):
    srv = make_server(host='localhost', port=12345, app=app, threaded=True)
    t = threading.Thread(target=srv.serve_forever)
    t.start()
    yield f'http://{srv.host}:{srv.port}'
    srv.shutdown()
    t.join()
