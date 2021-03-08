#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from base.auth import login_required
from api.status import Code, Message
from utils.fundutil import FundData
from apps.users.trade import TradeRecord
from docs import RequestHandler, define_api, Param


class FundSurvey(RequestHandler):
    @define_api('/fund/survey', [
    ], desc='基金概况')
    @login_required
    async def get(self):
        principal, income, today_income = 0, 0, 0
        records = await TradeRecord.objects.execute(
            TradeRecord.select().where(TradeRecord.user_id == self.user_id,
                                       TradeRecord.is_delete == TradeRecord.DELETE_NO
                                       ).order_by(TradeRecord.date))
        map = dict()
        for record in records:
            if record.code in map:
                if record.type == TradeRecord.TYPE_SELL_OUT:
                    map[record.code]['principal'] -= map[record.code]['principal'] / map[record.code][
                        'copies'] * record.copies
                    map[record.code]['copies'] -= record.copies
                else:
                    map[record.code]['principal'] += record.amount / 1000
                    map[record.code]['copies'] += record.copies
            else:
                tmp = await record.normal_info()
                tmp['fund_name'] = await FundData.get_fund_name(record.code)
                tmp['principal'] = record.amount / 1000
                tmp['code'] = record.code
                tmp['copies'] = record.copies
                map[record.code] = tmp

        for code in map:
            hold_net_worth = map[code]['principal'] / map[code]['copies']
            cur_net_worth = await FundData.get_current_net_worth(code)
            pre_net_worth = await FundData.get_last_day_net_worth(code)
            principal += map[code]['principal']
            today_income += map[code]['copies'] * (cur_net_worth - pre_net_worth)
            income += map[code]['copies'] * (cur_net_worth - hold_net_worth)

        return self.write_success(
            {'principal': round(principal, 2), 'income': round(income, 2), 'today_income': round(today_income, 2)})


class MyFundList(RequestHandler):
    RISE_COLOR = '#e25050'  # 上涨颜色
    FALL_COLOR = '#79e250'  # 下跌颜色

    @define_api('/fund/list', [
    ], desc='我的基金')
    @login_required
    async def get(self):
        records = await TradeRecord.objects.execute(TradeRecord.select().where(TradeRecord.user_id == self.user_id,
                                                                               TradeRecord.is_delete == TradeRecord.DELETE_NO).order_by(
            TradeRecord.date))
        map = dict()
        for record in records:
            if record.code in map:
                if record.type == TradeRecord.TYPE_SELL_OUT:
                    map[record.code]['principal'] -= map[record.code]['principal'] / map[record.code][
                        'copies'] * record.copies
                    map[record.code]['copies'] -= record.copies
                else:
                    map[record.code]['principal'] += record.amount / 1000
                    map[record.code]['copies'] += record.copies
            else:
                tmp = await record.normal_info()
                tmp['fund_name'] = await FundData.get_fund_name(record.code)
                tmp['principal'] = record.amount / 1000
                tmp['code'] = record.code
                tmp['copies'] = record.copies
                map[record.code] = tmp
        for code in map:
            hold_net_worth = round(map[code]['principal'] / map[code]['copies'], 4)
            cur_net_worth = await FundData.get_current_net_worth(code)
            pre_net_worth = await FundData.get_last_day_net_worth(code)
            earning_rate = (cur_net_worth - hold_net_worth) / hold_net_worth
            today_earning_rate = (cur_net_worth - pre_net_worth) / pre_net_worth
            map[code]['copies'] = round(map[code]['copies'], 2)
            map[code]['hold_net_worth'] = '%.4f' % hold_net_worth
            map[code]['cur_net_worth'] = '%.4f' % cur_net_worth
            map[code]['pre_net_worth'] = '%.4f' % pre_net_worth
            map[code]['principal'] = round(map[code]['principal'], 2)
            map[code]['earning_rate'] = round(earning_rate * 100, 2)
            map[code]['today_earning_rate'] = round(today_earning_rate * 100, 2)
            map[code]['today_income'] = round(map[code]['copies'] * (cur_net_worth - pre_net_worth), 2)
            map[code]['income'] = round(map[code]['copies'] * (cur_net_worth - hold_net_worth), 2)
            map[code]['color'] = self.RISE_COLOR if earning_rate > 0 else self.FALL_COLOR
            map[code]['today_color'] = self.RISE_COLOR if today_earning_rate > 0 else self.FALL_COLOR
        data = sorted(map.values(), key=lambda x: x['principal'], reverse=True)
        return self.write_success(data)


class FundGet(RequestHandler):
    @define_api('/fund/get', [
        Param('code', True, int, '', '基金代码'),
    ], desc='获取当前基金净值')
    async def get(self):
        net_worth = await FundData.get_current_net_worth(self.get_arg('code'))
        if net_worth is None:
            return self.write_fail(Code.Fund.NET_WORTH_NOT_EXIST, Message.Fund.NET_WORTH_NOT_EXIST)
        return self.write_success({'net_worth': net_worth})


class FundDelete(RequestHandler):
    @define_api('/fund/delete', [
        Param('code', True, str, '', '基金代码'),
    ], desc='删除基金')
    @login_required
    async def post(self):
        code = self.get_arg('code')
        await TradeRecord.objects.execute(TradeRecord.update(
            {TradeRecord.is_delete: TradeRecord.DELETE_IS}
        ).where(TradeRecord.code == code,
                TradeRecord.user_id == self.user_id,
                TradeRecord.is_delete == TradeRecord.DELETE_NO))
        return self.write_success()
