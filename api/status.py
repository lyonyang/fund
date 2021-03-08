#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon


class Code:
    # 系统状态
    class System:
        SUCCESS = 0
        ERROR = -1

    # 项目状态码为6位数
    class User:
        USERNAME_OR_PASSWORD_INVALID = 110001
        USER_NOT_EXIST = 110002
        TOKEN_INVALID = 110003
        USER_IS_EXIST = 110004

    # 基金相关
    class Fund:
        NET_WORTH_NOT_EXIST = 120001
        FUND_IN_OPTIONAL_LIST = 120002


class Message:
    class System:
        # 系统状态
        SUCCESS = "成功!"
        ERROR = "系统繁忙~"

    class User:
        # API文档相关
        USERNAME_OR_PASSWORD_INVALID = "用户名或密码错误!"
        USER_NOT_EXIST = "该用户不存在!"
        TOKEN_INVALID = 'Token无效!'
        USER_IS_EXIST = "手机号已存在, 请直接登录!"

    class Fund:
        NET_WORTH_NOT_EXIST = "净值不存在!"
        FUND_IN_OPTIONAL_LIST = "该基金在自选列表中!"
