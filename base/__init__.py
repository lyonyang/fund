#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import sys
import types
import tornado.ioloop
import tornado.options
import tornado.web

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, os.pardir, os.pardir))
from base.config import BaseConfig

try:
    from .. import config
except:
    import importlib

    config = importlib.import_module('fund.config')

current_app = None
current_config = BaseConfig()

from base.log import TornadoLogger


def run(app, port=8000):
    app.logger.info(' * Serving Tornado app "%s"' % __name__)
    app.logger.info(' * Environment: %s' % app.env)
    app.logger.info(' * Debug mode: %s' % ('on' if app.settings.get('debug') else 'off'))
    app.logger.info(' * Running on http://0.0.0.0:%d/ (Press CTRL+C to quit)' % port)
    if app.settings.get('debug'):
        app.logger.info(' * Tornado Docs running on http://0.0.0.0:%d/tornado_docs' % port)
    app.listen(port, '0.0.0.0')
    app.loop.start()


def make_app(env):
    global current_config, current_app

    if isinstance(env, str):
        config_cls = config.config_env.get(env)
        current_config = config_cls()
        assert issubclass(config_cls, BaseConfig), \
            "%s not have to_dict method." % config_cls.__name__
    elif isinstance(env, dict):
        config_cls = BaseConfig
        current_config = config_cls().from_dict(**env)
    else:
        raise TypeError

    options = current_config.to_dict()
    # 关闭Tornado原日志
    options['logging'] = 'none'

    from docs import route, RequestHandler, after_request

    # 请求日志
    after_request(RequestHandler.log_request)

    app = tornado.web.Application(route.handlers, **options)
    current_app = app
    app.env = env if isinstance(env, str) else env.__name__
    app.loop = tornado.ioloop.IOLoop.current()
    app.run = types.MethodType(run, app)

    app.__class__.logger = TornadoLogger(current_config).logger
    return app


def get_io_loop():
    if current_app:
        return current_app.loop
    return tornado.ioloop.IOLoop.current().run_sync()
