#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Celery 5.0 才会支持 async等异步方法
暂时使用同步函数, 后期寻更佳方案
"""

from celerys.server import app
from apps.fund.info import FundHistoryNetWorth


@app.task
def grab_fund_history_data(code):
    FundHistoryNetWorth.create(code, '基金名称', 1.01, '2020-01-01')
