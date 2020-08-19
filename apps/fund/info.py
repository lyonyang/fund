#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from db.mysql import MySQLModel
from peewee import CharField


class FundInfo(MySQLModel):
    """基金信息"""

    class Meta:
        table_name = 'fund_info'

    code = CharField(max_length=6, verbose_name='基金代码', index=True)
    name = CharField(max_length=256, verbose_name='基金名称')
