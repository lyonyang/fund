#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


import jwt
import datetime
import logging

jwt_log = logging.getLogger("JWT")


def jwt_encode(data, secret_key, expires=None, issuer=""):
    """
    生成token
    :param data: 用户数据
    :param secret_key: 加密串
    :param expires: 过期时间, 天
    :param issuer: 发行者
    :return:
    """
    if expires is None:
        expires = 7

    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=expires, seconds=0),  # 过期时间
        'iat': datetime.datetime.utcnow(),  # 发布时间
        'iss': issuer,
        'data': data
    }
    try:
        token = jwt.encode(
            payload,
            secret_key,
            algorithm='HS256'
        )
    except Exception as e:
        jwt_log.error(e)
        return None
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def jwt_decode(token, secret_key, **options):
    """
    解析token
    :param token:
    :param secret_key:
    :param options: 解析参数
    :return:
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms='HS256', options=options)
    except Exception as e:
        jwt_log.error(e)
        return None
    return payload
