#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


"""
Fist step: celery beat -A celerys.server --loglevel=info

Second step: celery worker -A celerys.server --loglevel=info

Flower : flower -A tasks --port=9000

Celery config : https://docs.celeryproject.org/en/latest/userguide/configuration.html
"""

import os
import sys
import importlib
from celery import Celery
from base import load_config
from mongoengine import connect

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, os.pardir))

config = load_config('dev')

app = Celery('fund', set_as_current=False)

beat_schedule = dict()
for cron in config.CELERY_CONFIG['include']:
    module = importlib.import_module(cron)
    if hasattr(module, 'beat_schedule'):
        beat_schedule.update(getattr(module, 'beat_schedule'))

app.config_from_object(config.CELERY_CONFIG)
app.conf.project_conf = config
app.conf.beat_schedule = beat_schedule

connect(config.MONGO_CONFIG["db"], host=config.MONGO_CONFIG['host'],
        port=config.MONGO_CONFIG["port"], username=config.MONGO_CONFIG["username"],
        password=config.MONGO_CONFIG["password"], connect=False)

if __name__ == '__main__':
    app.worker_main(argv=['-A', 'server', '--loglevel=info', '-P', 'eventlet'])
