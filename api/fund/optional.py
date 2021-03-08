#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from lib.dt import dt
from cache.fund import FundRedis
from base.auth import login_required
from api.status import Code, Message
from utils.fundutil import FundData
from apps.users.fund import FundOptionalRecord
from apps.fund.info import FundHistoryNetWorth
from docs import RequestHandler, define_api, Param
from celerys.tasks.fund import grab_last_month_data


class FundOptionalAdd(RequestHandler):
    @define_api('/fund/optional/add', [
        Param('code', True, str, '', '基金代码'),
    ], desc='添加自选基金')
    @login_required
    async def post(self):
        code = self.get_arg('code')

        exist = await FundOptionalRecord.execute_sql(
            "SELECT code FROM fund_optional_record WHERE code = %s AND user_id = %s AND is_delete = %s", code,
            self.current_user_id, FundOptionalRecord.DELETE_NO)
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
            {'code': code, 'is_delete': FundHistoryNetWorth.DELETE_NO}).sort([('date', 1)])

        data = dict()
        labels, series = list(), list()
        async for record in records:
            if not labels:
                data['fund_name'] = record['fund_name']
                data['fund_name'] = record['fund_name']
            series.append(round(int(record['net_worth']) / 1000, 4))
            labels.append(dt.dt_to_str(record['date'], '%m-%d'))
        data = {'labels': labels, 'series': series}

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
