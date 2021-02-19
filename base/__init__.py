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

from base.conf import BaseConfig

try:
    from .. import config as project_conf
except:
    import importlib

    project_conf = importlib.import_module('fund.config')

from base.log import TornadoLogger

app = None
config = None


def load_config(env):
    """Only load config, not app."""
    global config
    if config is not None:
        return config
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
    return config


def run(app, port=8000, host='0.0.0.0'):
    app.logger.info(' * Serving Tornado app "%s"' % __name__)
    app.logger.info(' * Environment: %s' % app.env)
    app.logger.info(' * Debug mode: %s' % ('on' if app.settings.get('debug') else 'off'))
    app.logger.info(' * Running on http://%s:%d/ (Press CTRL+C to quit)' % (host, port))
    if app.settings.get('debug'):
        app.logger.info(' * Tornado Docs running on http://%s:%d/tornado_docs' % (host, port))
    app.listen(port, host)
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
    # Close tornado log
    options['logging'] = 'none'

    from docs import route

    application = tornado.web.Application(route.handlers, **options)
    application.env = env if isinstance(env, str) else env.__name__
    application.loop = tornado.ioloop.IOLoop.current()
    application.config = config
    application.run = types.MethodType(run, application)
    application.run_sync = application.loop.run_sync
    application.logger = TornadoLogger(config).logger

    app = application

    return application
