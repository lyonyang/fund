#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import logging


class BaseConfig:
    """Project base settings"""
    PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
    INSTALL_HANDLERS = list()
    INSTALL_HANDLERS_NAME = dict()

    ################
    # Tornado Docs #
    ################
    DOCS_USERNAME = 'admin'
    DOCS_PASSWORD = 'admin'
    DOCS_GLOBAL_PARAMS = []
    DOCS_GLOBAL_HEADERS = []
    DOCS_TOKEN_VERIFY_EXPIRE = True
    DOCS_TOKEN_EXPIRE_DAYS = 7
    DOCS_TOKEN_SECRET_KEY = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'

    # APP
    STATIC_PATH = 'static'
    LOG_PATH = 'logs'
    LOG_HANDLER = [
        logging.INFO,
        logging.WARNING,
        logging.ERROR
    ]

    DEBUG = True

    REQUEST_ALLOW_ORIGIN = ['*']
    REQUEST_ALLOW_HEADERS = ['*']

    def to_dict(self):
        """lower settings"""
        settings = {}
        for key in dir(self):
            if not key.startswith('__'):
                settings[key.lower()] = getattr(self, key)
        return settings

    def from_dict(self, d, **kwargs):
        assert issubclass(type(d), dict)
        d.update(kwargs)
        for key, value in d.items():
            self[key] = value

    def __getitem__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        raise AttributeError(item)

    def __setitem__(self, key, value):
        setattr(self, key, value)
