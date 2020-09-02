#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import jwt
from functools import wraps
from api.status import Code, Message
from base import config


def login_required(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            type, token = self.request.headers.get('Authorization', ' ').split(' ')
            payload = jwt.decode(
                token,
                config.BACKEND_TOKEN_SECRET_KEY,
                options={'verify_exp': config.DOCS_TOKEN_VERIFY_EXPIRE})
            data = payload['data']
        except Exception:
            return self.finish({'return_code': Code.TOKEN_INVALID, 'return_msg': Message.TOKEN_INVALID})
        self.current_user_id = data['user_id']

        return method(self, *args, **kwargs)

    return wrapper
