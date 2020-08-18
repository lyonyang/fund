#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import logging
import os
from base import BaseConfig


class GlobalConfig(BaseConfig):
    """
    Global Config
    """
    project_root = os.path.realpath(os.path.dirname(__file__))

    debug = True

    no_keep_alive = True

    ################
    # Tornado Docs #
    ################
    install_handlers = [
        'api.users.user',
        'api.fund.fund',
        'api.fund.trade',
        'api.fund.simulate',
    ]
    install_handlers_name = {
        'api.users.user': '用户API',
        'api.fund.fund': '基金API',
        'api.fund.trade': '交易API'
    }
    docs_username = 'admin'
    docs_password = 'admin'
    docs_global_params = []
    docs_global_headers = [
        ('Authorization', False, str, '')
    ]
    docs_token_verify_expire = True
    docs_token_expire_days = 30
    docs_token_secret_key = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'

    # APP
    static_path = 'static'
    log_path = 'logs'
    log_handler = [
        logging.INFO,
        logging.WARNING,
        logging.ERROR
    ]

    cors_allow_origin = ['*']
    cors_allow_headers = ['*']
    cors_allow_method = ['POST', 'GET', 'OPTIONS']

    backend_md5_salt = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'
    backend_token_secret_key = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'


class DevelopConfig(GlobalConfig):
    debug = True

    # MySQL
    mysql_config = {
        'max_connections': 100,
        'stale_timeout': 300,
        'host': '121.37.242.252',
        'db': 'fund',
        'username': 'root',
        'password': 'mysql123456',
        'port': 3306
    }

    # Mongodb
    mongo_config = {
        'max_connections': 100,
        'min_connections': 1,
        'host': '121.37.242.252',
        'port': 27017,
        'db': 'fund',
        'username': 'root',
        'password': 'mongodb123456',
    }

    # Redis
    redis_config = {
        'max_connections': 100,
        'min_connections': 1,
        'host': '121.37.242.252',
        'db': 0,
        'password': 'redis123456',
        'port': 6379
    }

    # MQ
    mq_config = {
        'host': '121.37.242.252',
        'port': 15762,
        'username': 'guest',
        'password': 'guest'
    }


class ProductConfig(GlobalConfig):
    debug = False


config_env = {
    'dev': DevelopConfig,
    'pro': ProductConfig
}
