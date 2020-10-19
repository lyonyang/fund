#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from lib.dt import dt
from utils.fundutil import FundData
from base.db.redis import async_redis


class FundRedis:
    YESTERDAY_NET_WORTH_KEY = 'fund-{code}-{date}'

    @classmethod
    async def get_last_day_net_worth(cls, code):
        """最后一个交易日"""
        key = cls.YESTERDAY_NET_WORTH_KEY.format(code=str(code), date=dt.yesterday_str())
        value = await async_redis.decode(await async_redis.get(key))
        if not value:
            data = await FundData.get_last_day_net_worth(code, raw=True)
            value = '%s,%s' % (data[1], data[3])
            await async_redis.set(key, value, ex=60 * 60 * 24)
        return value
