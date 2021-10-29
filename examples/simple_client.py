from config import DevelopmentConfig
from flask import blueprints
from lesoon_common import LesoonApi
from lesoon_common import LesoonFlask
from lesoon_common import LesoonView
from lesoon_common import request_param
from lesoon_common import route

from lesoon_client.wrappers import LesoonClient

app = LesoonFlask(config=DevelopmentConfig)

bp = blueprints.Blueprint('lesoon_client', __name__)

api = LesoonApi(bp)


class SimpleClient(LesoonClient):
    BASE_HOST = 'http://127.0.0.1'
    URL_PREFIX = '/simple'

    def get_test(self, text: str):
        return self.get('/test', params={'text': text})


class SimpleView(LesoonView):
    simple_client = SimpleClient()

    @route('/test', methods=['GET'])
    @request_param()
    def test(self, text: str):
        return f'echo :{text}'

    @route('/testClient', methods=['GET'], skip_decorator=True)
    @request_param()
    def test_client(self, text: str):
        res = self.simple_client.get_test(text)
        return res


api.register_view(SimpleView, '/simple', endpoint='simple')

if __name__ == '__main__':
    app.register_blueprint(bp)
    print(app.url_map)
    app.run(port=12345, debug=True)
    # res = requests.get("http://localhost:12345/simple/testClient?text=client_test")
