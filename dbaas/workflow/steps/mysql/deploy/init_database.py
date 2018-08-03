# -*- coding: utf-8 -*-
import logging
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from itertools import permutations
from physical.configurations import configuration_factory
from util import check_ssh
from util import get_credentials_for, exec_remote_command_host, full_stack, \
    build_context_script
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class InitDatabase(BaseStep):

    def __unicode__(self):
        return "Initializing database..."

    def do(self, workflow_dict):
        try:
            cloud_stack = workflow_dict['plan'].stronger_offering
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

            for index, hosts in enumerate(permutations(workflow_dict['hosts'])):

                LOG.info("Getting vm credentials...")
                host = hosts[0]

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(host, wait=5, interval=10)

                if not host_ready:
                    LOG.warn("Host %s is not ready..." % host)
                    return False

                host_nfsattr = HostAttr.objects.get(host=host)

                contextdict = {
                    'EXPORTPATH': host_nfsattr.nfsaas_path,
                    'DATABASENAME': workflow_dict['name'],
                    'DBPASSWORD': get_credentials_for(
                        environment=workflow_dict['environment'],
                        credential_type=CredentialType.MYSQL
                    ).password,
                    'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                    'ENGINE': 'mysql',
                    'configuration': configuration,
                    'ENVIRONMENT': workflow_dict['databaseinfra'].environment,
                    'GRAYLOG_ENDPOINT': graylog_endpoint
                }

                if len(workflow_dict['hosts']) > 1:
                    LOG.info("Updating contexdict for %s" % host)

                    contextdict.update({
                        'SERVERID': index + 1,
                        'IPMASTER': hosts[1].address,
                        'IPWRITE': workflow_dict['databaseinfraattr'][0].ip,
                        'IPREAD': workflow_dict['databaseinfraattr'][1].ip,
                        'MASTERPAIRNAME': workflow_dict['databaseinfra'].name,
                        'HOST01': workflow_dict['hosts'][0],
                        'HOST02': workflow_dict['hosts'][1],
                        'INSTANCE01': workflow_dict['instances'][0],
                        'INSTANCE02': workflow_dict['instances'][1],
                        'SECOND_SCRIPT_FILE': '/opt/dbaas/scripts/dbaas_second_script.sh',
                    })

                scripts = (
                    plan.script.initialization_template,
                    plan.script.configuration_template,
                    plan.script.start_database_template
                )

                host.update_os_description()
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

            if len(workflow_dict['hosts']) > 1:

                for hosts in permutations(workflow_dict['hosts']):
                    script = plan.script.start_replication_template
                    host = hosts[0]
                    contextdict.update({'IPMASTER': hosts[1].address})
                    script = build_context_script(contextdict, script)

                    LOG.info("Executing script on %s" % host)
                    output = {}
                    return_code = exec_remote_command_host(
                        host, script, output
                    )
                    if return_code != 0:
                        error_msg = "Error executing script. Stdout: {} - " \
                                    "stderr: {}".format(output['stdout'],
                                                        output['stderr'])
                        raise Exception(error_msg)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
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

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
