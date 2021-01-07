import json
import math
import os
import subprocess

from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

from utils.parse_file import ExecEngineSingleton, GitlabConfigSingleton
from utils.producer import send_message
from utils.global_logger import getlogger
from utils.const_file import TASK_VIEW_INFO_LOG, TASK_VIEW_ERROR_LOG, SQL_INFO_LOG, SQL_ERROR_LOG
from utils.parse_file import MySQLSessionSingleton
from distribute import models
from distribute.models.adhoc import Task, Asset
from distribute.models.playbook import PlaybookTask, PlaybookAsset
from .forms.playbook import PlaybookCreateForm, PlaybookListForm
from utils.const_file import FILES_DIR



task_view_logger = getlogger(logger_name='task_view', info_file_path=TASK_VIEW_INFO_LOG, error_file_path=TASK_VIEW_ERROR_LOG)
sql_logger = getlogger(logger_name='sql', info_file_path=SQL_INFO_LOG, error_file_path=SQL_ERROR_LOG)


# adhoc下发和查询
class AdhocView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # 写入task和ip到数据库
    def __sync_task_ip_into_database(self, *args, **kwargs):
        ip_list = kwargs.get('ip_list')
        task_id = kwargs.get('task_id')
        task_name = kwargs.get('task_name')
        module = kwargs.get('module')
        args = kwargs.get('args')
        task_type = kwargs.get('task_type')

        session = MySQLSessionSingleton._get_mysql_session()

        try:

            session.add(Task(id=task_id, name=task_name, module=module, args=args, task_type=task_type))
            session.commit()
            asset_list = []
            for ip in ip_list:
                asset_list.append(Asset(ip=ip, task_id=task_id))
            # session.add(asset_list)
            # session.add_all(asset_list)
            session.bulk_save_objects(asset_list)
            session.commit()
        except Exception as e:
            task_view_logger.error('Sync task and ip to database Error: {}'.format(e))
            session.rollback()
            raise Exception('Sync task and ip to database Error')
        finally:
            session.close()

    # 消息剔除ip字段
    def __get_noip_data(self, data: dict):
        data.pop('ips')
        return data

    # 下发任务指令集
    def post(self, request):
        json_data = request.body.decode('utf-8')
        dict_data = json.loads(json_data)
        ips = dict_data.get('ips').strip(',').replace(' ', '')
        task_id = dict_data.get('task_id')
        task_name = dict_data.get('task_name')
        ip_list = ips.split(',')
        module = dict_data.get('module')
        args = dict_data.get('args')
        task_type = dict_data.get('type')

        try:
            self.__sync_task_ip_into_database(ip_list=ip_list,
                                              task_id=task_id,
                                              task_name=task_name,
                                              module=module,
                                              args=args,
                                              task_type=task_type)

        except Exception:
            return JsonResponse(data={'code': 500, 'data': None, 'msg': '任务和资产写入错误'})

        exec_number = ExecEngineSingleton._get_exec_number()
        ret = len(ip_list) / exec_number
        ret = math.ceil(ret)
        try:
            if ret == 1:
                dict_data["ip"] = dict_data.pop("ips")
                send_message(dict_data)

            else:
                noip_data = self.__get_noip_data(dict_data)
                for i in range(ret):
                    ceil = exec_number * i
                    tail = exec_number * (i + 1)
                    sub_ip_list = ip_list[ceil:tail]
                    sub_ip_str = ','.join(sub_ip_list)
                    noip_data['ip'] = sub_ip_str
                    send_message(noip_data)

        except Exception as e:
            task_view_logger.error('Send Message to Kafka Error: {}'.format(e))
            return JsonResponse(data={'code': 500, 'data': None, 'msg': 'Kafka指令集下发错误'})
        return JsonResponse(data={'code': 200, 'data': None, 'msg': '任务下发成功'})

    # 基于任务id，获取任务
    def get(self, request):
        task_id = request.GET.get('task_id')
        ip = request.GET.get('ip').strip(',').replace(' ', '') if request.GET.get('ip') else request.GET.get('ip')
        ips = request.GET.get('ips').strip(',').replace(' ', '') if request.GET.get('ips') else request.GET.get('ips')

        # 分情况讨论
        ############
        # 1：如果是task_id，那么只返回最后一行任务
        # 2：如果是IP
        #           ①：如果是单个IP，返回所有任务列表
        #           ②：如果是IP列表，返回最后10条任务列表
        ############

        session = MySQLSessionSingleton._get_mysql_session()
        result = []

        # TODO: 获取IP最后一条结果
        if task_id and not ip and not ips:

            try:
                task_instance = session.query(Task).filter_by(id=task_id).first()
                task_name = task_instance.name
                module = task_instance.module
                args = task_instance.args

                if task_instance:
                    tables = session.query(Asset.result_table).filter_by(task_id=task_id).group_by(Asset.result_table).all()
                    id_ip_list = session.query(Asset.id, Asset.ip).filter_by(task_id=task_id).all()
                    id_list = [item[0] for item in id_ip_list]

                    for table in tables:

                        if table[0] == models.adhoc.CopySuccess.__tablename__:
                            copy_success_result_instances = session.query(models.adhoc.CopySuccess).filter(models.adhoc.CopySuccess.asset_id.in_(id_list)).all()

                            for copy_success_result_instance in copy_success_result_instances:
                                item = {}
                                item['result'] = copy_success_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = copy_success_result_instance.id
                                item['asset_id'] = copy_success_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['dest'] = copy_success_result_instance.dest
                                item['created_date'] = copy_success_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")

                                result.append(item)

                        elif table[0] == models.adhoc.CopyFail.__tablename__:
                            copy_fail_result_instances = session.query(models.adhoc.CopyFail).filter(models.adhoc.CopyFail.asset_id.in_(id_list)).all()

                            for copy_fail_result_instance in copy_fail_result_instances:
                                item = {}
                                item['result'] = copy_fail_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = copy_fail_result_instance.id
                                item['asset_id'] = copy_fail_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['msg'] = copy_fail_result_instance.msg
                                item['exception'] = copy_fail_result_instance.exception
                                item['created_date'] = copy_fail_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                        elif table[0] == models.adhoc.SHELLSuccess.__tablename__:
                            shell_success_result_instances = session.query(models.adhoc.SHELLSuccess).filter(models.adhoc.SHELLSuccess.asset_id.in_(id_list)).all()

                            for shell_success_result_instance in shell_success_result_instances:
                                item = {}
                                item['result'] = shell_success_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = shell_success_result_instance.id
                                item['asset_id'] = shell_success_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['cmd'] = shell_success_result_instance.cmd
                                item['stdout'] = shell_success_result_instance.stdout
                                item['created_date'] = shell_success_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                        elif table[0] == models.adhoc.SHELLFail.__tablename__:
                            shell_fail_result_instances = session.query(models.adhoc.SHELLFail).filter(models.adhoc.SHELLFail.asset_id.in_(id_list)).all()

                            for shell_fail_result_instance in shell_fail_result_instances:
                                item = {}
                                item['result'] = shell_fail_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = shell_fail_result_instance.id
                                item['asset_id'] = shell_fail_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['msg'] = shell_fail_result_instance.msg
                                item['stderr'] = shell_fail_result_instance.stderr
                                item['created_date'] = shell_fail_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                        elif table[0] == models.adhoc.UNARCHIVESuccess.__tablename__:
                            unarchive_success_result_instances = session.query(models.adhoc.UNARCHIVESuccess).filter(models.adhoc.UNARCHIVESuccess.asset_id.in_(id_list)).all()

                            for unarchive_success_result_instance in unarchive_success_result_instances:
                                item = {}
                                item['result'] = unarchive_success_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = unarchive_success_result_instance.id
                                item['asset_id'] = unarchive_success_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['dest'] = unarchive_success_result_instance.dest
                                item['created_date'] = unarchive_success_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                        elif table[0] == models.adhoc.UNARCHIVEFail.__tablename__:
                            unarchive_fail_result_instances = session.query(models.adhoc.UNARCHIVEFail).filter(models.adhoc.UNARCHIVEFail.asset_id.in_(id_list)).all()

                            for unarchive_fail_result_instance in unarchive_fail_result_instances:
                                item = {}
                                item['result'] = unarchive_fail_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = unarchive_fail_result_instance.id
                                item['asset_id'] = unarchive_fail_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['msg'] = unarchive_fail_result_instance.msg
                                item['created_date'] = unarchive_fail_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                        elif table[0] == models.adhoc.UNREACHABLE.__tablename__:
                            unreachable_result_instances = session.query(models.adhoc.UNREACHABLE).filter(models.adhoc.UNREACHABLE.asset_id.in_(id_list)).all()

                            for unreachable_result_instance in unreachable_result_instances:
                                item = {}
                                item['result'] = unreachable_result_instance.result
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = unreachable_result_instance.id
                                item['asset_id'] = unreachable_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['msg'] = unreachable_result_instance.msg
                                item['created_date'] = unreachable_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                        elif table[0] == models.adhoc.ExecTimeout.__tablename__:
                            exec_timeout_result_instances = session.query(models.adhoc.ExecTimeout).filter(models.adhoc.ExecTimeout.asset_id.in_(id_list)).all()

                            for exec_timeout_result_instance in exec_timeout_result_instances:
                                item = {}
                                item['task_name'] = task_name
                                item['module'] = module
                                item['args'] = args
                                item['id'] = exec_timeout_result_instance.id
                                item['asset_id'] = exec_timeout_result_instance.asset_id
                                item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                                item['module'] = exec_timeout_result_instance.module
                                item['args'] = exec_timeout_result_instance.args
                                item['msg'] = exec_timeout_result_instance.msg
                                item['created_date'] = exec_timeout_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                                result.append(item)

                    # print(json.dumps(result, ensure_ascii=False))

            except Exception as e:
                sql_logger.error('SQL Query Error: {}'.format(e))

            finally:
                session.close()

        # TODO: 获取IP的所有结果, 以时间排倒叙
        elif ip and not task_id and not ips:
            # 先查看IP对应的table
            tables = session.query(Asset.result_table).filter_by(ip=ip).group_by(Asset.result_table).all()
            # IP不唯一，所以有多个
            id_ip_list = session.query(Asset.id, Asset.ip).filter_by(ip=ip).all()
            # 获取ID列表
            id_list = [item[0] for item in id_ip_list]

            cursor = session.execute("select asset.id, asset.ip, copy_success.asset_id, copy_success.path, copy_success.changed"
                                     "from  copy_success "
                                     "left join asset "
                                     "on asset.id = copy_success.asset_id "
                                     "where asset.ip='{}' "
                                     "order by copy_success.created_date "
                                     "desc;".format(ip))

            result = cursor.fetchall()
            print(result)

            try:
                for table in tables:
                    if table[0] == models.adhoc.CopySuccess.__tablename__:
                        copy_success_result_instances = session.query(models.adhoc.CopySuccess).filter(models.adhoc.CopySuccess.asset_id.in_(id_list)).all()

                        for copy_success_result_instance in copy_success_result_instances:
                            item = {}

                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = copy_success_result_instance.id
                            item['asset_id'] = copy_success_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['path'] = copy_success_result_instance.path
                            item['changed'] = copy_success_result_instance.changed
                            item['uid'] = copy_success_result_instance.uid
                            item['gid'] = copy_success_result_instance.gid
                            item['owner'] = copy_success_result_instance.owner
                            item['group'] = copy_success_result_instance.group
                            item['mode'] = copy_success_result_instance.mode
                            item['state'] = copy_success_result_instance.state
                            item['size'] = copy_success_result_instance.size
                            item['dest'] = copy_success_result_instance.dest
                            item['created_date'] = copy_success_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")

                            result.append(item)

                    elif table[0] == models.adhoc.CopyFail.__tablename__:
                        copy_fail_result_instances = session.query(models.adhoc.CopyFail).filter(
                            models.adhoc.CopyFail.asset_id.in_(id_list)).all()

                        for copy_fail_result_instance in copy_fail_result_instances:
                            item = {}
                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = copy_fail_result_instance.id
                            item['asset_id'] = copy_fail_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['msg'] = copy_fail_result_instance.msg
                            item['exception'] = copy_fail_result_instance.exception
                            item['changed'] = copy_fail_result_instance.changed
                            item['created_date'] = copy_fail_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            result.append(item)

                    elif table[0] == models.adhoc.SHELLSuccess.__tablename__:
                        shell_success_result_instances = session.query(models.adhoc.SHELLSuccess).filter(
                            models.adhoc.SHELLSuccess.asset_id.in_(id_list)).all()

                        for shell_success_result_instance in shell_success_result_instances:
                            item = {}

                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = shell_success_result_instance.id
                            item['asset_id'] = shell_success_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['cmd'] = shell_success_result_instance.cmd
                            item['stdout'] = shell_success_result_instance.stdout
                            item['stderr'] = shell_success_result_instance.stderr
                            item['rc'] = shell_success_result_instance.rc
                            item['start_time'] = shell_success_result_instance.start_time
                            item['end_time'] = shell_success_result_instance.end_time
                            item['delta_time'] = shell_success_result_instance.delta_time
                            item['changed'] = shell_success_result_instance.changed
                            item['created_date'] = shell_success_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            result.append(item)

                    elif table[0] == models.adhoc.SHELLFail.__tablename__:
                        shell_fail_result_instances = session.query(models.adhoc.SHELLFail).filter(
                            models.adhoc.SHELLFail.asset_id.in_(id_list)).all()

                        for shell_fail_result_instance in shell_fail_result_instances:
                            item = {}

                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = shell_fail_result_instance.id
                            item['asset_id'] = shell_fail_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['msg'] = shell_fail_result_instance.msg
                            item['stdout'] = shell_fail_result_instance.stdout
                            item['stderr'] = shell_fail_result_instance.stderr
                            item['rc'] = shell_fail_result_instance.rc
                            item['start_time'] = shell_fail_result_instance.start_time
                            item['end_time'] = shell_fail_result_instance.end_time
                            item['delta_time'] = shell_fail_result_instance.delta_time
                            item['changed'] = shell_fail_result_instance.changed
                            item['created_date'] = shell_fail_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            result.append(item)

                    elif table[0] == models.adhoc.UNARCHIVESuccess.__tablename__:
                        unarchive_success_result_instances = session.query(models.adhoc.UNARCHIVESuccess).filter(
                            models.adhoc.UNARCHIVESuccess.asset_id.in_(id_list)).all()

                        for unarchive_success_result_instance in unarchive_success_result_instances:
                            item = {}
                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = unarchive_success_result_instance.id
                            item['asset_id'] = unarchive_success_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['dest'] = unarchive_success_result_instance.dest
                            item['src'] = unarchive_success_result_instance.src
                            item['changed'] = unarchive_success_result_instance.changed
                            item['uid'] = unarchive_success_result_instance.uid
                            item['gid'] = unarchive_success_result_instance.gid
                            item['owner'] = unarchive_success_result_instance.owner
                            item['group'] = unarchive_success_result_instance.group
                            item['state'] = unarchive_success_result_instance.state
                            item['size'] = unarchive_success_result_instance.size
                            item['created_date'] = unarchive_success_result_instance.created_date.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            result.append(item)

                    elif table[0] == models.adhoc.UNARCHIVEFail.__tablename__:
                        unarchive_fail_result_instances = session.query(models.adhoc.UNARCHIVEFail).filter(
                            models.adhoc.UNARCHIVEFail.asset_id.in_(id_list)).all()

                        for unarchive_fail_result_instance in unarchive_fail_result_instances:
                            item = {}
                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = unarchive_fail_result_instance.id
                            item['asset_id'] = unarchive_fail_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['msg'] = unarchive_fail_result_instance.msg
                            item['changed'] = unarchive_fail_result_instance.changed
                            item['created_date'] = unarchive_fail_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            result.append(item)

                    elif table[0] == models.adhoc.UNREACHABLE.__tablename__:
                        unreachable_result_instances = session.query(models.adhoc.UNREACHABLE).filter(
                            models.adhoc.UNREACHABLE.asset_id.in_(id_list)).all()

                        for unreachable_result_instance in unreachable_result_instances:
                            item = {}
                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = unreachable_result_instance.id
                            item['asset_id'] = unreachable_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['unreachable'] = unreachable_result_instance.unreachable
                            item['msg'] = unreachable_result_instance.msg
                            item['changed'] = unreachable_result_instance.changed
                            item['created_date'] = unreachable_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            result.append(item)

                    elif table[0] == models.adhoc.ExecTimeout.__tablename__:
                        exec_timeout_result_instances = session.query(models.adhoc.ExecTimeout).filter(
                            models.adhoc.ExecTimeout.asset_id.in_(id_list)).all()

                        for exec_timeout_result_instance in exec_timeout_result_instances:
                            item = {}
                            # item['task_name'] = task_name
                            # item['module'] = module
                            # item['args'] = args
                            item['id'] = exec_timeout_result_instance.id
                            item['asset_id'] = exec_timeout_result_instance.asset_id
                            item.update({'ip': id_ip[1] for id_ip in id_ip_list if item['asset_id'] in id_ip})
                            item['module'] = exec_timeout_result_instance.module
                            item['args'] = exec_timeout_result_instance.args
                            item['msg'] = exec_timeout_result_instance.msg
                            item['created_date'] = exec_timeout_result_instance.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            result.append(item)

            except Exception as e:
                sql_logger.error('SQL Query Error: {}'.format(e))

            finally:
                session.close()


        # TODO: 获取ips的所有结果,以时间拍倒叙
        elif ips and not ip and not task_id:
            print(ips)

        else:
            task_view_logger.error('Result Get Error: Task_id, IP, IPs must one of them has data')
            return JsonResponse(data={'code': 500, 'data': None, 'msg': '任务下发错误，请联系管理员'.format(task_id, ip, ips)})

        return JsonResponse(data={'code': 200, 'data': result, 'msg': '', 'length': len(result)})

