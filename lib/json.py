#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

import json


def dumps(object: str):
    """
    json.dumps with exception
    """
    try:
        return json.dumps(str)
    except:
        return None


def loads(json_str):
    """
    json.loads with exception
    """
    try:
        return json.loads(json_str)
    except:
        return None
