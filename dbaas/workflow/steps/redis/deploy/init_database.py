# -*- coding: utf-8 -*-
import logging
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from util import check_ssh, get_credentials_for, exec_remote_command_host, \
    build_context_script
from physical.models import Instance
from physical.configurations import configuration_factory
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0016
from util import full_stack

LOG = logging.getLogger(__name__)


class InitDatabaseRedis(BaseStep):

    def __unicode__(self):
        return "Initializing database..."

    def do(self, workflow_dict):
        try:
            offering = workflow_dict['plan'].stronger_offering
            configuration = configuration_factory(
                workflow_dict['databaseinfra'], offering.memory_size_mb
            )

            graylog_credential = get_credentials_for(
                environment=workflow_dict['databaseinfra'].environment,
                credential_type=CredentialType.GRAYLOG
            )
            graylog_endpoint = graylog_credential.get_parameter_by_name(
                'endpoint_log'
            )

            plan = workflow_dict['plan']

            for index, host in enumerate(workflow_dict['hosts']):

                LOG.info("Getting vm credentials...")

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(host, wait=5, interval=10)

                if not host_ready:
                    LOG.warn("Host %s is not ready..." % host)
                    return False

                host.update_os_description()

                instances_redis = Instance.objects.filter(
                    hostname=host, instance_type=Instance.REDIS
                )
                instances_sentinel = Instance.objects.filter(
                    hostname=host, instance_type=Instance.REDIS_SENTINEL
                )

                if instances_redis:
                    host_nfsattr = HostAttr.objects.get(host=host)
                    nfsaas_path = host_nfsattr.nfsaas_path
                    only_sentinel = False
                    instance_redis_address = instances_redis[0].address
                    instance_redis_port = instances_redis[0].port
                else:
                    nfsaas_path = ""
                    only_sentinel = True
                    instance_redis_address = ''
                    instance_redis_port = ''

                if instances_sentinel:
                    instance_sentinel_address = instances_sentinel[0].address
                    instance_sentinel_port = instances_sentinel[0].port
                else:
                    instance_sentinel_address = ''
                    instance_sentinel_port = ''

                if index == 0:
                    master_host = instance_redis_address
                    master_port = instance_redis_port

                contextdict = {
                    'EXPORTPATH': nfsaas_path,
                    'DATABASENAME': workflow_dict['name'],
                    'DBPASSWORD': workflow_dict['databaseinfra'].password,
                    'HOSTADDRESS': instance_redis_address,
                    'PORT': instance_redis_port,
                    'ENGINE': 'redis',
                    'HOST': host.hostname.split('.')[0],
                    'DRIVER_NAME': workflow_dict['databaseinfra'].get_driver().topology_name(),
                    'SENTINELMASTER': master_host,
                    'SENTINELMASTERPORT': master_port,
                    'SENTINELADDRESS': instance_sentinel_address,
                    'SENTINELPORT': instance_sentinel_port,
                    'MASTERNAME': workflow_dict['databaseinfra'].name,
                    'ONLY_SENTINEL': only_sentinel,
                    'HAS_PERSISTENCE': workflow_dict['plan'].has_persistence,
                    'ENVIRONMENT': workflow_dict['databaseinfra'].environment,
                    'configuration': configuration,
                    'GRAYLOG_ENDPOINT': graylog_endpoint,
                }
                LOG.info(contextdict)

                scripts = (
                    plan.script.initialization_template,
                    plan.script.configuration_template,
                    plan.script.start_database_template,
                    plan.script.start_replication_template
                )

                for script in scripts:
                    LOG.info("Executing script on %s" % host)

                    script = build_context_script(contextdict, script)
                    output = {}
                    return_code = exec_remote_command_host(
                        host, script, output
                    )

                    if return_code != 0:
                        error_msg = "Error executing script. Stdout: {} - " \
                                    "stderr: {}".format(output['stdout'],
                                                        output['stderr'])
                        raise Exception(error_msg)

                if index > 0 and instances_redis:
                    client = instances_redis[
                        0].databaseinfra.get_driver().get_client(instances_redis[0])
                    client.slaveof(master_host, master_port)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0016)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            LOG.info("Remove all database files")

            for host in workflow_dict['hosts']:
                LOG.info("Removing database files on host %s" % host)
                exec_remote_command_host(
                    host, "/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh"
                )

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0016)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