# playbook下发和查询
class PlaybookView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # 消息剔除ip字段
    def __get_noip_data(self, data: dict):
        data.pop('ips')
        return data

    # 写入task和ip到数据库
    def __sync_task_ip_into_database(self, kwargs):
        ip_list = kwargs.get('ip_list')
        task_id = kwargs.get('task_id')
        task_name = kwargs.get('task_name')
        playbook_content = kwargs.get('playbook_content')
        playbook_name = kwargs.get('playbook_name')
        task_type = kwargs.get('task_type')

        session = MySQLSessionSingleton._get_mysql_session()

        try:

            session.add(PlaybookTask(id=task_id, name=task_name, playbook_content=playbook_content, playbook_name=playbook_name, task_type=task_type))
            session.commit()
            asset_list = []

            for ip in ip_list:
                asset_list.append(PlaybookAsset(ip=ip, task_id=task_id))

            session.bulk_save_objects(asset_list)
            session.commit()
        except Exception as e:
            task_view_logger.error('Sync task and ip to database Error: {}'.format(e))
            session.rollback()
            raise Exception('Sync task and ip to database Error')
        finally:
            session.close()

    # 下发任务指令集
    def post(self, request):
        json_data = request.body.decode('utf-8')
        dict_data = json.loads(json_data)

        ips = dict_data.get('ips').strip(',').replace(' ', '')
        task_id = dict_data.get('task_id')
        task_name = dict_data.get('task_name')
        ip_list = ips.split(',')
        playbook_content = dict_data.get('playbook_content')
        playbook_name = dict_data.get('playbook_name')
        task_type = dict_data.get('type')

        data = {'ips': ips,
                'task_id': task_id,
                'task_name': task_name,
                'playbook_content': playbook_content,
                'playbook_name': playbook_name,
                'task_type': task_type}

        create_form = PlaybookCreateForm(data)

        if create_form.is_valid():

            try:
                data.pop('ips')
                data['ip_list'] = ip_list
                self.__sync_task_ip_into_database(data)

            except Exception:
                return JsonResponse(data={'code': 500, 'data': None, 'msg': '任务和资产写入错误'})

            exec_number = ExecEngineSingleton._get_exec_number()
            ret = len(ip_list) / exec_number
            ret = math.ceil(ret)
            try:
                if ret == 1:
                    dict_data["ip"] = dict_data.pop("ips")
                    send_message(dict_data)
                else:
                    noip_data = self.__get_noip_data(dict_data)
                    for i in range(ret):
                        ceil = exec_number * i
                        tail = exec_number * (i + 1)
                        sub_ip_list = ip_list[ceil:tail]
                        sub_ip_str = ','.join(sub_ip_list)
                        noip_data['ip'] = sub_ip_str
                        send_message(noip_data)

            except Exception as e:
                task_view_logger.error('Send Message to Kafka Error: {}'.format(e))
                return JsonResponse(data={'code': 500, 'data': None, 'msg': 'Kafka指令集下发错误'})

            return JsonResponse(data={'code': 200, 'data': None, 'msg': '任务下发成功'})

        else:
            task_view_logger.error('Post data Error: {}'.format(json.dumps(create_form.errors, ensure_ascii=False)))
            return JsonResponse(data={'code': 500, 'data': dict_data, 'msg': create_form.errors})


    # 基于IP列表返回每个IP的执行结果
    def get(self, request):
        ips = request.GET.get('ips').strip(',').replace(' ', '')
        # task_id = request.GET.get('task_id')
        data = {'ips': ips}
        list_form = PlaybookListForm(data)

        if list_form.is_valid():
            session = MySQLSessionSingleton._get_mysql_session()
            ip_list = ips.split(',')
            # 基于最后一个IP，获取到playbook_content, 解析剧本的任务个数
            last_ip = ip_list[-1]
            try:
                last_playbook_asset_instance = session.query(models.playbook.PlaybookAsset).filter(models.playbook.PlaybookAsset.ip == last_ip).order_by(PlaybookAsset.id.desc()).first()
                task_view_logger.info('asset_ip={}, asset_task_id={}'.format(last_playbook_asset_instance.ip, last_playbook_asset_instance.task_id))
                playbook_content = session.query(models.playbook.PlaybookTask.playbook_content).filter(models.playbook.PlaybookTask.id == last_playbook_asset_instance.task_id).first()
                task_view_logger.info('playbook_content={}'.format(playbook_content))
                task_num = playbook_content[0].count('- name')
                task_view_logger.info('task_num={}'.format(task_num))
                playbook_asset_instances = session.query(models.playbook.PlaybookAsset).filter(models.playbook.PlaybookAsset.ip.in_(ip_list)).order_by(models.playbook.PlaybookAsset.id.desc())[0:len(ip_list)]

            except Exception as e:
                sql_logger.error('Get Playbook Result Error: {}'.format(e))
                return JsonResponse(data={'code': 500, 'data': data, 'msg': 'Get Playbook Result Error'})

            # 返回IP列表任务成功数
            result = []
            for playbook_asset_instance in playbook_asset_instances:
                item = {}

                item['ip'] = playbook_asset_instance.ip
                result_tables = playbook_asset_instance.result_table
                if not result_tables:
                    continue
                result_table_list = result_tables.split(',')
                success_table_num = sum(1 for _ in filter(lambda x: x.endswith('success'), result_table_list))
                success_rate = int(success_table_num / task_num * 100)
                item['success_rate'] = '{}%'.format(success_rate)
                item['result'] = 'success' if success_table_num >= task_num else 'fail'
                item['datetime'] = str(playbook_asset_instance.modify_date)
                result.append(item)
                
            return JsonResponse(data={'code': 200, 'data': result, 'msg': '', 'length': len(result)})

        else:
            task_view_logger.error('Post data Error: {}'.format(json.dumps(list_form.errors, ensure_ascii=False)))
            return JsonResponse(data={'code': 500, 'data': data, 'msg': list_form.errors})

