#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


from apps.users.user import FundUser
from api.status import Code, Message
from base.auth import login_required
from docs import RequestHandler, define_api, Param


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
        user = await FundUser.async_get(phone=phone, password=password, is_delete=FundUser.DELETE_NO)
        if user:
            return self.write_fail(Code.User.USER_IS_EXIST, Message.User.USER_IS_EXIST)
        user = await FundUser.async_create(phone=phone, name=name, password=password)
        return self.write_success({'token': FundUser.encode_token(user)})


class UserLogin(RequestHandler):
    @define_api('/fund/user/login', [
        Param('phone', True, str, '', '手机号'),
        Param('password', False, str, '', '密码'),
    ], desc='登录')
    async def post(self):
        phone = self.get_arg('phone')
        password = self.get_arg('password')
        user = await FundUser.async_get(phone=phone, password=password, is_delete=FundUser.DELETE_NO)
        if user:
            return self.write_success({'token': FundUser.encode_token(user)})
        return self.write_fail(Code.User.USERNAME_OR_PASSWORD_INVALID, Message.User.USERNAME_OR_PASSWORD_INVALID)


class UserInfo(RequestHandler):
    @define_api('/fund/user/info', [
    ], desc='用户信息')
    @login_required
    async def get(self):
        user = await FundUser.async_get(id=self.current_user_id)
        return self.write_success(data=user.normal_info())
