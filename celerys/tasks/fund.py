#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Celery 5.0 才会支持 async等异步方法
暂时使用同步函数, 后期寻更佳方案
"""

from celerys.server import app
from utils.fundutil import FundData
from apps.fund.info import FundHistoryNetWorth


@app.task
def grab_last_month_data(code):
    """抓取该基金半年的数据"""
    exist = FundHistoryNetWorth.objects.filter(code=code, is_delete=FundHistoryNetWorth.DELETE_NO).first()
    if exist:
        return

    fund_name = FundData.sync_get_fund_name(code)
    records = FundData.sync_get_trade_net_worth(code, 180)
    for rec in records:
        FundHistoryNetWorth.create(code, fund_name, float(rec[1]) * 1000, rec[0], float(rec[3][:-1]))
