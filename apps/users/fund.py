#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


from base.db.mysql import MySQLModel
from peewee import IntegerField, CharField


class FundOptionalRecord(MySQLModel):
    """基金自选记录"""

    class Meta:
        table_name = 'fund_optional_record'

    user_id = IntegerField(verbose_name='用户id', index=True)
    code = CharField(max_length=6, verbose_name='基金代码', index=True)
    fund_name = CharField(max_length=128, null=True, verbose_name='基金名称')

    @classmethod
    async def async_create(cls, user_id, code, fund_name, **kwargs):
        _obj = await super(FundOptionalRecord, cls).async_create(user_id=user_id, code=code, fund_name=fund_name)
        return _obj

    async def normal_info(self):
        data = await super(FundOptionalRecord, self).normal_info()
        data.update({
            'code': self.code,
            'fund_name': self.fund_name
        })
        return data
