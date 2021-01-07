# coding: utf-8
"""
@Author: Robby
@Module name: parse_file.py
@Create date: 2020-10-28
@Function: 全局单例
"""
import socket
from configparser import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from kafka import KafkaProducer, KafkaConsumer
from sqlalchemy.ext.declarative import declarative_base

from utils.const_file import SERVER_CONFIG, SQL_INFO_LOG, SQL_ERROR_LOG
from utils.encrypt_decrypt import decrypt

from utils.global_logger import getlogger

class SingletonBase:

    __parser = None

    @classmethod
    def _get_parser(cls):
        if cls.__parser == None:
            cls.__parser = ConfigParser()
            cls.__parser.read(SERVER_CONFIG)
        return cls.__parser

# Gitlab配置
class GitlabConfigSingleton(SingletonBase):
    __gitlab_config_info = None

    @classmethod
    def _get_gitlab_config_info(cls):
        if cls.__gitlab_config_info == None:
            parser = cls._get_parser()
            gitlab_ip = parser.get('Gitlab', 'IP')
            gitlab_group = parser.get('Gitlab', 'GROUP')

            cls.__gitlab_config_info = gitlab_ip, gitlab_group

        return cls.__gitlab_config_info

# MySQL配置
class MySQLConfigSingleton(SingletonBase):
    __mysql_config_info = None

    @classmethod
    def _get_mysql_config_info(cls):
        if cls.__mysql_config_info == None:
            parser = cls._get_parser()
            mysql_ip = parser.get('MySQL', 'IP')
            mysql_port = parser.get('MySQL', 'PORT')
            mysql_database = parser.get('MySQL', 'DATABASE')
            mysql_user = parser.get('MySQL', 'USER')
            mysql_password = parser.get('MySQL', 'PASSWORD')

            cls.__mysql_config_info = mysql_ip, int(mysql_port), mysql_database, mysql_user, decrypt(mysql_password)

        return cls.__mysql_config_info

# 执行引擎配置
class ExecEngineSingleton(SingletonBase):
    __exec_number = None

    # 获取单台执行引擎最多执行的主机数
    @classmethod
    def _get_exec_number(cls):
        if cls.__exec_number == None:
            parser = cls._get_parser()
            exec_number = int(parser.get('Exec_Engine', 'NUMBER'))
            cls.__exec_number = exec_number
        return cls.__exec_number

# 数据库engine单例
class MySQLEngineSingleton:
    __engine = None

    @classmethod
    def _get_mysql_engine(cls):
        if cls.__engine == None:
            mysql_ip, mysql_port, mysql_database, mysql_user, mysql_password = MySQLConfigSingleton._get_mysql_config_info()
            engine = create_engine('mysql+pymysql://{user}:{password}@{mysql_ip}:{port}/{database}?charset=utf8mb4'
                                   .format(user=mysql_user, password=mysql_password, mysql_ip=mysql_ip, port=mysql_port, database=mysql_database),
                                    echo=False,
                                    pool_size=10,
                                    pool_recycle=10,
                                    encoding='utf-8',
                                    max_overflow=1000)

            # 配置日志
            getlogger('sqlalchemy.engine', SQL_INFO_LOG, SQL_ERROR_LOG)
            cls.__engine = engine
        return cls.__engine

# 数据库session会话
class MySQLSessionSingleton:
    __Session = None

    @classmethod
    def _get_mysql_session(cls):
        if cls.__Session == None:

            from distribute.models import adhoc
            from distribute.models import playbook
            Base = SQLAlchemyBaseSingleton._get_sqlalchemy_base()
            engine = MySQLEngineSingleton._get_mysql_engine()
            Base.metadata.create_all(engine)
            cls.__Session = sessionmaker(bind=engine)

        session = cls.__Session()
        return session





# kafka配置
class KafkaConfigSingleton:
    __parser = None
    __kafka_config_info = None

    @classmethod
    def __get_parser(cls):
        if cls.__parser == None:
            cls.__parser = ConfigParser()
            cls.__parser.read(SERVER_CONFIG)
        return cls.__parser

    @classmethod
    def _get_kafka_config_info(cls):
        if cls.__kafka_config_info == None:
            parser = cls.__get_parser()
            kafka_bootstrap_servers = parser.get('Kafka_Cluster', 'BOOTSTRAP_SERVERS')
            kafka_group_id = parser.get('Kafka_Cluster', 'GROUP_ID')
            kafka_auto_offset_reset = parser.get('Kafka_Cluster', 'AUTO_OFFSET_RESET')
            kafka_topic = parser.get('Kafka_Cluster', 'TOPIC')

            cls.__kafka_config_info = kafka_bootstrap_servers, kafka_group_id, kafka_auto_offset_reset, kafka_topic

        return cls.__kafka_config_info

# 消费者和生产者
class KafkaProducerConsumerSingleton:
    __kafka_bootstrap_servers_str = None
    __kafka_group_id = None
    __kafka_auto_offset_reset = None
    __kafka_topic = None
    __kafka_consumer = None
    __kafka_producer = None

    @classmethod
    def _get_kafka_config_info(cls, role):
        if cls.__kafka_bootstrap_servers_str == None:
            cls.__kafka_bootstrap_servers_str, cls.__kafka_group_id, cls.__kafka_auto_offset_reset, cls.__kafka_topic = KafkaConfigSingleton._get_kafka_config_info()

        if not role == 'consumer':
            return cls.__kafka_bootstrap_servers_str
        return cls.__kafka_bootstrap_servers_str, cls.__kafka_group_id, cls.__kafka_auto_offset_reset, cls.__kafka_topic


    @classmethod
    def _get_producer(cls):
        if cls.__kafka_producer == None:
            kafka_bootstrap_servers_str = cls._get_kafka_config_info('producer')
            kafka_bootstrap_servers = kafka_bootstrap_servers_str.split(',')
            cls.__kafka_producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers,
                                                 retries=5)
        return cls.__kafka_producer

    @classmethod
    def _get_consumer(cls):
        if cls.__kafka_consumer == None:
            kafka_bootstrap_servers_str, kafka_group_id, kafka_auto_offset_reset, kafka_topic = cls._get_kafka_config_info('consumer')
            kafka_bootstrap_servers = kafka_bootstrap_servers_str.split(',')
            cls.__kafka_consumer = KafkaConsumer(kafka_topic,
                                                 client_id=socket.gethostname(),
                                                 group_id=kafka_group_id,
                                                 auto_offset_reset=kafka_auto_offset_reset,
                                                 bootstrap_servers=kafka_bootstrap_servers,
                                                 enable_auto_commit=False)
        return cls.__kafka_consumer


# 数据表绑定的Base单例
class SQLAlchemyBaseSingleton:
    __Base = None

    @classmethod
    def _get_sqlalchemy_base(cls):
        if cls.__Base == None:
            cls.__Base = declarative_base()
        return cls.__Base

if __name__ == '__main__':
    print(MySQLConfigSingleton._get_mysql_config_info())
    print(MySQLEngineSingleton._get_mysql_engine())
    print(MySQLSessionSingleton._get_mysql_session())
    print(ExecEngineSingleton._get_exec_number())
    print(GitlabConfigSingleton._get_gitlab_config_info())
