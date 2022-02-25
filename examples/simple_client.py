from config import Config
from lesoon_common import LesoonFlask
from lesoon_restful import Api
from lesoon_restful import Resource
from lesoon_restful import Route
from lesoon_restful import use_kwargs
from lesoon_restful import web_fields as wf

from lesoon_client.wrappers import LesoonClient

app = LesoonFlask(config=Config)
api = Api(app)


class SimpleClient(LesoonClient):
    BASE_URL = 'http://localhost:12345'
    URL_PREFIX = '/simple'

    def get_test(self, text: str):
        return self.GET('/test', params={'text': text}, load_response=False)


class SimpleResource(Resource):

    class Meta:
        name = 'simple'

    simple_client = SimpleClient()

    @Route.GET('/test')
    @use_kwargs({'text': wf.Str()}, location='query')
    def test(self, text: str):
        return f'echo :{text}'

    @Route.GET('/testClient')
    @use_kwargs({'text': wf.Str()}, location='query')
    def test_client(self, text: str):
        res = self.simple_client.get_test(text)
        return res


api.add_resource(SimpleResource)

if __name__ == '__main__':
    print(app.url_map)
    app.run(port=12345, debug=True)
    # res = requests.get("http://localhost:12345/simple/testClient?text=client_test")
