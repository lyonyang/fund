#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import re
import time
import datetime
from lib.dt import dt
from lxml import etree
from tornado.httpclient import AsyncHTTPClient

DATE_RE = re.compile(r'<tr>(.*?)</tr>')
LINE_RE = re.compile(
    r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?></td>''',
    re.X)


class FundData:
    client = AsyncHTTPClient()
    # 历史净值
    # 示例: http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=001618&page=1
    FUND_HISTORY_NET_WORTH_URL = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=%s&page=%s'

    # 基金信息
    # 示例: http://fund.eastmoney.com/001618.html?spm=search
    FUND_INFO_URL = 'http://fund.eastmoney.com/%s.html?spm=search'

    # 解析历史净值数据
    data_re = re.compile(r'<tr>(.*?)</tr>')
    line_re = re.compile(
        r'''<td>(\d{4}-\d{2}-\d{2})</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?>(.*?)</td><td.*?></td>''',
        re.X)

    @classmethod
    async def get_date_net_worth(cls, code, date):
        days = (dt.yesterday() - dt.str_to_dt(date, "%Y-%m-%d")).days + 1
        total_count = 0
        weekend = set(list([5, 6]))
        for d in range(days):
            day = dt.yesterday() - datetime.timedelta(days=d)
            if day.weekday() in weekend:
                continue
            total_count += 1
        page = total_count // 10 + (1 if total_count % 10 != 0 else 0)

        url = cls.FUND_HISTORY_NET_WORTH_URL % (code, page)
        response = await cls.client.fetch(url)
        net_worth_map = dict()
        for line in cls.data_re.findall(response.body.decode()):
            match = cls.line_re.match(line)
            if match:
                entry = match.groups()
                net_worth_map[entry[0]] = entry[1]
        if date not in net_worth_map:
            return None
        return float(net_worth_map[date])

    @classmethod
    async def get_fund_name(cls, code):
        """
        获取基金名称
        :param code:
        :return:
        """
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
    async def get_current_net_worth(cls, code):
        """
        获取当前净值
        :param code:
        :return:
        """
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
    async def get_pre_net_worth(cls, code):
        """
        获取昨日净值
        :param code:
        :return:
        """
        url = cls.FUND_HISTORY_NET_WORTH_URL % (code, 1)
        response = await cls.client.fetch(url)
        data = response.body.decode()
        for line in cls.data_re.findall(data):
            match = cls.line_re.match(line)
            if match:
                entry = match.groups()
                if entry[0] == dt.today_str():
                    continue
                return float(entry[1])
        return None


if __name__ == '__main__':
    from tornado.ioloop import IOLoop


    async def main():
        return await FundData.get_fund_name('001618')


    result = IOLoop.current().run_sync(main)
    print(result)
