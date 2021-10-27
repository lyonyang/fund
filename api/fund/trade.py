#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon



from api.status import Code, Message
from base.auth import login_required
from docs import RequestHandler, define_api, Param
from apps.users.trade import TradeRecord
from utils.fundutil import FundData


class TradeRecordAdd(RequestHandler):
    @define_api('/fund/trade/record/add', [
        Param('name', False, str, '', '基金名称'),
        Param('code', True, str, '', '基金代码'),
        Param('amount', True, int, '', '金额, x1000'),
        Param('date', True, str, '', '日期'),
        Param('type', True, int, '', '类型, 1: 买入, 2: 卖出'),
    ], desc='添加交易记录')
    @login_required
    async def post(self):
        code = self.get_arg('code')
        amount = self.get_arg_int('amount')
        date = self.get_arg('date')
        type = self.get_arg_int('type')
        net_worth = await FundData.get_date_net_worth(code, date)
        fund_name = await FundData.get_fund_name(code)
        if net_worth is None:
            return self.write_fail(Code.Fund.NET_WORTH_NOT_EXIST, Message.Fund.NET_WORTH_NOT_EXIST)
        copies = amount / net_worth / 1000
        await TradeRecord.async_create(self.user_id, code, fund_name, amount, net_worth * 10000, copies, date, type)
        return self.write_success()


class TradeRecordDelete(RequestHandler):
    @define_api('/fund/trade/record/delete', [
        Param('record_id', True, int, '', '记录id'),
    ], desc='删除交易记录')
    @login_required
    async def post(self):
        record_id = self.get_arg_int('record_id')
        record = await TradeRecord.async_get(id=record_id, user_id=self.user_id, is_delete=TradeRecord.DELETE_NO)
        if not record:
            return self.write_bad_request()
        await record.async_delete()
        return self.write_success()


class TradeRecordList(RequestHandler):
    @define_api('/fund/trade/record/list', [
    ], desc='交易记录列表')
    @login_required
    async def get(self):
        records = await TradeRecord.async_select(user_id=self.user_id, is_delete=TradeRecord.DELETE_NO,
                                                 order_by=TradeRecord.date.desc())
        data = []
        for record in records:
            data.append(await record.normal_info())
        return self.write_success(data=data)
