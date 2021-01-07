# coding: utf-8
"""
@Author: Robby
@Module name: playbook.py
@Create date: 2020-12-27
@Function: 
"""


from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship

from utils.parse_file import SQLAlchemyBaseSingleton


Base = SQLAlchemyBaseSingleton._get_sqlalchemy_base()



# playbook任务表
class PlaybookTask(Base):
    __tablename__ = 'playbook_task'

    id = Column(String(160), primary_key=True, doc='任务id', comment='任务id')
    name = Column(String(160), nullable=False, doc='任务名称', comment='任务名称')
    playbook_content = Column(Text, nullable=False, doc='剧本内容', comment='剧本内容')
    playbook_name = Column(String(160), nullable=False, doc='剧本名称', comment='剧本名称')
    task_type = Column(String(160), nullable=False, doc='任务类型', comment='任务类型')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')
    modify_date = Column(DateTime, onupdate=datetime.now, doc='修改时间', comment='修改时间')

    __table_args__ = {'mysql_engine': 'InnoDB',
                      'mysql_collate': 'utf8mb4_general_ci',
                      'mysql_charset': 'utf8mb4', }


# playbook资产表
class PlaybookAsset(Base):
    __tablename__ = 'playbook_asset'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    ip = Column(String(160), nullable=False, doc='资产IP', comment='资产IP')
    task_id = Column(String(160), ForeignKey('playbook_task.id'), doc='外键playbook_task的id',comment='外键playbook_task的id')
    result_table = Column(String(160), doc='结果表名称', comment='结果表名称')  # 可以为空， 因为存储IP的时候，并不知道结果表名称, 只有执行的时候才知道结果表名称
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')
    modify_date = Column(DateTime, onupdate=datetime.now, doc='修改时间', comment='修改时间')
    playbook_task = relationship('PlaybookTask', backref='playbook_asset')

    __table_args__ = (
        Index('random_ip', 'ip'),
        {'mysql_engine': 'InnoDB',
         'mysql_collate': 'utf8mb4_general_ci',
         'mysql_charset': 'utf8mb4'}
    )


# playbook copy拷贝成功
class PlaybookCopySuccess(Base):
    __tablename__ = 'playbook_copy_success'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='ok', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_copy_success')


# copy拷贝失败
class PlaybookCopyFail(Base):
    __tablename__ = 'playbook_copy_fail'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='fail', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_copy_fail')


# shell执行成功
class PlaybookSHELLSuccess(Base):
    __tablename__ = 'playbook_shell_success'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='ok', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_shell_success')


# shell执行失败
class PlaybookSHELLFail(Base):
    __tablename__ = 'playbook_shell_fail'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='fail', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_shell_fail')


# unarchives执行成功
class PlaybookUNARCHIVESuccess(Base):
    __tablename__ = 'playbook_unarchive_success'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='ok', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_unarchive_success')


# unarchives执行失败
class PlaybookUNARCHIVEFail(Base):
    __tablename__ = 'playbook_unarchive_fail'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='ok', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_unarchive_fail')


# 无法连接
class PlaybookUNREACHABLE(Base):
    __tablename__ = 'playbook_unreachable'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='unreachable', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_unreachable')


# 执行任务超时
class PlaybookExecTimeout(Base):
    __tablename__ = 'playbook_exec_timeout'
    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('playbook_asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    result = Column(String(160), default='timeout', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    playbook_asset = relationship('PlaybookAsset', backref='playbook_exec_timeout')