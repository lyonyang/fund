#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Base lock
"""
import uuid
import time
import tornado.gen
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


class RedisLock(Lock):
    async_client = async_redis
    sync_client = sync_redis

    def __init__(self, *args, async_client=None, sync_client=None, time_out=10, expire_time=10, **kwargs):
        if async_client:
            self.async_client = async_client
        if sync_client:
            self.sync_client = sync_client
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
        release_script = """
            if redis.call("get",KEYS[1]) == ARGV[1] then
                return redis.call("del",KEYS[1])
            else
                return 0
            end
            """
        try:
            await self.async_client.eval(release_script, keys=[lock_name], args=[self.id])
        except Exception as e:
            raise ReleaseError

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
        release_script = """
            if redis.call("get",KEYS[1]) == ARGV[1] then
                return redis.call("del",KEYS[1])
            else
                return 0
            end
            """
        try:
            self.sync_client.register_script(release_script)(keys=[lock_name], args=[self.id])
        except Exception as e:
            raise ReleaseError

    def get_lock_name(self):
        raise NotImplementedError()
