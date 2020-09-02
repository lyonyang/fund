#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from celerys.server import app


@app.task
def send_email():
    print('发送邮件~')
    return 'Success'
