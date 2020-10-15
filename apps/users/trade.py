#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from base.db.mysql import MySQLModel
from utils.fundutil import FundData
from peewee import (
    IntegerField, CharField, DateField, DoubleField
)


class TradeRecord(MySQLModel):
    """交易记录"""

    class Meta:
        table_name = 'trade_record'

    TYPE_CHOICES = (
        (1, '买入'),
        (2, '卖出'),
    )

    TYPE_BUY = 1
    TYPE_SELL_OUT = 2

    user_id = IntegerField(verbose_name='用户id', index=True)
    code = CharField(max_length=6, verbose_name='基金代码', index=True)
    fund_name = CharField(max_length=128, null=True, verbose_name='基金名称')
    amount = IntegerField(verbose_name='购买金额, x1000')
    net_worth = IntegerField(verbose_name='净值, x1000')
    copies = DoubleField(default=0, verbose_name='份额')
    date = DateField(verbose_name='日期')
    type = IntegerField(verbose_name='类别')

    @classmethod
    async def async_create(cls, user_id, code, fund_name, amount, net_worth, copies, date, type):
        _obj = await super(TradeRecord, cls).async_create(user_id=user_id,
                                                          code=code,
                                                          fund_name=fund_name,
                                                          amount=amount,
                                                          net_worth=net_worth,
                                                          copies=copies,
                                                          date=date,
                                                          type=type)
        return _obj

    async def normal_info(self):
        data = super(TradeRecord, self).normal_info()
        data.update({
            'code': self.code,
            'amount': self.amount,
            'net_worth': '%.04f' % (self.net_worth / 10000),
            'date': self.date_to_str(self.date),
            'type': self.type,
            'fund_name': self.fund_name or await self.update_fund_name(),
            'copies': round(self.copies, 2),
        })
        return data

    async def update_fund_name(self):
        fund_name = await FundData.get_fund_name(self.code)
        await self.async_update(fund_name=fund_name)
        return fund_name
