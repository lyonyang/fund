#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from peewee import CharField

from base.db.mysql import MySQLModel


class FundInfo(MySQLModel):
    """基金信息"""

    class Meta:
        table_name = 'fund_info'

    code = CharField(max_length=6, verbose_name='基金代码', index=True)
    name = CharField(max_length=256, verbose_name='基金名称')
