#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import logging


class BaseConfig:
    """Project base settings"""
    project_root = os.path.realpath(os.path.dirname(__file__))
    install_handlers = []
    install_handlers_name = {}

    ################
    # Tornado Docs #
    ################
    docs_username = 'admin'
    docs_password = 'admin'
    docs_global_params = []
    docs_global_headers = []
    docs_token_verify_expire = True
    docs_token_expire_days = 7
    docs_token_secret_key = '8i-!yfmt+hk@-$e7%wl2hx#!v7+rjdc%s8udl0a_*um0l)++y%'

    # APP
    static_path = 'static'
    log_path = 'logs'
    log_handler = [
        logging.INFO,
        logging.WARNING,
        logging.ERROR
    ]

    debug = True

    request_allow_origin = ['*']
    request_allow_headers = ['*']

    def to_dict(self):
        settings = {}
        for key in dir(self):
            if not key.startswith('__'):
                settings[key] = getattr(self, key)
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
