#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Aioredis document : https://aioredis.readthedocs.io/en/v1.3.0/examples.html
Redis Command Reference: http://redisdoc.com/
"""

import uuid
import time
import aioredis
import datetime
from redis import Redis
import tornado.gen
import tornado.ioloop
from base import config
from aioredis import ConnectionsPool

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

iteritems = lambda x: iter(x.items())

EMPTY_RESPONSE = 'EMPTY_RESPONSE'


def list_or_args(keys, args):
    # returns a single new list combining keys and args
    try:
        iter(keys)
        # a string or bytes instance can be iterated, but indicates
        # keys wasn't passed as a list
        if isinstance(keys, (str, bytes)):
            keys = [keys]
        else:
            keys = list(keys)
    except TypeError:
        keys = [keys]
    if args:
        keys.extend(args)
    return keys


# Async Redis
class _AsyncConnectionContextManager:
    __slots__ = ('_pool', '_conn')

    def __init__(self, pool):
        self._pool = pool
        self._conn = None

    async def __aenter__(self):
        # pool._wait_execute
        conn = await self._pool.acquire()
        self._conn = conn
        return self._conn

    async def __aexit__(self, exc_type, exc_value, tb):
        try:
            self._pool.release(self._conn)
        finally:
            self._pool = None
            self._conn = None


class RedisMixin:
    """Redis 方法, 尚未完全补全, 补全参考
        >>> from redis import Redis
        >>> # self.execute_command -> await self.execute
        命令参考 : http://redisdoc.com/index.html
    """

    async def execute(self, command, *args, **kwargs):
        raise NotImplementedError

    # 字符串
    async def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        pieces = [name, value]
        if ex is not None:
            pieces.append('EX')
            if isinstance(ex, datetime.timedelta):
                ex = int(ex.total_seconds())
            pieces.append(ex)
        if px is not None:
            pieces.append('PX')
            if isinstance(px, datetime.timedelta):
                px = int(px.total_seconds() * 1000)
            pieces.append(px)

        if nx:
            pieces.append('NX')
        if xx:
            pieces.append('XX')
        return await self.execute('SET', *pieces)

    async def setnx(self, name, value):
        "Set the value of key ``name`` to ``value`` if key doesn't exist"
        return await self.execute('SETNX', name, value)

    async def setex(self, name, time, value):
        """
        Set the value of key ``name`` to ``value`` that expires in ``time``
        seconds. ``time`` can be represented by an integer or a Python
        timedelta object.
        """
        if isinstance(time, datetime.timedelta):
            time = int(time.total_seconds())
        return await self.execute('SETEX', name, time, value)

    async def psetex(self, name, time_ms, value):
        """
        Set the value of key ``name`` to ``value`` that expires in ``time_ms``
        milliseconds. ``time_ms`` can be represented by an integer or a Python
        timedelta object
        """
        if isinstance(time_ms, datetime.timedelta):
            time_ms = int(time_ms.total_seconds() * 1000)
        return await self.execute('PSETEX', name, time_ms, value)

    async def get(self, name):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        """
        return await self.execute('GET', name)

    async def getset(self, name, value):
        """
        Sets the value at key ``name`` to ``value``
        and returns the old value at key ``name`` atomically.
        """
        return await self.execute('GETSET', name, value)

    async def strlen(self, name):
        "Return the number of bytes stored in the value of ``name``"
        return await self.execute('STRLEN', name)

    # BASIC KEY COMMANDS
    async def append(self, key, value):
        """
        Appends the string ``value`` to the value at ``key``. If ``key``
        doesn't already exist, create it with a value of ``value``.
        Returns the new length of the value at ``key``.
        """
        return await self.execute('APPEND', key, value)

    async def setrange(self, name, offset, value):
        """
        Overwrite bytes in the value of ``name`` starting at ``offset`` with
        ``value``. If ``offset`` plus the length of ``value`` exceeds the
        length of the original value, the new value will be larger than before.
        If ``offset`` exceeds the length of the original value, null bytes
        will be used to pad between the end of the previous value and the start
        of what's being injected.

        Returns the length of the new string.
        """
        return await self.execute('SETRANGE', name, offset, value)

    async def getrange(self, key, start, end):
        """
        Returns the substring of the string value stored at ``key``,
        determined by the offsets ``start`` and ``end`` (both are inclusive)
        """
        return await self.execute('GETRANGE', key, start, end)

    async def incr(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        """
        return await self.incrby(name, amount)

    async def incrby(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        """
        # An alias for ``incr()``, because it is already implemented
        # as INCRBY redis command.
        return await self.execute('INCRBY', name, amount)

    async def incrbyfloat(self, name, amount=1.0):
        """
        Increments the value at key ``name`` by floating ``amount``.
        If no key exists, the value will be initialized as ``amount``
        """
        return await self.execute('INCRBYFLOAT', name, amount)

    async def decr(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        """
        # An alias for ``decr()``, because it is already implemented
        # as DECRBY redis command.
        return await self.decrby(name, amount)

    async def decrby(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        """
        return await self.execute('DECRBY', name, amount)

    async def mget(self, keys, *args):
        """
        Returns a list of values ordered identically to ``keys``
        """
        args = list_or_args(keys, args)
        options = {}
        if not args:
            options[EMPTY_RESPONSE] = []
        return await self.execute('MGET', *args, **options)

    async def mset(self, mapping):
        """
        Sets key/values based on a mapping. Mapping is a dictionary of
        key/value pairs. Both keys and values should be strings or types that
        can be cast to a string via str().
        """
        items = []
        for pair in iteritems(mapping):
            items.extend(pair)
        return await self.execute('MSET', *items)

    async def msetnx(self, mapping):
        """
        Sets key/values based on a mapping if none of the keys are already set.
        Mapping is a dictionary of key/value pairs. Both keys and values
        should be strings or types that can be cast to a string via str().
        Returns a boolean indicating if the operation was successful.
        """
        items = []
        for pair in iteritems(mapping):
            items.extend(pair)
        return await self.execute('MSETNX', *items)

    # 数据库
    async def keys(self, pattern='*'):
        "Returns a list of keys matching ``pattern``"
        return await self.execute('KEYS', pattern)

    # 客户端与服务器
    async def client_getname(self):
        "Returns the current connection name"
        return await self.execute('CLIENT GETNAME')

    async def client_id(self):
        "Returns the current connection id"
        return await self.execute('CLIENT ID')

    async def client_setname(self, name):
        "Sets the current connection name"
        return await self.execute('CLIENT SETNAME', name)

    # 配置
    async def config_get(self, pattern="*"):
        "Return a dictionary of configuration based on the ``pattern``"
        return await self.execute('CONFIG GET', pattern)

    async def config_set(self, name, value):
        "Set config item ``name`` with ``value``"
        return await self.execute('CONFIG SET', name, value)

    async def config_resetstat(self):
        "Reset runtime statistics"
        return await self.execute('CONFIG RESETSTAT')

    async def config_rewrite(self):
        "Rewrite config file with the minimal change to reflect running config"
        return await self.execute('CONFIG REWRITE')


class AsyncRedis(RedisMixin):
    """Async Redis"""

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

    async def execute(self, command, *args, **kwargs):
        async with self.conn() as conn:
            result = await conn.execute(command, *args, **kwargs)
            return result

    async def decode(self, result):
        return None if result is None else result.decode()


try:
    async_redis = AsyncRedis(
        config.REDIS_CONFIG['host'],
        config.REDIS_CONFIG['port'],
        config.REDIS_CONFIG['db'],
        config.REDIS_CONFIG['password'],
        config.REDIS_CONFIG['min_connections'],
        config.REDIS_CONFIG['max_connections']
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
