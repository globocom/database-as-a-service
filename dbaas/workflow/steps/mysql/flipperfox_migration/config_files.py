# -*- coding: utf-8 -*-
import logging
import os
import shutil
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from util import scp_get_file
from util import scp_put_file
from system.models import Configuration
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.util import test_bash_script_error
from workflow.steps.mysql.util import build_stop_database_script
from workflow.steps.mysql.util import build_server_id_conf_script

LOG = logging.getLogger(__name__)


class ConfigFiles(BaseStep):

    def __unicode__(self):
        return "Config files..."

    def do(self, workflow_dict):
        try:
            region_migration_dir = Configuration.get_by_name(
                'region_migration_dir')
            if not region_migration_dir:
                region_migration_dir = '/tmp'

            workflow_dict['region_migration_dir_infra_name'] = "{}/{}".format(
                region_migration_dir, workflow_dict['databaseinfra'].name)

            for index, source_instance in enumerate(workflow_dict['source_instances']):

                source_host = source_instance.hostname
                source_cs_host_attr = CS_HostAttr.objects.get(host=source_host)

                hostname = source_host.hostname.split('.')[0]
                localpath = "{}/{}".format(
                    workflow_dict['region_migration_dir_infra_name'], hostname)
                os.makedirs(localpath)

                LOG.info('Get source host files to {}'.format(localpath))

                if not scp_get_file(server=source_host.address,
                                    username=source_cs_host_attr.vm_user,
                                    password=source_cs_host_attr.vm_password,
                                    localpath="{}/my.cnf".format(localpath),
                                    remotepath="/etc/my.cnf"):
                    raise Exception("FTP Error")

                if not scp_get_file(server=source_host.address,
                                    username=source_cs_host_attr.vm_user,
                                    password=source_cs_host_attr.vm_password,
                                    localpath="{}/mysql_statsd.conf".format(
                                        localpath),
                                    remotepath="/etc/mysql_statsd/mysql_statsd.conf"):
                    raise Exception("FTP Error")

                if not scp_get_file(server=source_host.address,
                                    username=source_cs_host_attr.vm_user,
                                    password=source_cs_host_attr.vm_password,
                                    localpath="{}/td-agent.conf".format(
                                        localpath),
                                    remotepath="/etc/td-agent/td-agent.conf"):
                    raise Exception("FTP Error")

                target_host = source_host.future_host
                LOG.info(target_host)
                target_cs_host_attr = CS_HostAttr.objects.get(host=target_host)

                if not scp_put_file(server=target_host.address,
                                    username=target_cs_host_attr.vm_user,
                                    password=target_cs_host_attr.vm_password,
                                    localpath="{}/my.cnf".format(localpath),
                                    remotepath="/etc/my.cnf"):
                    raise Exception("FTP Error")

                if not scp_put_file(server=target_host.address,
                                    username=target_cs_host_attr.vm_user,
                                    password=target_cs_host_attr.vm_password,
                                    localpath="{}/mysql_statsd.conf".format(
                                        localpath),
                                    remotepath="/etc/mysql_statsd/mysql_statsd.conf"):
                    raise Exception("FTP Error")

                if not scp_put_file(server=target_host.address,
                                    username=target_cs_host_attr.vm_user,
                                    password=target_cs_host_attr.vm_password,
                                    localpath="{}/td-agent.conf".format(
                                        localpath),
                                    remotepath="/etc/td-agent/td-agent.conf"):
                    raise Exception("FTP Error")

                script = test_bash_script_error()
                script += build_server_id_conf_script()

                context_dict = {
                    'SERVERID': index + 3,
                }

                script = build_context_script(context_dict, script)

                output = {}
                LOG.info(script)
                return_code = exec_remote_command(server=target_host.address,
                                                  username=target_cs_host_attr.vm_user,
                                                  password=target_cs_host_attr.vm_password,
                                                  command=script,
                                                  output=output)
                LOG.info(output)
                if return_code != 0:
                    raise Exception(str(output))

            shutil.rmtree(workflow_dict['region_migration_dir_infra_name'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            script = build_stop_database_script()
            script = build_context_script({}, script)
            for target_instance in workflow_dict['target_instances']:
                target_host = target_instance.hostname
                target_cs_host_attr = CS_HostAttr.objects.get(host=target_host)
                output = {}
                exec_remote_command(server=target_host.address,
                                    username=target_cs_host_attr.vm_user,
                                    password=target_cs_host_attr.vm_password,
                                    command=script,
                                    output=output)
                LOG.info(output)

            try:
                if 'region_migration_dir_infra_name' in workflow_dict:
                    shutil.rmtree(
                        workflow_dict['region_migration_dir_infra_name'])
            except Exception:
                pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
