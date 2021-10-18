import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # flask
    SECRET_KEY = os.environ.get("SECRET_KEY")
    PROPAGATE_EXCEPTIONS = True
    # sqlalchemy
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # cache
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # debug-tool
    # 性能分析开关
    DEBUG_TB_PROFILER_ENABLED = True

    # sqlalchemy
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL")

    # jwt
    JWT_SECRET_KEY = os.environ.get("DEV_JWT_SECRET_KEY")


config = {"development": DevelopmentConfig, "default": DevelopmentConfig}
