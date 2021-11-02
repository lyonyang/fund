#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
Peewee Document : http://docs.peewee-orm.com/en/latest/
Peewee-async Document : https://peewee-async.readthedocs.io/en/latest/index.html

Using transactions
Documents: https://peewee-async.readthedocs.io/en/latest/peewee_async/examples.html#using-both-sync-and-async-calls

with sync_db.atomic() as tran:
    pass

with async_db.atomic_async() as tran:
    pass
"""

import operator
from lib.dt import dt
from base import config
from peewee import reduce
from peewee_async import Manager, PooledMySQLDatabase, AsyncQueryWrapper
from peewee import Model, AutoField, DateTimeField, IntegerField, Query
from playhouse.pool import PooledMySQLDatabase as SyncPooledMySQLDatabase

# Connect to a MySQL database on network.
async_db = PooledMySQLDatabase(
    config.MYSQL_CONFIG['db'],
    max_connections=config.MYSQL_CONFIG['max_connections'],
    user=config.MYSQL_CONFIG['username'],
    password=config.MYSQL_CONFIG['password'],
    host=config.MYSQL_CONFIG['host'],
    port=config.MYSQL_CONFIG['port']
)

sync_db = SyncPooledMySQLDatabase(
    config.MYSQL_CONFIG['db'],
    max_connections=config.MYSQL_CONFIG['max_connections'],
    user=config.MYSQL_CONFIG['username'],
    password=config.MYSQL_CONFIG['password'],
    host=config.MYSQL_CONFIG['host'],
    port=config.MYSQL_CONFIG['port']
)


class Func:
    def __init__(self, value, opt, **kwargs):
        self.val = value
        self.opt = opt
        self.kwargs = kwargs

    @classmethod
    def like(cls, value) -> "Func":
        return cls(value, '%')

    @classmethod
    def in_(cls, value) -> "Func":
        return cls(value, 'in')

    @classmethod
    def eq(cls, value) -> "Func":
        return cls(value, '=')

    @classmethod
    def ne(cls, value) -> "Func":
        return cls(value, '!=')

    @classmethod
    def notin(cls, value) -> "Func":
        return cls(value, 'ni')

    @classmethod
    def gt(cls, value) -> "Func":
        return cls(value, '>')

    @classmethod
    def gte(cls, value):
        return cls(value, '>=')

    @classmethod
    def lt(cls, value) -> "Func":
        return cls(value, '<')

    @classmethod
    def lte(cls, value) -> "Func":
        return cls(value, '<=')

    @classmethod
    def or_(cls, **kwargs) -> "Func":
        """
        phone_or_name=Func.or_(phone=130, name='Lyon')
        """
        return cls(kwargs, '|')

    @classmethod
    def and_(cls, **kwargs) -> "Func":
        """
        phone_and_name=Func.and_(phone=130, name='Lyon')
        """
        return cls(kwargs, '&')

    @classmethod
    def is_null(cls, **kwargs) -> "Func":
        return cls(kwargs, 'is')

    @classmethod
    def not_null(cls, **kwargs) -> "Func":
        return cls(kwargs, 'si')


class BaseModel(Model):
    # async
    objects = Manager(async_db)

    DELETE_NO = 0
    DELETE_IS = 1

    DELETE_CHOICES = (
        (0, '未删除'),
        (1, '已删除'),
    )

    class Meta:
        database = sync_db

    create_time = DateTimeField(default=dt.now, verbose_name='创建时间')
    update_time = DateTimeField(default=dt.now, verbose_name='更新时间')
    is_delete = IntegerField(default=DELETE_NO, choices=DELETE_CHOICES, verbose_name='是否删除')

    @classmethod
    def get_sql(cls, *fields, order_by=None, paginate=None, **where):
        return cls._get_query(*fields, order_by=order_by, paginate=paginate, **where)

    # Async
    @classmethod
    async def async_sql(cls, sql, *params) -> AsyncQueryWrapper:
        """async execute sql
        """
        return await cls.objects.execute(cls.raw(sql, *params))

    @classmethod
    async def async_execute(cls, query):
        return await cls.objects.execute(query)

    @classmethod
    async def async_execute_count(cls, query):
        return await cls.objects.count(query)

    @classmethod
    async def async_get(cls, *fields, order_by=None, paginate=None, **where) -> Model or None:
        query = cls._get_query(*fields, order_by=order_by, paginate=paginate, **where)
        try:
            result = await cls.objects.execute(query)
            return list(result)[0]
        except IndexError:
            return None

    @classmethod
    async def async_select(cls, *fields, order_by=None, paginate=None, **where) -> AsyncQueryWrapper:
        """
        Simple select
        :param fields: 需要获取的字段
        :param order_by: 排序
        :param paginate: 分页 Demo: (0, 10)
        :param where: 条件 关键字条件
        """
        query = cls._get_query(*fields, order_by=order_by, paginate=paginate, **where)
        return await cls.objects.execute(query)

    @classmethod
    async def async_count(cls, *fields, clear_limit=False, **where) -> int:
        query = cls._get_query(*fields, **where)
        return await cls.objects.count(query, clear_limit)

    @classmethod
    async def async_create(cls, **kwargs) -> Model:
        """Create object
        """
        for field, value in kwargs.items():
            if not hasattr(cls, field):
                raise AttributeError("%s object has no attribute %s" % (cls.__name__, field))
        return await cls.objects.create(cls, **kwargs)

    async def async_update(self, _only=True, **kwargs) -> Model:
        """Update object, only kwargs
        """
        self.update_time = dt.now()
        update_fields = ['update_time']
        for field, value in kwargs.items():
            if hasattr(self, field):
                if getattr(self, field) != value:
                    setattr(self, field, value)
            else:
                raise AttributeError("%s object has no attribute %s" % (self.__class__.__name__, field))
            update_fields.append(field)
        if _only:
            _only = update_fields
        else:
            _only = None

        await self.objects.update(self, only=_only)
        return self

    async def async_delete(self) -> Model:
        """Soft delete, `DELETE_NO` -> `DELETE_IS`
        """
        await self.async_update(is_delete=self.DELETE_IS)
        return self

    # Sync
    @classmethod
    def sync_sql(cls, sql, *params):
        return sync_db.execute_sql(sql, params)

    @classmethod
    def sync_get(cls, *fields, order_by=None, paginate=None, **where) -> Model or None:
        query = cls._get_query(*fields, order_by=order_by, paginate=paginate, **where)
        try:
            result = query.limit(1)
            return list(result)[0]
        except Exception:
            return None

    @classmethod
    def sync_select(cls, *fields, order_by=None, paginate=None, **where):
        """
        Simple select
        :param fields: 需要获取的字段
        :param order_by: 排序
        :param paginate: 分页 Demo: (0, 10)
        :param where: 条件 关键字条件
        """
        query = cls._get_query(*fields, order_by=order_by, paginate=paginate, **where)
        return query

    @classmethod
    def sync_count(cls, *fields, clear_limit=False, **where) -> int:
        query = cls._get_query(*fields, **where)
        return query.count(clear_limit)

    @classmethod
    def sync_create(cls, **kwargs) -> Model:
        return cls(**kwargs).save(force_insert=True)

    def sync_update(self, _only=True, **kwargs) -> Model:
        """Update object, only kwargs
        """
        self.update_time = dt.now()
        update_fields = ['update_time']
        for field, value in kwargs.items():
            if hasattr(self, field):
                if getattr(self, field) != value:
                    setattr(self, field, value)
            else:
                raise AttributeError("%s object has no attribute %s" % (self.__class__.__name__, field))
            update_fields.append(field)
        if _only:
            _only = update_fields
        else:
            _only = None
        self.save(only=_only)
        return self

    def sync_delete(self) -> Model:
        """Soft delete, `DELETE_NO` -> `DELETE_IS`
        """
        self.sync_update(is_delete=self.DELETE_IS)
        return self

    def dt_to_str(self, datetime, format="%Y-%m-%d %H:%M:%S"):
        return dt.dt_to_str(datetime, format)

    @classmethod
    def get_or_expression(cls, kwargs):
        return reduce(operator.or_, (cls.get_expression(field, value) for field, value in kwargs.items()))

    @classmethod
    def get_and_expression(cls, kwargs):
        return reduce(operator.and_, (cls.get_expression(field, value) for field, value in kwargs.items()))

    @classmethod
    def get_expression(cls, field, value):
        field = getattr(cls, field, None)
        if isinstance(value, Func):
            if value.opt == '%':
                return field ** value.val
            elif value.opt == 'in':
                return field.in_(value.val)
            elif value.opt == 'ni':
                return field.not_in(value.val)
            elif value.opt == '>':
                return field > value.val
            elif value.opt == '<':
                return field < value.val
            elif value.opt == '>=':
                return field >= value.val
            elif value.opt == '<=':
                return field <= value.val
            elif value.opt == 'is':
                return field.is_null()
            elif value.opt == 'si':
                return field.is_null(False)
            elif value.opt == '=':
                return field == value.val
            elif value.opt == '!=':
                return field != value.val
            elif value.opt == '|':
                return cls.get_or_expression(value.val)
            elif value.opt == '&':
                return cls.get_and_expression(value.val)
            else:
                raise AttributeError("Func has no operator %s" % value.opt)
        else:
            return field == value

    @classmethod
    def _get_query(cls, *fields, order_by=None, paginate=None, **where) -> Query:
        query = cls.select(*fields)
        expressions = []
        if where:
            for field, value in where.items():
                if hasattr(cls, field):
                    if isinstance(value, (list, tuple)):
                        for val in value:
                            expressions.append(cls.get_expression(field, val))
                    else:
                        expressions.append(cls.get_expression(field, value))
                else:
                    if isinstance(value, Func) and (value.opt == '&' or value.opt == '|'):
                        expressions.append(cls.get_expression(field, value))
                    else:
                        raise AttributeError("%s Model has no field %s" % (cls.__name__, field))

            query = query.where(*expressions)
        if order_by:
            if isinstance(order_by, (list, tuple)):
                query = query.order_by(*order_by)
            else:
                query = query.order_by(order_by)
        if paginate:
            page, paginate_by = paginate
            query = query.paginate(page, paginate_by)
        return query

    async def normal_info(self):
        return {
            'create_time': self.dt_to_str(self.create_time),
            'update_time': self.dt_to_str(self.update_time),
            'is_delete': self.is_delete,
        }


class MySQLModel(BaseModel):
    """MySQL BaseModel"""

    id = AutoField()

    async def normal_info(self):
        return {
            'id': self.id,
            'create_time': self.dt_to_str(self.create_time),
            'update_time': self.dt_to_str(self.update_time),
            'is_delete': self.is_delete,
        }
