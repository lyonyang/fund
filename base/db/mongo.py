#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Mongoengine Doccument : http://docs.mongoengine.org/
Motor for Tornado Document : https://motor.readthedocs.io/en/stable/tutorial-tornado.html
Motor for query : https://motor.readthedocs.io/en/stable/api-tornado/motor_collection.html#motor.motor_tornado.MotorCollection
"""

import re
from lib.dt import dt
from base import config
from mongoengine import Document, fields, connect
from motor.core import AgnosticCollection
from motor.motor_tornado import MotorClient
from motor.metaprogramming import create_class_with_framework

client = MotorClient(
    host=config.MONGO_CONFIG['host'],
    port=config.MONGO_CONFIG['port'],
    username=config.MONGO_CONFIG['username'],
    password=config.MONGO_CONFIG['password'],
    maxPoolSize=config.MONGO_CONFIG['max_connections'],
    minPoolSize=config.MONGO_CONFIG['min_connections'],
    authSource=config.MONGO_CONFIG['db'],
    authMechanism='SCRAM-SHA-1'
)

mongo_db = client[config.MONGO_CONFIG['db']]

HUMP_REGEX = re.compile(r'([a-z]|\d)([A-Z])')


class Collection(AgnosticCollection):
    """AgnosticCollection Object Descriptor."""

    def __init__(self):
        pass

    def __get__(self, instance, owner):
        collection_class = create_class_with_framework(
            AgnosticCollection, owner.database._framework, owner.database.__module__)
        return collection_class(owner.database, owner.collection_name())


class MongoModel(Document):
    DELETE_NO = 0
    DELETE_IS = 1

    database = mongo_db

    is_delete = fields.IntField(verbose_name='删除状态', default=DELETE_NO)
    create_time = fields.DateTimeField(verbose_name='创建时间', default=dt.now)
    update_time = fields.DateTimeField(verbose_name='更新时间', default=dt.now)

    async_objects = Collection()

    meta = {
        'abstract': True
    }

    def __init__(self, *args, **kwargs):
        _id = None
        if '_id' in kwargs:
            _id = kwargs.pop('_id')
        super(MongoModel, self).__init__(*args, **kwargs)
        self._id = _id
        self.pk = _id

    @classmethod
    def connect(cls):
        """Sync link."""
        connect(config.MONGO_CONFIG["db"], host=config.MONGO_CONFIG['host'],
                port=config.MONGO_CONFIG["port"], username=config.MONGO_CONFIG["username"],
                password=config.MONGO_CONFIG["password"], connect=False)

    @classmethod
    def collection_name(cls):
        return cls._meta.get('collection', re.sub(HUMP_REGEX, r'\1_\2', cls.__name__))

    @classmethod
    async def create_one(cls, **values):
        document = cls(**values)
        result = await cls.objects.insert_one(document.to_mongo())
        try:
            document.pk = result.inserted_id
            document._id = result.inserted_id
            return document
        except:
            return None

    @classmethod
    async def create_many(cls, *values):
        result = await cls.objects.insert_many([cls(**i).to_mongo() for i in values])
        try:
            return result.inserted_ids
        except:
            return None

    async def replace(self):
        assert (self.pk or self._id), "%s object's `_id` or `pk` cannot be None." % self.__class__.__name__
        return await self.__class__.objects.replace_one({'_id': self.pk or self._id}, self.to_mongo())

    async def update(self, **kwargs):
        assert (self.pk or self._id), "%s object's `_id` or `pk` cannot be None." % self.__class__.__name__
        return await self.__class__.objects.update_one({'_id': self.pk or self._id}, {'$set': kwargs})

    async def delete(self, *args, **kwargs):
        return await self.update(is_delete=self.DELETE_IS)

    def __str__(self):
        return "%s object [%s]" % (self.__class__.__name__, self.pk or self._id)
