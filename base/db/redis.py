#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Aioredis document : https://aioredis.readthedocs.io/en/v1.3.0/examples.html
Redis Command Reference: http://redisdoc.com/, http://redis.io/commands/#connection
"""

import redis
import aioredis
from base import config

"""
Sync Redis:

    >>> import redis
    >>> redis_pool = redis.ConnectionPool(
    >>>     max_connections=config.REDIS_CONFIG['max_connections'],
    >>>     host=config.REDIS_CONFIG['host'],
    >>>     db=config.REDIS_CONFIG['db'],
    >>>     password=config.REDIS_CONFIG['password'],
    >>>     port=config.REDIS_CONFIG['port'],
    >>> )
    >>> conn = redis.Redis(connection_pool=redis_pool, decode_responses=True)
"""


class SyncRedis(redis.Redis):
    def __init__(self, host, port, db=0, password=None,
                 max_connections=10,
                 socket_timeout=None, socket_connect_timeout=None, encoding='utf-8', decode_responses=True,
                 pool_cls=redis.ConnectionPool):
        pool = pool_cls(max_connections=max_connections, host=host,
                        db=db, password=password, port=port,
                        socket_timeout=socket_timeout, socket_connect_timeout=socket_connect_timeout,
                        encoding=encoding, decode_responses=decode_responses)

        super(SyncRedis, self).__init__(connection_pool=pool)


class AsyncRedis(aioredis.Redis):
    """Async Redis"""

    def __init__(self, pool_or_conn=None, host='localhost', port=6379, db=0, password=None, min_connections=1,
                 max_connections=10,
                 ssl=None, encoding='utf-8', parser=None, loop=None, create_connection_timeout=None,
                 pool_cls=aioredis.ConnectionsPool, connection_cls=None):

        if not pool_or_conn:
            address = (host, port)
            pool = pool_cls(address, db=db, password=password, encoding=encoding,
                            minsize=min_connections, maxsize=max_connections,
                            ssl=ssl, parser=parser,
                            create_connection_timeout=create_connection_timeout,
                            connection_cls=connection_cls,
                            loop=loop)
        else:
            pool = pool_or_conn
        super(AsyncRedis, self).__init__(pool)


try:
    sync_redis = SyncRedis(
        host=config.REDIS_CONFIG['host'],
        port=config.REDIS_CONFIG['port'],
        db=config.REDIS_CONFIG['db'],
        password=config.REDIS_CONFIG['password'],
        max_connections=config.REDIS_CONFIG['max_connections']
    )
except:
    sync_redis = None

try:
    async_redis = AsyncRedis(
        host=config.REDIS_CONFIG['host'],
        port=config.REDIS_CONFIG['port'],
        db=config.REDIS_CONFIG['db'],
        password=config.REDIS_CONFIG['password'],
        min_connections=config.REDIS_CONFIG['min_connections'],
        max_connections=config.REDIS_CONFIG['max_connections']
    )
except:
    async_redis = None
