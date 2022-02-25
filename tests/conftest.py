"""Defines fixtures available to all tests."""
import logging
import threading

import pytest
from lesoon_common import LesoonFlask
from lesoon_restful import Api
from tests.resources import SimpleResource
from werkzeug.serving import make_server


class Config:
    TESTING = True


@pytest.fixture
def app():
    """Create application for the tests."""
    app = LesoonFlask(__name__, config=Config)
    app.testing = True
    app.logger.setLevel(logging.CRITICAL)
    ctx = app.test_request_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture
def server(app):
    api = Api(app)
    SimpleResource.api = None
    api.add_resource(SimpleResource)
    srv = make_server(host='localhost', port=12345, app=app, threaded=True)
    t = threading.Thread(target=srv.serve_forever)
    t.start()
    yield f'http://{srv.host}:{srv.port}'
    srv.shutdown()
    t.join()
