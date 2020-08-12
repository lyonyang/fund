#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
TODO : 基金模拟
"""

from base.auth import login_required
from docs import RequestHandler, define_api, Param
from apps.users.trade import TradeRecord
from api.status import Code, Message
from utils.fundutil import FundData


class FundSim(RequestHandler):
    @define_api('/fund/simulate', [
    ], desc='基金模拟')
    async def post(self):
        return self.write_success(data={})
