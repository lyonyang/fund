#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Mongoengine Doccument : http://docs.mongoengine.org/
Motor for Tornado Document : https://motor.readthedocs.io/en/stable/tutorial-tornado.html
Motor for query : https://motor.readthedocs.io/en/stable/api-tornado/motor_collection.html#motor.motor_tornado.MotorCollection
"""

import re
import datetime
from lib.dt import dt
from base import config
from mongoengine import Document, fields, connect
from motor.core import AgnosticCollection
from motor.motor_tornado import MotorClient
from motor.metaprogramming import create_class_with_framework

# Sync link
connect(config.MONGO_CONFIG["db"],
        host=config.MONGO_CONFIG['host'],
        port=config.MONGO_CONFIG["port"],
        username=config.MONGO_CONFIG["username"],
        password=config.MONGO_CONFIG["password"],
        maxPoolSize=config.MONGO_CONFIG['max_connections'],
        minPoolSize=config.MONGO_CONFIG['min_connections'],
        connect=False)

# Sync link
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

    # async collection
    database = mongo_db

    is_delete = fields.IntField(verbose_name='删除状态', default=DELETE_NO)
    create_time = fields.DateTimeField(verbose_name='创建时间', default=dt.now)
    update_time = fields.DateTimeField(verbose_name='更新时间', default=dt.now)

    # sync objects
    # type: Document._meta.objects

    # async objects
    query = Collection()

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
    def collection_name(cls):
        return cls._meta.get('collection', re.sub(HUMP_REGEX, r'\1_\2', cls.__name__))

    @classmethod
    async def async_create(cls, *items, **values):
        """
        Async create
        :param items: call `insert_many`
        :param values: call `insert_one`
        :return:
            items -> list[id] or None
            values -> Document object or None
        """
        if items:
            result = await cls.query.insert_many([cls(**i).to_mongo() for i in items])
            try:
                return result.inserted_ids
            except:
                return None

        if values:
            document = cls(**values)
            result = await cls.query.insert_one(document.to_mongo())
            try:
                document.pk = result.inserted_id
                document._id = result.inserted_id
                return document
            except:
                return None

    async def async_replace(self):
        assert (self.pk or self._id), "%s object's `_id` or `pk` cannot be None." % self.__class__.__name__
        return await self.__class__.query.replace_one({'_id': self.pk or self._id}, self.to_mongo())

    async def async_update(self, **kwargs):
        assert (self.pk or self._id), "%s object's `_id` or `pk` cannot be None." % self.__class__.__name__
        return await self.__class__.query.update_one({'_id': self.pk or self._id}, {'$set': kwargs})

    async def async_delete(self, *args, **kwargs):
        return await self.async_update(is_delete=self.DELETE_IS)

    @classmethod
    def create(cls, **kwargs):
        document = cls(**kwargs)
        document = super(MongoModel, document).save(**kwargs)
        return document

    def delete(self):
        """Override Document.delete"""
        return self.update(is_delete=self.DELETE_IS)

    def update(self, **kwargs):
        if not kwargs.get('update_time'):
            kwargs['update_time'] = datetime.datetime.now()
        super(MongoModel, self).update(**kwargs)
        return self

    def __str__(self):
        return "%s object [%s]" % (self.__class__.__name__, self.pk or self._id)
