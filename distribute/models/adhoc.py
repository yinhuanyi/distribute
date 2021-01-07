from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship, backref

from utils.parse_file import SQLAlchemyBaseSingleton


Base = SQLAlchemyBaseSingleton._get_sqlalchemy_base()

# 任务表
class Task(Base):
    __tablename__ = 'task'

    id = Column(String(160), primary_key=True, doc='任务id', comment='任务id')
    name = Column(Text, nullable=False, doc='任务名称', comment='任务名称')
    module = Column(String(160), nullable=False, doc='模块名称', comment='模块名称')
    args = Column(String(160), nullable=False, doc='模块名称', comment='模块名称')
    task_type = Column(String(160), nullable=False, doc='任务类型', comment='任务类型')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')
    modify_date = Column(DateTime, onupdate=datetime.now, doc='修改时间', comment='修改时间')

    __table_args__ = {'mysql_engine': 'InnoDB',
                      'mysql_collate': 'utf8mb4_general_ci',
                      'mysql_charset': 'utf8mb4', }


# 资产表
class Asset(Base):
    __tablename__ = 'asset'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    ip = Column(String(160), nullable=False, doc='资产IP', comment='资产IP')
    task_id = Column(String(160), ForeignKey('task.id'), doc='外键Task的id', comment='外键Task的id')
    result_table = Column(String(160), doc='结果表名称', comment='结果表名称')  # 可以为空， 因为存储IP的时候，并不知道结果表名称, 只有执行的时候才知道结果表名称
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')
    modify_date = Column(DateTime, onupdate=datetime.now, doc='修改时间', comment='修改时间')
    # 用于外键的正向和反向查询
    task = relationship('Task', backref='asset')

    __table_args__ = (
        Index('random_ip', 'ip'),
        {'mysql_engine': 'InnoDB',
         'mysql_collate': 'utf8mb4_general_ci',
         'mysql_charset': 'utf8mb4'}
    )


# copy拷贝成功
class CopySuccess(Base):
    __tablename__ = 'copy_success'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    # path = Column(Text, doc='文件路径', comment='文件路径')
    # changed = Column(String(160), doc='文件是否改变', comment='文件是否改变')
    # uid = Column(String(160), doc='文件UID', comment='文件UID')
    # gid = Column(String(160), doc='文件GID', comment='文件GID')
    # owner = Column(String(160), doc='文件属主', comment='文件属主')
    # group = Column(String(160), doc='文件属组', comment='文件属组')
    # mode = Column(String(160), doc='文件权限', comment='文件权限')
    # state = Column(String(160), doc='文件状态', comment='文件状态')
    # size = Column(String(160), doc='文件大小', comment='文件大小')
    dest = Column(String(160), doc='目标地址', comment='目标地址')
    result = Column(String(160), default='拷贝成功', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='copy_success')


# copy拷贝失败
class CopyFail(Base):
    __tablename__ = 'copy_fail'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    msg = Column(Text, doc='执行信息', comment='执行信息')
    exception = Column(Text, doc='异常消息', comment='异常消息')
    # changed = Column(String(160), doc='文件是否改变', comment='文件是否改变')
    result = Column(String(160), default='拷贝失败', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='copy_fail')


# shell执行成功
class SHELLSuccess(Base):
    __tablename__ = 'shell_success'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    cmd = Column(Text, doc='执行命令', comment='执行命令')
    stdout = Column(Text, doc='标准输出', comment='标准输出')
    # stderr = Column(Text, doc='错误输出', comment='错误输出')
    # rc = Column(String(160), doc='返回状态码', comment='返回状态码')
    # start_time = Column(String(160), doc='执行开始时间', comment='执行开始时间')
    # end_time = Column(String(160), doc='执行结束时间', comment='执行结束时间')
    # delta_time = Column(String(160), doc='执行时间间隔', comment='执行时间间隔')
    # changed = Column(String(160), doc='系统状态是否改变', comment='系统状态是否改变')
    result = Column(String(160), default='执行成功', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='shell_success')


# shell执行失败
class SHELLFail(Base):
    __tablename__ = 'shell_fail'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    msg = Column(Text, doc='失败原因', comment='失败原因')
    cmd = Column(Text, doc='执行命令', comment='执行命令')
    # stdout = Column(Text, doc='标准输出', comment='标准输出')
    stderr = Column(Text, doc='错误输出', comment='错误输出')
    # rc = Column(String(160), doc='返回状态码', comment='返回状态码')
    # start_time = Column(String(160), doc='执行开始时间', comment='执行开始时间')
    # end_time = Column(String(160), doc='执行结束时间', comment='执行结束时间')
    # delta_time = Column(String(160), doc='执行时间间隔', comment='执行时间间隔')
    # changed = Column(String(160), doc='系统状态是否改变', comment='系统状态是否改变')
    result = Column(String(160), default='执行失败', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='shell_fail')


# unarchives执行成功
class UNARCHIVESuccess(Base):
    __tablename__ = 'unarchive_success'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    dest = Column(Text, doc='目标地址', comment='目标地址')
    # src = Column(Text, doc='源地址', comment='源地址')
    # changed = Column(String(160), doc='文件是否改变', comment='文件是否改变')
    # uid = Column(String(160), doc='文件UID', comment='文件UID')
    # gid = Column(String(160), doc='文件GID', comment='文件GID')
    # owner = Column(String(160), doc='文件属主', comment='文件属主')
    # group = Column(String(160), doc='文件属组', comment='文件属组')
    # state = Column(String(160), doc='文件状态', comment='文件状态')
    # size = Column(String(160), doc='文件大小', comment='文件大小')
    result = Column(String(160), default='解压成功', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='unarchive_success')


# unarchives执行失败
class UNARCHIVEFail(Base):
    __tablename__ = 'unarchive_fail'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    msg = Column(Text, doc='解压信息', comment='解压信息')
    # changed = Column(String(160), doc='是否改变', comment='是否改变')
    result = Column(String(160), default='解压失败', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='unarchive_fail')


# 无法连接
class UNREACHABLE(Base):
    __tablename__ = 'unreachable'

    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    # unreachable = Column(String(160), doc='是否无法连接', comment='是否无法连接')
    msg = Column(Text, doc='执行信息', comment='执行信息')
    # changed = Column(String(160), doc='是否改变', comment='是否改变')
    result = Column(String(160), default='无法连接', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='unreachable')


# 执行任务超时
class ExecTimeout(Base):
    __tablename__ = 'exec_timeout'
    id = Column(Integer, primary_key=True, doc='主键id', comment='主键id')
    asset_id = Column(Integer, ForeignKey('asset.id'), doc='外键Asset的id', comment='外键Asset的id')
    module = Column(String(160), doc='模块', comment='模块')
    args = Column(String(160), doc='参数', comment='参数')
    msg = Column(Text, doc='超时日志', comment='超时日志')
    result = Column(String(160), default='执行超时', doc='结果名称', comment='结果名称')
    created_date = Column(DateTime, default=datetime.now, doc='创建时间', comment='创建时间')

    asset = relationship('Asset', backref='exec_timeout')
