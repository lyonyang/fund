#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from lib.dt import dt
from celerys.server import app
from celery.schedules import crontab
from utils.fundutil import FundData
from apps.fund.info import FundHistoryNetWorth

beat_schedule = {
    # 每个工作日的早上8点跑
    'update_optional_data': {
        'task': 'celerys.crontabs.fund.update_optional_data',
        'schedule': crontab(0, 8, day_of_week='mon-fri'),
        'args': ()
    }
}


@app.task
def update_optional_data():
    """每天8点更新自选基金历史净值"""

    yesterday = dt.yesterday()

    records = FundHistoryNetWorth.objects.aggregate(
        {'$match': {'is_delete': 0}},
        {"$group": {"_id": "$code", 'date': {'$max': '$date'}}}
    )

    for rec in records:
        code = rec['_id']
        last_day = rec['date']
        days = (yesterday - last_day).days
        if days <= 0:
            continue
        net_worth_list = FundData.sync_get_section_net_worth(code,
                                                             last_day.strftime("%Y-%m-%d"),
                                                             yesterday.strftime("%Y-%m-%d"),
                                                             raw=True)
        fund_name = FundData.sync_get_fund_name(code)
        for entry in net_worth_list:
            FundHistoryNetWorth.create(code, fund_name, float(entry[1]) * 1000, entry[0], float(entry[3][:-1]))
