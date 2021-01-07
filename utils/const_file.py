# coding: utf-8
"""
@Author: Robby
@Module name:
@Create date: 2020-11-17
@Function:
"""
import os


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
CONF_DIR = os.path.join(PROJECT_DIR, 'conf')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

DISTRIBUTE_INFO_LOG = os.path.join(LOG_DIR, 'fil_distribute_info.log')
DISTRIBUTE_ERROR_LOG = os.path.join(LOG_DIR, 'fil_distribute_error.log')
TASK_VIEW_INFO_LOG = os.path.join(LOG_DIR, 'task_view_info.log')
TASK_VIEW_ERROR_LOG = os.path.join(LOG_DIR, 'task_view_error.log')
FILE_INFO_LOG = os.path.join(LOG_DIR, 'file_info.log')
FILE_ERROR_LOG = os.path.join(LOG_DIR, 'file_error.log')
SQL_INFO_LOG = os.path.join(LOG_DIR, 'sql_info.log')
SQL_ERROR_LOG = os.path.join(LOG_DIR, 'sql_error.log')
PRODUCER_INFO_LOG = os.path.join(LOG_DIR, 'producer_info.log')
PRODUCER_ERROR_LOG = os.path.join(LOG_DIR, 'producer_error.log')

SERVER_CONFIG = os.path.join(CONF_DIR, 'server.conf')

FILES_DIR = os.path.join(DATA_DIR, 'files')


if __name__ == '__main__':
    print(PROJECT_DIR)
    print(LOG_DIR)
    print(CONF_DIR)
    print(DATA_DIR)

    print(DISTRIBUTE_INFO_LOG)
    print(DISTRIBUTE_ERROR_LOG)
    print(TASK_VIEW_INFO_LOG)
    print(TASK_VIEW_ERROR_LOG)
    print(FILE_INFO_LOG)
    print(FILE_ERROR_LOG)