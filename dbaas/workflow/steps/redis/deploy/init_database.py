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
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0016
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

            for index, instance in enumerate(workflow_dict['instances']):
                host = instance.hostname

                LOG.info("Getting vm credentials...")
                host_csattr = CsHostAttr.objects.get(host=host)

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(
                    server=host.address, username=host_csattr.vm_user, password=host_csattr.vm_password, wait=5,
                    interval=10)

                if not host_ready:
                    LOG.warn("Host %s is not ready..." % host)
                    return False

                host_nfsattr = HostAttr.objects.get(host=host)

                planattr = PlanAttr.objects.get(plan=workflow_dict['plan'])

                if index == 0:
                    master_host = instance.address
                    master_port = instance.port

                contextdict = {
                    'EXPORTPATH': host_nfsattr.nfsaas_path,
                    'DATABASENAME': workflow_dict['name'],
                    'DBPASSWORD': workflow_dict['databaseinfra'].password,
                    'HOSTADDRESS':  instance.address,
                    'PORT': instance.port,
                    'ENGINE': 'redis',
                    'DATABASENAME': workflow_dict['name'],
                    'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                    'STATSD_HOST': statsd_host,
                    'STATSD_PORT': statsd_port,
                    'IS_HA': workflow_dict['databaseinfra'].plan.is_ha,
                    'SENTINELMASTER': master_host,
                    'SENTINELPORT': 26379,
                    'MASTERNAME': instance.databaseinfra.name,
                }
                LOG.info(contextdict)

                LOG.info("Updating userdata for %s" % host)
                planattr = PlanAttr.objects.get(plan=workflow_dict['plan'])
                script = build_context_script(contextdict, planattr.userdata)

                LOG.info("Executing script on %s" % host)
                LOG.info(script)
                output ={}
                return_code = exec_remote_command(server=host.address,
                                                  username=host_csattr.vm_user,
                                                  password=host_csattr.vm_password,
                                                  command=script,
                                                  output=output)

                LOG.info(output)
                if return_code != 0:
                    return False

                if index != 0:
                    client = instance.databaseinfra.get_driver().get_client(instance)
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
