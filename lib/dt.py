#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import datetime

DateTime = datetime.datetime


class DateTimeProxy:
    def dt_to_str(self, dt: DateTime, format: str = "%Y-%m-%d %H:%M:%S"):
        """datetime object --> str object"""
        if not dt:
            return None
        return dt.strftime(format)

    def str_to_dt(self, dt_str: str, format: str = "%Y-%m-%d %H:%M:%S"):
        """str object --> datetime object"""

        if "T" in dt_str and "Z" in dt_str:
            format += '.%fZ'
            return datetime.datetime.strptime(dt_str, format) + datetime.timedelta(
                hours=8)
        return datetime.datetime.strptime(dt_str, format)

    def now(self) -> DateTime:
        return datetime.datetime.now()

    def today(self) -> DateTime:
        return datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def today_str(self, format: str = "%Y-%m-%d"):
        return datetime.datetime.now().strftime(format)

    def yesterday(self):
        return self.today() - datetime.timedelta(days=1)

    def yesterday_str(self, format: str = "%Y-%m-%d"):
        return (self.today() - datetime.timedelta(days=1)).strftime(format)

    def now_str(self, format: str = "%Y-%m-%d %H:%M:%S"):
        return self.now().strftime(format)


dt = DateTimeProxy()
