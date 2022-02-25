import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    PROPAGATE_EXCEPTIONS = True
    # sqlalchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # client
    CLIENT = {'BASE_URL': '', 'PROVIDER_URLS': {}}
