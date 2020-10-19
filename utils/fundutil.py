#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import re
import time
import json
import datetime
import requests
from lib.dt import dt
from lxml import etree
from tornado.httpclient import AsyncHTTPClient

DATE_RE = re.compile(r'<tr>(.*?)</tr>')
LINE_RE = re.compile(
    r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?></td>''',
    re.X)


class FundData:
    client = AsyncHTTPClient()

    # 基金列表
    FUND_LIST = 'http://fund.eastmoney.com/js/fundcode_search.js'

    # 历史净值
    # 示例: http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=001618&page=1
    # 示例: http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=001618&page=1&per=50
    # 示例: http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=001618&page=1&per=20&sdate=2017-03-01&edate=2017-03-01
    # raw=True (净值日期, 单位净值, 累计净值, 日增长率, 申购状态, 赎回状态, 分红送配)
    FUND_NET_WORTH_URL = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=%s&page=%s&per=%s'
    FUND_NET_WORTH_URL_BY_DATE = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=%s&page=%s&per=%s&sdate=%s&edate=%s'

    # 基金信息
    # 示例: http://fund.eastmoney.com/001618.html?spm=search
    FUND_INFO_URL = 'http://fund.eastmoney.com/%s.html?spm=search'

    # 基金实时净值
    FUND_NET_WORTH = 'http://fundgz.1234567.com.cn/js/%s.js?rt=%s'

    # 解析历史净值数据
    data_re = re.compile(r'<tr>(.*?)</tr>')
    line_re = re.compile(
        r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?></td>''',
        re.X)

    @classmethod
    def sync_get_fund_name(cls, code):
        """获取基金名称"""
        url = cls.FUND_INFO_URL % code
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        try:
            html = etree.HTML(response.text)
            b = html.xpath('//div[@class="fundDetail-tit"]')
        except:
            return None
        if not b: return None
        return b[0].findtext('div')

    @classmethod
    def sync_get_section_net_worth(cls, code, start_time, end_time, raw=False):
        """获取时间区间净值"""
        url = cls.FUND_NET_WORTH_URL_BY_DATE % (code, 1, 10, start_time, end_time)
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        line = cls.data_re.findall(response.text)[1]
        match = cls.line_re.match(line)
        data = list()
        if match:
            entry = match.groups()
            if raw:
                data.append(entry)
            else:
                data.append(entry[1])
        return data

    @classmethod
    def sync_get_last_month_net_worth(cls, code):
        """同步方法, 获取近一个月的净值, 包含非交易日"""
        yesterday = dt.yesterday()
        last_month = yesterday - datetime.timedelta(days=30)
        url = cls.FUND_NET_WORTH_URL_BY_DATE % (
            code, 1, 10, last_month.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        )
        response = requests.get(url)
        lines = cls.data_re.findall(response.text)
        res = list()
        for i in range(1, len(lines)):
            match = cls.line_re.match(lines[i])
            if match:
                entry = match.groups()
                res.append(entry)
        return res

    @classmethod
    def sync_get_last_thirty_net_worth(cls, code):
        """获取近30个交易日的净值"""
        url = cls.FUND_NET_WORTH_URL % (code, 1, 30)
        response = requests.get(url)
        lines = cls.data_re.findall(response.text)
        res = list()
        for i in range(1, len(lines)):
            match = cls.line_re.match(lines[i])
            if match:
                entry = match.groups()
                res.append(entry)
        return res

    @classmethod
    async def get_date_net_worth(cls, code, date, raw=False):
        """获取单个时间净值"""
        url = cls.FUND_NET_WORTH_URL_BY_DATE % (code, 1, 1, date, date)
        response = await cls.client.fetch(url)
        line = cls.data_re.findall(response.body.decode())[1]
        match = cls.line_re.match(line)
        if match:
            entry = match.groups()
            if raw:
                return entry
            return float(entry[1])
        return None

    @classmethod
    async def get_yesterday_net_worth(cls, code, raw=False):
        """获取昨日净值"""
        yesterday = dt.yesterday()
        if yesterday.weekday() in {5, 6}:
            pass
        return await cls.get_date_net_worth(code, dt.yesterday_str(), raw)

    @classmethod
    async def get_last_day_net_worth(cls, code, raw=False):
        """获取最后一个交易日净值"""
        url = cls.FUND_NET_WORTH_URL % (code, 1, 1)
        response = await cls.client.fetch(url)
        line = cls.data_re.findall(response.body.decode())[1]
        match = cls.line_re.match(line)
        if match:
            entry = match.groups()
            if raw:
                return entry
            return float(entry[1])
        return None

    @classmethod
    async def get_fund_name(cls, code):
        """获取基金名称"""
        url = cls.FUND_INFO_URL % code
        response = await cls.client.fetch(url)
        try:
            html = etree.HTML(response.body.decode())
            b = html.xpath('//div[@class="fundDetail-tit"]')
        except:
            return None
        if not b: return None
        fund_name = b[0].findtext('div')
        return fund_name

    @classmethod
    async def get_current_net_worth_old(cls, code):
        """获取实时的当前净值(旧版本, 暂时不用)"""
        url = cls.FUND_INFO_URL % code + '&' + str(time.time())
        response = await cls.client.fetch(url)
        try:
            html = etree.HTML(response.body.decode())
            b = html.xpath('//dd[@class="dataNums"]//text()')
        except:
            return None
        if len(b) != 6: return None
        cur_net_worth, date_net_worth, total_net_worth = b[0], b[3], b[5]
        return float(cur_net_worth)

    @classmethod
    async def get_current_net_worth(cls, code):
        """获取实时的当前净值"""
        url = cls.FUND_NET_WORTH % (code, int(time.time()))
        response = await cls.client.fetch(url)
        data = json.loads(response.body.decode()[8: -2])
        return float(data['gsz'])


if __name__ == '__main__':
    from tornado.ioloop import IOLoop


    async def main():
        return await FundData.get_current_net_worth('009308')


    result = IOLoop.current().run_sync(main)
    print(result)
