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

    class SimpleView(BaseView):
        @route("/", methods=["GET", "POST", "PUT", "DELETE"])
        def simple(self):
            return {
                "method": request.method,
                "params": request.args,
                "data": request.get_json(silent=True),
            }

    SimpleView.register(app, "/simple", endpoint="simple")


@pytest.fixture
def server(app, view):
    srv = make_server(host="localhost", port=5000, app=app, threaded=True)
    t = threading.Thread(target=srv.serve_forever)
    t.start()
    yield f"http://{srv.host}:{srv.port}"
    srv.shutdown()
    t.join()
