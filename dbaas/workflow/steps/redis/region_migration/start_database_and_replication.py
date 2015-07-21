# -*- coding: utf-8 -*-
import logging
from time import sleep
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.util import test_bash_script_error
from workflow.steps.redis.util import build_start_stop_scripts
from workflow.steps.redis.util import build_start_database_script
from workflow.steps.redis.util import build_stop_database_script
from workflow.steps.redis.util import build_start_sentinel_script
from workflow.steps.redis.util import build_stop_sentinel_script
from workflow.steps.redis.util import build_start_http_script
from workflow.steps.redis.util import reset_sentinel


LOG = logging.getLogger(__name__)


class StartDatabaseReplication(BaseStep):

    def __unicode__(self):
        return "Starting database and replication..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()
            sentinel = driver.get_sentinel_client()
            master = sentinel.discover_master(databaseinfra.name)
            master_host = master[0]
            master_port = master[1]

            for index, source_host in enumerate(workflow_dict['source_hosts']):

                target_host = source_host.future_host
                target_cs_host_attr = CS_HostAttr.objects.get(host=target_host)

                script = test_bash_script_error()
                script += build_start_stop_scripts()
                if index < 2:
                    script += build_start_database_script()
                script += build_start_sentinel_script()
                script += build_start_http_script()
                script = build_context_script({}, script)

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

            for target_instance in workflow_dict['target_instances']:
                if target_instance.instance_type == target_instance.REDIS:
                    LOG.info(
                        'Changing master of host: {}'.format(target_instance.address))
                    client = driver.get_client(target_instance)
                    client.slaveof(master_host, master_port)
                    LOG.info(
                        'New master: {}:{}'.format(master_host, master_port))

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            databaseinfra = workflow_dict['databaseinfra']

            for index, source_host in enumerate(workflow_dict['source_hosts']):
                target_host = source_host.future_host
                target_cs_host_attr = CS_HostAttr.objects.get(host=target_host)

                script = test_bash_script_error()
                script += build_start_stop_scripts()
                script += build_stop_sentinel_script()
                if index < 2:
                    script += build_stop_database_script()
                script = build_context_script({}, script)
                output = {}

                exec_remote_command(server=target_host.address,
                                    username=target_cs_host_attr.vm_user,
                                    password=target_cs_host_attr.vm_password,
                                    command=script,
                                    output=output)
                LOG.info(output)

            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type == source_instance.REDIS_SENTINEL:
                    reset_sentinel(host=source_instance.hostname,
                                   sentinel_host=source_instance.address,
                                   sentinel_port=source_instance.port,
                                   service_name=databaseinfra.name)
                    sleep(30)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
