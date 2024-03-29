#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import os
import sys

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, os.pardir))

from base import make_app


async def do_something():
    pass


if __name__ == '__main__':
    app = make_app('dev')
    app.run_sync(do_something)
