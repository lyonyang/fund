#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


import os
import time
import logging


class TornadoLogger(object):
    def __init__(self, config):
        self.logger = logging.RootLogger(logging.DEBUG)
        self.logger.propagate = False
        self.format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
        self.config = config
        for level in self.config.LOG_HANDLER:
            level_name = logging._levelToName.get(level)
            self.add_handler(self.logger, level, level_name)
            self.add_console(self.logger, level)

        if self.config.DEBUG:
            self.add_console(self.logger, logging.DEBUG)

    def add_handler(self, logger, level, level_name):
        file_name = time.strftime('%Y-%m-%d', time.localtime(time.time()))

        dir = self.config.PROJECT_ROOT + os.sep + \
              self.config.LOG_PATH + os.sep + \
              level_name.lower()

        path = dir + os.sep + file_name + '.log'
        self.makedir(dir)
        handler = logging.FileHandler(path, encoding='UTF-8')
        filter = logging.Filter()
        filter.filter = lambda r: r.levelno == level

        handler.addFilter(filter)
        handler.setLevel(level)
        handler.setFormatter(self.format)

        logger.addHandler(handler)

    def add_console(self, logger, level):
        console = logging.StreamHandler()
        filter = logging.Filter()
        filter.filter = lambda r: r.levelno == level

        console.setLevel(level)
        console.addFilter(filter)
        logger.addHandler(console)

    def makedir(self, path):
        path = path.strip()
        if not os.path.exists(path):
            os.makedirs(path)
        return path