# 拉取gitlab项目文件，且实时同步到其他执行引擎
class FileView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # 从gitlab拉取代码
    def post(self, request):
        json_data = request.body.decode('utf-8')
        dict_data = json.loads(json_data)
        project_name = dict_data.get('project_name')

        ret = os.system('cd {} && rm -fr {}'.format(FILES_DIR, project_name))
        task_view_logger.info('FILES_DIR={}, project_name={}, result={}, result_type={}'.format(FILES_DIR, project_name, ret, type(ret)))

        if ret == 0:
            ip, group = GitlabConfigSingleton._get_gitlab_config_info()
            cmd = 'cd {} && git clone git@{}:{}/{}.git'.format(FILES_DIR, ip, group, project_name)
            task_view_logger.info('cmd={}'.format(cmd))
            clone_result = os.system(cmd)

            if clone_result == 0:
                return JsonResponse(data={'code': 200, 'data': '', 'msg': '{}克隆成功'.format(project_name),})
            else:
                return JsonResponse(data={'code': 500, 'data': '', 'msg': '{} 克隆失败'.format(project_name)})

        else:
            task_view_logger.error('FILES_DIR={}, project_name={}, result={}'.format(FILES_DIR, project_name, ret))
            return JsonResponse(data={'code': 500, 'data': '', 'msg': '{} 无法删除'.format(project_name)})