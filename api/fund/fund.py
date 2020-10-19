#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from lib.dt import dt
from cache.fund import FundRedis
from base.auth import login_required
from api.status import Code, Message
from utils.fundutil import FundData
from apps.users.trade import TradeRecord
from apps.users.fund import FundOptionalRecord
from apps.fund.info import FundHistoryNetWorth
from docs import RequestHandler, define_api, Param
from celerys.tasks.fund import grab_last_month_data


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
            return self.write_fail(Code.NET_WORTH_NOT_EXIST, Message.NET_WORTH_NOT_EXIST)
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


class FundOptionalAdd(RequestHandler):
    @define_api('/fund/optional/add', [
        Param('code', True, str, '', '基金代码'),
    ], desc='添加自选基金')
    @login_required
    async def post(self):
        code = self.get_arg('code')
        exist = await FundOptionalRecord.objects.execute(
            FundOptionalRecord.select('code').where(FundOptionalRecord.code == code,
                                                    FundOptionalRecord.user_id == self.current_user_id,
                                                    FundOptionalRecord.is_delete == FundOptionalRecord.DELETE_NO))
        if exist:
            return self.write_fail(code=Code.FUND_IN_OPTIONAL_LIST, msg=Message.FUND_IN_OPTIONAL_LIST)
        fund_name = await FundData.get_fund_name(code)

        await FundOptionalRecord.async_create(self.current_user_id, code, fund_name)
        grab_last_month_data.delay(code)
        return self.write_success()


class FundOptionalList(RequestHandler):
    @define_api('/fund/optional/list', [
    ], desc='自选基金列表')
    @login_required
    async def get(self):
        records = await FundOptionalRecord.objects.execute(
            FundOptionalRecord.select().where(FundOptionalRecord.user_id == self.current_user_id,
                                              FundOptionalRecord.is_delete == FundOptionalRecord.DELETE_NO))
        data = list()
        for rec in records:
            temp = rec.normal_info()
            yesterday_net_worth, yesterday_growth_rate = (
                await FundRedis.get_last_day_net_worth(rec.code)).split(',')
            current_net_worth = await FundData.get_current_net_worth(rec.code)
            current_growth_rate = round(
                (current_net_worth - float(yesterday_net_worth)) / float(yesterday_net_worth) * 100, 2)
            temp.update({
                'yesterday_net_worth': yesterday_net_worth,
                'yesterday_growth_rate': yesterday_growth_rate,
                'current_net_worth': current_net_worth,
                'current_growth_rate': current_growth_rate,
            })
            data.append(temp)

        return self.write_success(data)


class FundOptionalDetail(RequestHandler):
    @define_api('/fund/optional/detail', [
        Param('code', True, str, '', '基金代码'),
    ], desc='自选基金详情')
    @login_required
    async def get(self):
        code = self.get_arg('code')
        records = FundHistoryNetWorth.query.find(
            {'code': code, 'is_delete': FundHistoryNetWorth.DELETE_NO})
        data = list()
        async for record in records:
            data.append({
                'code': record['code'],
                'fund_name': record['fund_name'],
                'net_worth': record['net_worth'],
                'date': dt.dt_to_str(record['date'], '%Y-%m-%d'),
                'daily_growth_rate': record['daily_growth_rate']
            })

        return self.write_success(data)


class FundOptionalDelete(RequestHandler):
    @define_api('/fund/optional/delete', [
        Param('code', True, str, '', '基金代码'),
    ], desc='删除自选基金')
    @login_required
    async def post(self):
        code = self.get_arg('code')
        await FundOptionalRecord.objects.execute(FundOptionalRecord.update(
            {FundOptionalRecord.is_delete: FundOptionalRecord.DELETE_IS}
        ).where(FundOptionalRecord.code == code,
                FundOptionalRecord.user_id == self.user_id,
                FundOptionalRecord.is_delete == FundOptionalRecord.DELETE_NO))
        return self.write_success()
