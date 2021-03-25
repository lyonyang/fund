#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Base lock
"""

import uuid
import time
import tornado.gen
from redis.exceptions import WatchError
from aioredis.errors import WatchVariableError
from base.db.redis import async_redis, sync_redis


class AcquireError(Exception):
    def __init__(self):
        pass


class ReleaseError(Exception):
    def __init__(self):
        pass


class Lock:
    def acquire(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    async def async_acquire(self):
        raise NotImplementedError

    async def async_release(self):
        raise NotImplementedError

    # Sync with
    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.release()

    # Async with
    async def __aenter__(self):
        await self.async_acquire()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.async_release()


class AsyncRedisLock(Lock):
    def __init__(self, *args, async_client=None, time_out=10, expire_time=20, **kwargs):
        if async_client:
            self.async_client = async_client
        else:
            self.async_client = async_redis
        assert self.async_client is not None
        self.args = args
        self.time_out = time_out
        self.expire_time = expire_time
        self.kwargs = kwargs
        self.id = None
        self.ok = False

    async def async_acquire(self):
        self.id = str(uuid.uuid4())
        end = time.time() + self.time_out
        lock_name = self.get_lock_name()
        while time.time() < end:
            if await self.async_client.setnx(lock_name, self.id):
                await self.async_client.expire(lock_name, self.expire_time)
                return self
            elif not await self.async_client.ttl(lock_name):
                await self.async_client.expire(lock_name, self.expire_time)
            await tornado.gen.sleep(0.001)
        raise AcquireError

    async def async_release(self):
        lock_name = self.get_lock_name()
        pipe = self.async_client.multi_exec()
        while True:
            try:
                await self.async_client.watch(lock_name)
                val = await self.async_client.get(lock_name)
                if val and isinstance(val, bytes):
                    val = val.decode('utf-8')
                if val == self.id:
                    pipe.delete(lock_name)
                    await pipe.execute()
                    self.ok = True
                    return self.id
                await self.async_client.unwatch()
                break
            except WatchVariableError:
                pass

    def get_lock_name(self):
        raise NotImplementedError()


class SyncRedisLock(Lock):
    def __init__(self, *args, sync_client=None, time_out=10, **kwargs):
        if sync_client:
            self.sync_client = sync_client
        else:
            self.sync_client = sync_redis
        assert self.sync_client is not None
        self.args = args
        self.time_out = time_out
        self.kwargs = kwargs
        self.id = None
        self.ok = False

    def acquire(self):
        self.id = str(uuid.uuid4())
        end = time.time() + self.time_out
        lock_name = self.get_lock_name()
        while time.time() < end:
            if self.sync_client.setnx(lock_name, self.id):
                self.sync_client.expire(lock_name, self.time_out)
                return self.id
            elif not self.sync_client.ttl(lock_name):
                self.sync_client.expire(lock_name, self.time_out)
            time.sleep(0.001)
        raise AcquireError

    def release(self):
        lock_name = self.get_lock_name()
        pip = self.sync_client.pipeline(True)
        while True:
            try:
                pip.watch(lock_name)
                lock_value = self.sync_client.get(lock_name)
                if not lock_value:
                    break
                if lock_value.decode() == self.id:
                    pip.multi()
                    pip.delete(lock_name)
                    pip.execute()
                    self.ok = True
                    break
                pip.unwatch()
                break
            except WatchError:
                pass

    def get_lock_name(self):
        raise NotImplementedError()
