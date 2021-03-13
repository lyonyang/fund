#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import sys
import types
import tornado.gen
import tornado.web
import tornado.ioloop
import tornado.options
import concurrent.futures
from base.log import TornadoLogger

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, os.pardir, os.pardir))

try:
    import config as project_conf
except:
    import importlib

    project_conf = importlib.import_module('fund.config')

app = None
config = None


class Application(tornado.web.Application):
    def __init__(self, handlers, config, default_host=None, transforms=None, **settings):
        super(Application, self).__init__(handlers, default_host=default_host, transforms=transforms, **settings)

        self.config = config

        self.loop = tornado.ioloop.IOLoop.current()

        logger = TornadoLogger(self.config.PROJECT_ROOT, self.config.LOG_PATH, self.config.LOG_HANDLER,
                               self.config.LOG_FORMAT, self.config.DEBUG).logger
        self.logger = logger

        def _run_callback(self, callback) -> None:
            try:
                ret = callback()
                if ret is not None:
                    try:
                        ret = tornado.gen.convert_yielded(ret)
                    except tornado.gen.BadYieldError:
                        pass
                    else:
                        self.add_future(ret, self._discard_future_result)
            except concurrent.futures.CancelledError:
                pass
            except Exception:
                logger.error("Exception in callback %r", callback, exc_info=True)

        self.loop._run_callback = types.MethodType(_run_callback, self.loop)

    def run(self, port=8000, host='0.0.0.0'):
        self.logger.info(' * Serving Tornado app "%s"' % __name__)
        self.logger.info(' * Environment: %s' % self.config.ENV)
        self.logger.info(' * Debug mode: %s' % ('on' if self.config.DEBUG else 'off'))
        self.logger.info(' * Running on http://%s:%d/ (Press CTRL+C to quit)' % (host, port))
        if self.settings.get('debug'):
            self.logger.info(' * Tornado Docs running on http://%s:%d/tornado_docs' % (host, port))
        self.listen(port, host)
        self.loop.start()

    def run_sync(self, func, time_out=None):
        return self.loop.run_sync(func, time_out)


def load_config(env):
    """Only load config, not app."""
    from base.conf import BaseConfig
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

    config.ENV = env if isinstance(env, str) else env.__name__

    return config


def make_app(env):
    global app

    config = load_config(env)

    from docs import route, RequestHandler, PageNotFound
    options = config.to_dict()
    options['logging'] = 'none'
    options['default_handler_class'] = PageNotFound
    options['log_function'] = RequestHandler.log_request
    app = Application(route.handlers, config, **options)

    return app
