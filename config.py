#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import logging
from base.conf import BaseConfig


class Config(BaseConfig):
    """Public config"""
    PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))

    DEBUG = True

    NO_KEEP_ALIVE = True

    ################
    # Tornado Docs #
    ################
    INSTALL_HANDLERS = [
        'api.users.user',
        'api.fund.fund',
        'api.fund.optional',
        'api.fund.trade',
        'api.fund.simulate',
    ]

    INSTALL_HANDLERS_NAME = {
        'api.users.user': '用户API',
        'api.fund.fund': '基金API',
        'api.fund.optional': '自选API',
        'api.fund.trade': '交易API',
        'api.fund.simulate': '基金模拟API'
    }
    DOCS_USERNAME = 'admin'
    DOCS_PASSWORD = 'admin'
    DOCS_GLOBAL_PARAMS = []
    DOCS_GLOBAL_HEADERS = [
        ('Authorization', False, str, '')
    ]
    DOCS_TOKEN_VERIFY_EXPIRE = True
    DOCS_TOKEN_EXPIRE_DAYS = 30
    DOCS_TOKEN_SECRET_KEY = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'

    # APP
    STATIC_PATH = 'static'
    LOG_PATH = 'logs'
    LOG_HANDLER = [
        logging.INFO,
        logging.WARNING,
        logging.ERROR
    ]
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s'
    LOG_REQUEST_DETAIL = True
    ON_FINISH_ASYNC = True

    CORS_ALLOW_ORIGIN = ['*']
    CORS_ALLOW_HEADERS = ['*']
    CORS_ALLOW_METHOD = ['POST', 'GET', 'OPTIONS']

    BACKEND_MD5_SALT = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'
    BACKEND_TOKEN_SECRET_KEY = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'


class DevelopConfig(Config):
    DEBUG = True

    # MySQL
    MYSQL_CONFIG = {
        'max_connections': 100,
        'stale_timeout': 300,
        'host': '127.0.0.1',
        'db': 'fund',
        'username': 'root',
        'password': 'mysql',
        'port': 3306
    }

    # Mongodb
    MONGO_CONFIG = {
        'max_connections': 100,
        'min_connections': 1,
        'host': '127.0.0.1',
        'port': 27017,
        'db': 'fund',
        'username': 'root',
        'password': 'mongodb',
    }

    # Redis
    REDIS_CONFIG = {
        'max_connections': 100,
        'min_connections': 1,
        'host': '127.0.0.1',
        'db': 0,
        'password': 'redis',
        'port': 6379
    }

    # MQ
    MQ_CONFIG = {
        'host': '127.0.0.1',
        'port': 15762,
        'username': 'guest',
        'password': 'guest'
    }

    # Celery
    CELERY_CONFIG = {
        'timezone': "Asia/Shanghai",
        'enable_utc': False,
        'broker_url': 'redis://username:password@127.0.0.1:6379/0',  # redis://:password@host:port/db
        'result_backend': 'redis://username:password@127.0.0.1:6379/0',  # amqp://user:password@host:port/myvhost
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'include': [
            'celerys.crontabs.fund',
            'celerys.tasks.fund',
        ]
    }


class ProductConfig(Config):
    DEBUG = False


config_env = {
    'dev': DevelopConfig,
    'pro': ProductConfig,
}
