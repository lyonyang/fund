#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import hashlib
from base import config
from base.db.mysql import MySQLModel
from peewee import (
    CharField
)


class FundUser(MySQLModel):
    class Meta:
        table_name = 'fund_user'

    DEFAULT_AVATAR = ''

    name = CharField(max_length=32, unique=True, verbose_name='姓名')
    phone = CharField(max_length=11, null=True, verbose_name='手机号')
    password = CharField(max_length=255, null=True, verbose_name='手机号')
    avatar = CharField(max_length=255, null=True, default=DEFAULT_AVATAR, verbose_name='头像')

    def normal_info(self):
        data = super(FundUser, self).normal_info()
        data.update({
            'name': self.name,
            'phone': self.phone,
            'avatar': self.avatar,
        })
        return data

    @classmethod
    async def async_create(cls, phone, name, password, **kwargs):
        _obj = await super(FundUser, cls).async_create(phone=phone, name=name, password=password)
        return _obj

    @classmethod
    def get_md5(cls, password):
        md = hashlib.md5()
        md.update((config.backend_md5_salt + password).encode('utf-8'))
        return md.hexdigest()
