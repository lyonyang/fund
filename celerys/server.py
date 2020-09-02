#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


"""
Fist step: celery beat -A celerys.server --loglevel=info

Second setp: celery worker -A celerys.server --loglevel=info

Celery config : https://docs.celeryproject.org/en/latest/userguide/configuration.html
"""

import os
import sys
import importlib
from celery import Celery
from base import load_config

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, os.pardir))

config = load_config('test')

app = Celery('fund',
             broker=config.CELERY_CONFIG['broker_url'],
             backend=config.CELERY_CONFIG['result_backend'],
             include=config.CELERY_CONFIG['include'],
             set_as_current=False)

beat_schedule = dict()
for cron in config.CELERY_CONFIG['include']:
    module = importlib.import_module(cron)
    if hasattr(module, 'beat_schedule'):
        beat_schedule.update(getattr(module, 'beat_schedule'))

app.config_from_object(config)
app.conf.beat_schedule = beat_schedule

if __name__ == '__main__':
    app.worker_main(argv=['-A', 'server', '--loglevel=info', '-P', 'eventlet'])
