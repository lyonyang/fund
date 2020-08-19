#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Aioredis document : https://aioredis.readthedocs.io/en/v1.3.0/examples.html
Redis Command Reference: http://redisdoc.com/
"""

import uuid
import time
import tornado.gen
import aioredis
import tornado.ioloop
from base import config
from aioredis import ConnectionsPool

"""
Sync Redis:

    >>> import redis
    >>> redis_pool = redis.ConnectionPool(
    >>>     max_connections=config.redis_config['max_connections'],
    >>>     host=config.redis_config['host'],
    >>>     db=config.redis_config['db'],
    >>>     password=config.redis_config['password'],
    >>>     port=config.redis_config['port'],
    >>> )
    >>> conn = redis.Redis(connection_pool=redis_pool, decode_responses=True)
"""


# Async Redis
class _AsyncConnectionContextManager:
    __slots__ = ('_pool', '_conn')

    def __init__(self, pool):
        self._pool = pool
        self._conn = None

    async def __aenter__(self):
        conn = await self._pool.acquire()
        self._conn = conn
        return self._conn

    async def __aexit__(self, exc_type, exc_value, tb):
        try:
            self._pool.release(self._conn)
        finally:
            self._pool = None
            self._conn = None


class AsyncRedis:
    # Commands

    GET = 'get'

    def __init__(self, host, port, db=0, password=None, minsize=1, maxsize=10,
                 ssl=None, encoding=None, parser=None, loop=None, create_connection_timeout=None,
                 pool_cls=ConnectionsPool, connection_cls=None):
        self.address = (host, port)
        self.db = db
        self.password = password
        self.minsize = minsize
        self.maxsize = maxsize
        self.pool = pool_cls(self.address, db=db, password=password, encoding=encoding,
                             minsize=minsize, maxsize=maxsize,
                             ssl=ssl, parser=parser,
                             create_connection_timeout=create_connection_timeout,
                             connection_cls=connection_cls,
                             loop=loop)

    def conn(self):
        return _AsyncConnectionContextManager(self.pool)

    async def get(self, name):
        async with self.conn() as conn:
            return await conn.execute(self.GET, name)


try:
    async_redis = AsyncRedis(
        config.redis_config['host'],
        config.redis_config['port'],
        config.redis_config['db'],
        config.redis_config['password'],
        config.redis_config['min_connections'],
        config.redis_config['max_connections']
    )
except:
    async_redis = None


class AsyncLock:
    LOCK_PRE = 'lock:'

    def __init__(self, redis):
        self.redis = redis

    async def acquire_lock(self, lock_name, acquire_time=10, time_out=10):
        id = str(uuid.uuid4())
        end = time.time() + acquire_time
        lock_name = self.LOCK_PRE + lock_name

        while time.time() < end:
            # If key doesn't exist return `False` else `True`
            async with self.redis.conn() as conn:
                if await conn.execute('setnx', lock_name, id):
                    await conn.execute('expire', lock_name, time_out)
                    return id
                # Set an expire flag on key
                elif await conn.execute('ttl', lock_name) == -1:
                    await conn.execute('expire', lock_name, time_out)

            await tornado.gen.sleep(0.001)
        return False

    async def release_lock(self, lock_name, id):
        lock_name = self.LOCK_PRE + lock_name
        async with self.redis.conn() as conn:
            pipe = await conn.pipeline()
            while True:
                try:
                    await pipe.watch(lock_name)
                    if await pipe.get(lock_name) == id:
                        pipe.conn.multi_exec()
                        pipe.delete(lock_name)
                        await pipe.execute()
                        return True
                    await pipe.unwatch()
                    break
                except aioredis.WatchVariableError:
                    continue
        return False


async_lock = AsyncLock(async_redis)
