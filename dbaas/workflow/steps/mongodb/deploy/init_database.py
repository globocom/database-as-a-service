# -*- coding: utf-8 -*-
import logging
import string
import random
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from dbaas_cloudstack.models import PlanAttr
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import full_stack
from util import check_ssh
from util import get_credentials_for
from util import exec_remote_command
from util import build_context_script
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0014

LOG = logging.getLogger(__name__)


class InitDatabaseMongoDB(BaseStep):

    def __unicode__(self):
        return "Initializing database..."

    def do(self, workflow_dict):
        try:
            mongodbkey = ''.join(random.choice(string.hexdigits)
                                 for i in range(50))

            workflow_dict['replicasetname'] = 'RepicaSet_' + \
                workflow_dict['databaseinfra'].name

            statsd_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.STATSD)

            statsd_host, statsd_port = statsd_credentials.endpoint.split(':')
            mongodb_password = get_credentials_for(environment=workflow_dict['environment'],
                                                   credential_type=CredentialType.MONGODB).password

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

                if instance.is_arbiter:
                    contextdict = {
                        'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                        'DATABASENAME': workflow_dict['name'],
                        'ENGINE': 'mongodb',
                        'STATSD_HOST': statsd_host,
                        'STATSD_PORT': statsd_port,
                        'IS_HA': workflow_dict['databaseinfra'].plan.is_ha
                    }
                    databaserule = 'ARBITER'
                else:
                    host_nfsattr = HostAttr.objects.get(host=host)
                    contextdict = {
                        'EXPORTPATH': host_nfsattr.nfsaas_path,
                        'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                        'DATABASENAME': workflow_dict['name'],
                        'ENGINE': 'mongodb',
                        'DBPASSWORD': mongodb_password,
                        'STATSD_HOST': statsd_host,
                        'STATSD_PORT': statsd_port,
                        'IS_HA': workflow_dict['databaseinfra'].plan.is_ha
                    }

                    if index == 0:
                        databaserule = 'PRIMARY'
                    else:
                        databaserule = 'SECONDARY'

                if len(workflow_dict['hosts']) > 1:
                    LOG.info("Updating contexdict for %s" % host)

                    contextdict.update({
                        'REPLICASETNAME': workflow_dict['replicasetname'],
                        'HOST01': workflow_dict['hosts'][0],
                        'HOST02': workflow_dict['hosts'][1],
                        'HOST03': workflow_dict['hosts'][2],
                        'MONGODBKEY': mongodbkey,
                        'DATABASERULE': databaserule,
                        'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                    })
                else:
                    contextdict.update({'DATABASERULE': databaserule})

                planattr = PlanAttr.objects.get(plan=workflow_dict['plan'])

                scripts = (planattr.initialization_script,
                           planattr.configuration_script,
                           planattr.start_database_script)

                for script in scripts:
                    LOG.info("Executing script on %s" % host)

                    script = build_context_script(contextdict, script)
                    return_code = exec_remote_command(server=host.address,
                                                      username=host_csattr.vm_user,
                                                      password=host_csattr.vm_password,
                                                      command=script)

                    if return_code != 0:
                        return False

            if len(workflow_dict['hosts']) > 1:
                scripts_to_run = planattr.start_replication_script

                contextdict.update({'DBPASSWORD': mongodb_password,
                                    'DATABASERULE': 'PRIMARY'})

                scripts_to_run = build_context_script(contextdict,
                                                      scripts_to_run)

                host = workflow_dict['hosts'][0]
                host_csattr = CsHostAttr.objects.get(host=host)

                return_code = exec_remote_command(server=host.address,
                                                  username=host_csattr.vm_user,
                                                  password=host_csattr.vm_password,
                                                  command=scripts_to_run)

                if return_code != 0:
                    return False

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
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

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
