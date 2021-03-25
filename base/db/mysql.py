#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Peewee Document : http://docs.peewee-orm.com/en/latest/
Peewee-async Document : https://peewee-async.readthedocs.io/en/latest/index.html
"""

from lib.dt import dt
from base import config
from peewee import Model, AutoField, DateTimeField, IntegerField, Query, ModelRaw
from peewee_async import Manager as BaseManager, PooledMySQLDatabase

# Connect to a MySQL database on network.
mysql_db = PooledMySQLDatabase(
    config.MYSQL_CONFIG['db'],
    max_connections=config.MYSQL_CONFIG['max_connections'],
    user=config.MYSQL_CONFIG['username'],
    password=config.MYSQL_CONFIG['password'],
    host=config.MYSQL_CONFIG['host'],
    port=config.MYSQL_CONFIG['port']
)


class Manager(BaseManager):
    async def get(self, source_, *args, **kwargs):
        """Get the model instance or ``None`` if not found.
        :param source_: model or base query for lookup

        Example::

            async def my_async_func():
                obj1 = await objects.get(MyModel, id=1)
                obj2 = await objects.get(MyModel, MyModel.id==1)
                obj3 = await objects.get(MyModel.select().where(MyModel.id==1))

        All will return `MyModel` instance with `id = 1`
        """
        await self.connect()

        if isinstance(source_, Query):
            query = source_
            model = query.model
        else:
            query = source_.select()
            model = source_

        conditions = list(args) + [(getattr(model, k) == v)
                                   for k, v in kwargs.items()]

        if conditions:
            query = query.where(*conditions)

        try:
            result = await self.execute(query)
            return list(result)[0]
        except IndexError:
            return None


class Raw(ModelRaw):
    def sql(self):
        sql, args = super(Raw, self).sql()
        return sql, None


class MySQLModel(Model):
    """MySQL BaseModel"""

    # async
    objects = Manager(mysql_db)

    DELETE_NO = 0
    DELETE_IS = 1

    DELETE_CHOICES = (
        (0, '未删除'),
        (1, '已删除'),
    )

    class Meta:
        database = mysql_db

    id = AutoField()
    create_time = DateTimeField(default=dt.now, verbose_name='创建时间')
    update_time = DateTimeField(default=dt.now, verbose_name='更新时间')
    is_delete = IntegerField(default=DELETE_NO, choices=DELETE_CHOICES, verbose_name='是否删除')

    @classmethod
    def _sql(cls, sql):
        """no escape !"""
        return Raw(cls, sql, None)

    @classmethod
    async def execute_sql_no_escape(cls, sql):
        """不要用, 只使用参数化查询"""
        return await cls.objects.execute(cls._sql(sql))

    @classmethod
    async def execute_sql(cls, sql, *params):
        """async execute sql"""
        return await cls.objects.execute(cls.raw(sql, *params))

    @classmethod
    async def async_execute(cls, query):
        """async execute sql"""
        return await cls.objects.execute(query)

    @classmethod
    async def async_get(cls, *args, **kwargs):
        return await cls.objects.get(cls, *args, **kwargs)

    @classmethod
    async def async_select(cls, *fields, where=None, order_by=None):
        """
        Simple select.
        :param fields:
        :param where: list or tuple
        :param order_by:
        :return:
        """
        query = cls.select(*fields)
        if where:
            query = query.where(*where)
        if order_by:
            query = query.order_by(order_by)
        return await cls.objects.execute(query)

    @classmethod
    async def async_count(cls, query, clear_limit=False):
        return await cls.objects.count(query, clear_limit)

    async def async_save(self):
        """暂时只做创建使用"""
        query = self.__class__.insert(**dict(self.__data__))

        pk = await self.async_execute(query)
        if self._pk is None:
            self._pk = pk
        return self

    @classmethod
    async def async_create(cls, **kwargs):
        """Create object
        :param kwargs:
        :return:
        """
        for field, value in kwargs.items():
            if not hasattr(cls, field):
                raise AttributeError("%s object has no attribute %s" % (cls.__name__, field))
        return await cls.objects.create(cls, **kwargs)

    async def async_update(self, **kwargs):
        """Update object
        :param kwargs:
        :return:
        """
        for field, value in kwargs.items():
            if hasattr(self, field):
                if getattr(self, field) != value:
                    setattr(self, field, value)
            else:
                raise AttributeError("%s object has no attribute %s" % (self.__class__.__name__, field))
        return await self.objects.update(self)

    async def async_delete(self):
        """Soft delete, `DELETE_NO` -> `DELETE_IS`
        :return:
        """
        self.is_delete = self.DELETE_IS
        return await self.objects.update(self)

    def normal_info(self):
        return {
            'id': self.id,
            'create_time': self.datetime_to_str(self.create_time),
            'update_time': self.datetime_to_str(self.update_time),
            'is_delete': self.is_delete,
        }

    def date_to_str(self, datetime):
        return dt.dt_to_str(datetime, "%Y-%m-%d")

    def datetime_to_str(self, datetime):
        return dt.dt_to_str(datetime)

    # Using transactions
    # Documents: https://peewee-async.readthedocs.io/en/latest/peewee_async/examples.html#using-both-sync-and-async-calls
    """
    async def test(self):
        import peewee_async
        obj = await self.objects.create(TestModel, text='FOO')
        obj_id = obj.id

        try:
            async with self.database.atomic_async():
                obj.text = 'BAR'
                await self.objects.update(obj)
                raise Exception('Fake error')
        except:
            res = await self.objects.get(TestModel, TestModel.id == obj_id)

        print(res.text)  # Should print 'FOO', not 'BAR'
    """
