#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = Lyon

"""
数据库模型迁移

http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#schema-migrations

migrate(
    migrator.add_column('comment_tbl', 'pub_date', pubdate_field),
    migrator.rename_column('story', 'pub_date', 'publish_date'),
    migrator.drop_column('story', 'some_old_field'),
    migrator.alter_column_type('person', 'email', TextField())
    migrator.rename_table('story', 'stories_tbl'),
    migrate(migrator.drop_constraint('products', 'price_check'))
    migrate(migrator.add_unique('person', 'first_name', 'last_name'))
)
"""

from base import make_app

app = make_app('dev')

from base.db.mysql import mysql_db as db
from playhouse.migrate import MySQLMigrator, migrate
from apps.users.user import FundUser
from apps.users.trade import TradeRecord
from apps.users.fund import FundOptionalRecord

migrator = MySQLMigrator(db)


def migrate_table():
    # 新增字段

    migrate(
        # migrator.add_column('trade_record', 'fund_name', TradeRecord.fund_name),
        migrator.add_column('trade_record', 'copies', TradeRecord.copies),
    )


def create_table():
    db.connect()
    # 创建表
    db.create_tables([
        FundUser,
        TradeRecord,
        FundOptionalRecord
    ])


if __name__ == '__main__':
    # migrate_table()
    create_table()
