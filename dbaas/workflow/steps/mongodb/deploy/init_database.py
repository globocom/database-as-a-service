# -*- coding: utf-8 -*-
import logging
import string
import random
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr
from physical.configurations import configuration_factory
from util import full_stack, check_ssh, get_credentials_for, \
    exec_remote_command_host, build_context_script
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0014

LOG = logging.getLogger(__name__)


class InitDatabaseMongoDB(BaseStep):

    def __unicode__(self):
        return "Initializing database..."

    def do(self, workflow_dict):
        try:
            cloud_stack = workflow_dict['plan'].cs_plan_attributes.first()
            offering = cloud_stack.get_stronger_offering()
            configuration = configuration_factory(
                workflow_dict['databaseinfra'], offering.memory_size_mb
            )

            mongodbkey = ''.join(
                random.choice(string.hexdigits) for i in range(50)
            )

            infra = workflow_dict['databaseinfra']
            if infra.plan.is_ha:
                infra.database_key = mongodbkey
                infra.save()

            workflow_dict['replicasetname'] = infra.get_driver().replica_set_name

            mongodb_password = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.MONGODB
            ).password

            disk_offering = workflow_dict['plan'].disk_offering

            graylog_credential = get_credentials_for(
                environment=workflow_dict['databaseinfra'].environment,
                credential_type=CredentialType.GRAYLOG
            )
            graylog_endpoint = graylog_credential.get_parameter_by_name(
                'endpoint_log'
            )
            plan = workflow_dict['plan']

            for index, instance in enumerate(workflow_dict['instances']):
                host = instance.hostname

                LOG.info("Getting vm credentials...")

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(host, wait=5, interval=10)

                if not host_ready:
                    LOG.warn("Host %s is not ready..." % host)
                    return False

                host.update_os_description()

                if instance.instance_type == instance.MONGODB_ARBITER:
                    contextdict = {
                        'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                        'DATABASENAME': workflow_dict['name'],
                        'ENGINE': 'mongodb',
                        'DRIVER_NAME': infra.get_driver().topology_name(),
                        'configuration': configuration,
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
                        'DRIVER_NAME': infra.get_driver().topology_name(),
                        'configuration': configuration,
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

                contextdict.update({
                    'ENVIRONMENT': workflow_dict['databaseinfra'].environment,
                    'DISK_SIZE_IN_GB': disk_offering.size_gb(),
                    'GRAYLOG_ENDPOINT': graylog_endpoint
                })

                scripts = (
                    plan.script.initialization_template,
                    plan.script.configuration_template,
                    plan.script.start_database_template
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

            if len(workflow_dict['hosts']) > 1:
                scripts_to_run = plan.script.start_replication_template

                contextdict.update({
                    'DBPASSWORD': mongodb_password,
                    'DATABASERULE': 'PRIMARY'
                })

                scripts_to_run = build_context_script(
                    contextdict, scripts_to_run
                )

                host = workflow_dict['hosts'][0]
                output = {}
                return_code = exec_remote_command_host(
                    host, scripts_to_run, output
                )

                if return_code != 0:
                    error_msg = "Error executing script. Stdout: {} - " \
                                "stderr: {}".format(output['stdout'],
                                                    output['stderr'])
                    raise Exception(error_msg)

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
                exec_remote_command_host(
                    host, "/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh"
                )

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
