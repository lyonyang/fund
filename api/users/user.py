#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


from api.status import Code, Message
from base.auth import login_required
from docs import RequestHandler, define_api, Param
from apps.users.user import FundUser


class UserRegister(RequestHandler):
    @define_api('/fund/user/register', [
        Param('phone', True, str, '', '手机号'),
        Param('password', True, str, '', '密码'),
        Param('name', True, str, '', '昵称'),
    ], desc='注册')
    async def post(self):
        phone = self.get_arg('phone')
        name = self.get_arg('name')
        password = self.get_arg('password')
        user = await FundUser.objects.get(
            FundUser.select().where(FundUser.phone == phone, FundUser.password == password))
        if user:
            return self.write_fail(Code.USER_IS_EXIST, Message.USER_IS_EXIST)
        user = await FundUser.async_create(phone=phone, name=name, password=password)
        return self.write_success(Code.SUCCESS, {'token': self.token_encode(user.id)})


class UserLogin(RequestHandler):
    @define_api('/fund/user/login', [
        Param('phone', True, str, '', '手机号'),
        Param('password', False, str, '', '密码'),
    ], desc='登录')
    async def post(self):
        phone = self.get_arg('phone')
        password = self.get_arg('password')
        try:
            user = await FundUser.objects.get(
                FundUser.select().where(FundUser.phone == phone, FundUser.password == password))
            if user.id:
                return self.write_success({'token': self.token_encode(user.id)})
        except Exception as e:
            self.app.logger.info(e)
            return self.write_fail(Code.USERNAME_OR_PASSWORD_INVALID, Message.USERNAME_OR_PASSWORD_INVALID)
        return self.write_fail(Code.USERNAME_OR_PASSWORD_INVALID, Message.USERNAME_OR_PASSWORD_INVALID)


class UserInfo(RequestHandler):
    @define_api('/fund/user/info', [
    ], desc='用户信息')
    @login_required
    async def get(self):
        user = await FundUser.objects.get(FundUser.select().where(FundUser.id == self.user_id))

        return self.write_success(data=user.normal_info())
