#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from celerys.server import app
from celery.schedules import crontab

beat_schedule = {
    'send_email': {
        'task': 'celerys.crontabs.notify.send_email',
        'schedule': crontab(minute='*/1'),
        'args': ()
    }
}


@app.task
def send_email():
    print('发送邮件~')
    return 'Success'
