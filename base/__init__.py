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
    from .. import config as project_conf
except:
    import importlib

    project_conf = importlib.import_module('fund.config')

from base.log import TornadoLogger

# TODO: Thread-local
app = None
config = None


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
    global app, config

    if isinstance(env, str):
        config_cls = project_conf.config_env.get(env)
        config = config_cls()
        assert issubclass(config_cls, BaseConfig), \
            "%s not have to_dict method." % config_cls.__name__
    elif isinstance(env, dict):
        config_cls = BaseConfig
        config = config_cls().from_dict(**env)
    else:
        raise TypeError

    options = config.to_dict()
    # 关闭Tornado原日志
    options['logging'] = 'none'

    from docs import route, RequestHandler, after_request

    # 请求日志
    after_request(RequestHandler.log_request)

    application = tornado.web.Application(route.handlers, **options)
    application.env = env if isinstance(env, str) else env.__name__
    application.loop = tornado.ioloop.IOLoop.current()
    application.config = config
    application.run = types.MethodType(run, application)
    application.run_sync = application.loop.run_sync
    application.__class__.logger = TornadoLogger(config).logger

    app = application

    return application
