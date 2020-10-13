#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

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

    @classmethod
    def create(cls, code, fund_name, net_worth, date, **kwargs):
        """同步创建"""
        cls.connect()
        obj = cls(code=code, fund_name=fund_name, net_worth=net_worth, date=date, **kwargs)
        return obj.save()
