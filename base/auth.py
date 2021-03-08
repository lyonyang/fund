#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

from functools import wraps
from api.status import Code, Message


def login_required(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):

        from apps.users.user import FundUser

        res = self.request.headers.get('Authorization', ' ').split(' ')
        if len(res) < 2 or not res[1]:
            self.write_bad_request()
        token = res[1]
        data = FundUser.decode_token(token)
        if data is None:
            return self.write_fail(Code.User.TOKEN_INVALID, Message.User.TOKEN_INVALID)
        self.current_user_id = data.get('user_id')

        return await method(self, *args, **kwargs)

    return wrapper
