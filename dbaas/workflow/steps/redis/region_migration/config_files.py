# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import check_ssh
from util import exec_remote_command
from util import build_context_script
from util import get_credentials_for
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from dbaas_cloudstack.models import PlanAttr
from physical.models import Instance
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.util import test_bash_script_error
from workflow.steps.redis.util import build_permission_script
from workflow.steps.redis.util import build_clean_database_dir_script
from workflow.steps.redis.util import change_slave_priority_file

LOG = logging.getLogger(__name__)


class ConfigFiles(BaseStep):

    def __unicode__(self):
        return "Config files..."

    def do(self, workflow_dict):
        try:

            LOG.info("Getting cloudstack credentials...")

            statsd_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.STATSD)

            statsd_host, statsd_port = statsd_credentials.endpoint.split(':')
            databaseinfra = workflow_dict['databaseinfra']

            sentinel = databaseinfra.get_driver().get_sentinel_client()
            master = sentinel.discover_master(databaseinfra.name)
            master_host = master[0]
            master_port = master[1]

            for index, source_host in enumerate(workflow_dict['source_hosts']):

                target_host = source_host.future_host
                LOG.info(target_host)
                target_cs_host_attr = CS_HostAttr.objects.get(host=target_host)

                if index == 2:
                    LOG.info("Cheking host ssh...")
                    host_ready = check_ssh(server=target_host.address,
                                           username=target_cs_host_attr.vm_user,
                                           password=target_cs_host_attr.vm_password,
                                           wait=5, interval=10)

                    if not host_ready:
                        raise Exception(
                            str("Host %s is not ready..." % target_host))

                script = test_bash_script_error()
                script += build_permission_script()
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

                instances_redis = Instance.objects.filter(hostname=target_host,
                                                          instance_type=Instance.REDIS)
                instances_sentinel = Instance.objects.filter(hostname=target_host,
                                                             instance_type=Instance.REDIS_SENTINEL)

                if instances_redis:
                    only_sentinel = False
                    instance_redis_address = instances_redis[0].address
                    instance_redis_port = instances_redis[0].port
                else:
                    only_sentinel = True
                    instance_redis_address = ''
                    instance_redis_port = ''

                if instances_sentinel:
                    instance_sentinel_address = instances_sentinel[0].address
                    instance_sentinel_port = instances_sentinel[0].port
                else:
                    instance_sentinel_address = ''
                    instance_sentinel_port = ''

                contextdict = {
                    'DATABASENAME': workflow_dict['database'].name,
                    'DBPASSWORD': databaseinfra.password,
                    'HOSTADDRESS': instance_redis_address,
                    'PORT': instance_redis_port,
                    'ENGINE': 'redis',
                    'HOST': source_host.hostname.split('.')[0],
                    'STATSD_HOST': statsd_host,
                    'STATSD_PORT': statsd_port,
                    'IS_HA': databaseinfra.plan.is_ha,
                    'SENTINELMASTER': master_host,
                    'SENTINELMASTERPORT': master_port,
                    'SENTINELADDRESS': instance_sentinel_address,
                    'SENTINELPORT': instance_sentinel_port,
                    'MASTERNAME': databaseinfra.name,
                    'ONLY_SENTINEL': only_sentinel,
                }

                planattr = PlanAttr.objects.get(
                    plan=workflow_dict['source_plan'])
                script = build_context_script(
                    contextdict, planattr.configuration_script)

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

                if index < 2:
                    change_slave_priority_file(host=target_host,
                                               original_value=100,
                                               final_value=0)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            script = build_clean_database_dir_script()
            script = build_context_script({}, script)
            for source_host in workflow_dict['source_hosts']:
                target_host = source_host.future_host
                target_cs_host_attr = CS_HostAttr.objects.get(host=target_host)
                output = {}
                exec_remote_command(server=target_host.address,
                                    username=target_cs_host_attr.vm_user,
                                    password=target_cs_host_attr.vm_password,
                                    command=script,
                                    output=output)
                LOG.info(output)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
