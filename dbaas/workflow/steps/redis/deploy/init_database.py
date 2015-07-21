# -*- coding: utf-8 -*-
import logging
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from dbaas_cloudstack.models import PlanAttr
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import check_ssh
from util import exec_remote_command
from util import get_credentials_for
from util import build_context_script
from physical.models import Instance
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0016
from util import full_stack

LOG = logging.getLogger(__name__)


class InitDatabaseRedis(BaseStep):

    def __unicode__(self):
        return "Initializing database..."

    def do(self, workflow_dict):
        try:

            LOG.info("Getting cloudstack credentials...")

            statsd_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.STATSD)

            statsd_host, statsd_port = statsd_credentials.endpoint.split(':')

            for index, host in enumerate(workflow_dict['hosts']):

                LOG.info("Getting vm credentials...")
                host_csattr = CsHostAttr.objects.get(host=host)

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(
                    server=host.address, username=host_csattr.vm_user,
                    password=host_csattr.vm_password, wait=5, interval=10)

                if not host_ready:
                    LOG.warn("Host %s is not ready..." % host)
                    return False

                instances_redis = Instance.objects.filter(hostname=host,
                                                          instance_type=Instance.REDIS)
                instances_sentinel = Instance.objects.filter(hostname=host,
                                                             instance_type=Instance.REDIS_SENTINEL)

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
                    'STATSD_HOST': statsd_host,
                    'STATSD_PORT': statsd_port,
                    'IS_HA': workflow_dict['databaseinfra'].plan.is_ha,
                    'SENTINELMASTER': master_host,
                    'SENTINELMASTERPORT': master_port,
                    'SENTINELADDRESS': instance_sentinel_address,
                    'SENTINELPORT': instance_sentinel_port,
                    'MASTERNAME': workflow_dict['databaseinfra'].name,
                    'ONLY_SENTINEL': only_sentinel,
                }
                LOG.info(contextdict)

                planattr = PlanAttr.objects.get(plan=workflow_dict['plan'])
                scripts = (planattr.initialization_script,
                           planattr.configuration_script,
                           planattr.start_database_script,
                           planattr.start_replication_script)

                for script in scripts:
                    LOG.info("Executing script on %s" % host)

                    script = build_context_script(contextdict, script)
                    return_code = exec_remote_command(server=host.address,
                                                      username=host_csattr.vm_user,
                                                      password=host_csattr.vm_password,
                                                      command=script)

                    if return_code != 0:
                        return False

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
                host_csattr = CsHostAttr.objects.get(host=host)

                exec_remote_command(server=host.address,
                                    username=host_csattr.vm_user,
                                    password=host_csattr.vm_password,
                                    command="/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh")

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0016)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
