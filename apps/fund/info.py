#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
这里面 MySQL 和 MongoDB 夹杂在一起, 这个分类看个人, 现在因为表比较少, 没有分类太细
夹杂在一起要注意用法的差异
"""

from peewee import CharField
from mongoengine import fields
from base.db.mysql import MySQLModel
from base.db.mongo import MongoModel


class FundInfo(MySQLModel):
    """基金信息"""

    class Meta:
        table_name = 'fund_info'

    code = CharField(max_length=6, verbose_name='基金代码', index=True)
    name = CharField(max_length=256, verbose_name='基金名称')


class FundHistoryNetWorth(MongoModel):
    """基金历史净值"""

    meta = {
        'collection': 'fund_history_net_worth',
        'indexes': ['code']
    }

    code = fields.StringField(max_length=6, verbose_name='基金代码')
    fund_name = fields.StringField(verbose_name='基金代码')
    net_worth = fields.IntField(verbose_name='净值, x1000')
    date = fields.DateField(verbose_name='日期')
    daily_growth_rate = fields.FloatField(verbose_name='日增长率')

    @classmethod
    def create(cls, code, fund_name, net_worth, date, daily_growth_rate, **kwargs):
        """注意使用同步需要保证有connection"""
        obj = cls(code=code, fund_name=fund_name, net_worth=net_worth, date=date, daily_growth_rate=daily_growth_rate,
                  **kwargs)
        return obj.save()
