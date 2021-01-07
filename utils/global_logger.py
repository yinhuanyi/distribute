# coding: utf-8
"""
@Author: Robby
@Module name:
@Create date: 2020-11-17
@Function: 
"""

import logging
from logging import handlers

logging.basicConfig(format='%(asctime)s  %(message)s ', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

class SingleLogger:
    __logger_map = {}

    @classmethod
    def getLoggerInstance(cls, logger_name, info_file_path, error_file_path):
        # 如果没有这个logger实例，那么直接创建即可
        if cls.__logger_map.get(logger_name) == None:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            logger.propagate = False

            info_handler = handlers.TimedRotatingFileHandler(info_file_path, when='midnight', interval=1, backupCount=100, encoding='utf-8')
            info_handler.setLevel(level=logging.INFO)
            info_handler.setFormatter(fmt=logging.Formatter(fmt='%(asctime)s %(levelname)s %(lineno)d %(module)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            info_handler.suffix = '%Y-%m-%d'

            error_handler = handlers.TimedRotatingFileHandler(error_file_path, when='midnight', interval=1, backupCount=100, encoding='utf-8')
            error_handler.setLevel(level=logging.ERROR)
            error_handler.setFormatter(fmt=logging.Formatter(fmt='%(asctime)s %(levelname)s %(lineno)d %(module)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            error_handler.suffix = '%Y-%m-%d'
            logger.addHandler(info_handler)
            logger.addHandler(error_handler)
            cls.__logger_map[logger_name] = logger
        return cls.__logger_map.get(logger_name)


def getlogger(logger_name: str, info_file_path: str, error_file_path: str):
    return SingleLogger.getLoggerInstance(logger_name, info_file_path, error_file_path)



if __name__ == '__main__':
    from utils.const_file import AGENT_INFO_LOG, AGENT_ERROR_LOG
    import time

    while True:
        agent_logger = getlogger('Agent', AGENT_INFO_LOG, AGENT_ERROR_LOG)
        agent_logger.info('这是测试info log')
        agent_logger.error('这是测试的 errorlogging')
        time.sleep(1)